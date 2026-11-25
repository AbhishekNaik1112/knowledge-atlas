"""GitHub webhook signature verification + repo sync.

Security: GitHub signs each delivery with HMAC-SHA256 over the raw body in `X-Hub-Signature-256`.
Verify against the shared secret with a constant-time compare BEFORE trusting any payload field.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import get_engine
from app.embeddings import Embedder
from app.ingest import IngestService
from app.repository import SqlConceptRepository, SqlEdgeRepository, SqlSyncEventRepository

logger = logging.getLogger(__name__)


def verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


class RepoSyncer:
    """Clone the pushed repo (shallow) and ingest it. Runs in a background task, own DB session."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        sync_subdir: str | None = None,
        sync_branch: str | None = None,
        github_token: str | None = None,
        namespace_by_bundle: bool = False,
        repos_config: dict[str, dict[str, str]] | None = None,
        cloud_mode: bool = False,
    ) -> None:
        self.embedder = embedder
        self.sync_subdir = sync_subdir
        self.sync_branch = sync_branch
        self.github_token = github_token
        self.namespace_by_bundle = namespace_by_bundle
        self.repos_config = repos_config or {}
        self.cloud_mode = cloud_mode

    def _auth_clone_url(self, clone_url: str) -> str:
        if self.github_token and clone_url.startswith("https://"):
            return clone_url.replace("https://", f"https://x-access-token:{self.github_token}@", 1)
        return clone_url

    def sync(self, payload: dict) -> None:
        repo = payload.get("repository", {})
        clone_url = repo.get("clone_url")
        if not clone_url:
            return
        if self.cloud_mode and not clone_url.startswith("https://github.com/"):
            logger.warning("Blocked non-GitHub clone URL in cloud mode: %s", clone_url)
            return
        name = repo.get("name", "default")
        repo_cfg = self.repos_config.get(name, {})
        ref = payload.get("ref")
        target_branch = repo_cfg.get("branch") or self.sync_branch or repo.get("default_branch")
        if ref and target_branch and ref != f"refs/heads/{target_branch}":
            return

        subdir = repo_cfg.get("subdir") or self.sync_subdir
        ns_val = repo_cfg.get("namespace")
        namespace_ids = (
            ns_val.lower() in ("1", "true", "yes")
            if isinstance(ns_val, str)
            else self.namespace_by_bundle
        )

        head_commit = payload.get("head_commit") or {}
        commit_sha = payload.get("after")
        commit_message = head_commit.get("message")
        pusher = (payload.get("pusher") or {}).get("name")

        with tempfile.TemporaryDirectory() as tmp:
            try:
                cmd = ["git", "clone", "--depth", "1"]
                if target_branch:
                    cmd.extend(["--branch", target_branch])
                cmd.extend([self._auth_clone_url(clone_url), tmp])
                subprocess.run(cmd, check=True, capture_output=True)

                target_dir = Path(tmp) / subdir if subdir else Path(tmp)
                with Session(get_engine()) as session:
                    service = IngestService(
                        SqlConceptRepository(session),
                        SqlEdgeRepository(session),
                        session,
                        embedder=self.embedder,
                    )
                    sync_repo = SqlSyncEventRepository(session)
                    sync_event = None

                    def _mark_in_progress(embeddable_count: int) -> None:
                        nonlocal sync_event
                        if self.embedder is not None and embeddable_count > 0:
                            sync_event = sync_repo.record(
                                bundle=name,
                                source="webhook",
                                commit_sha=commit_sha,
                                commit_message=commit_message,
                                pusher=pusher,
                                ref=ref,
                                embed_status="in_progress",
                                embed_detail=f"Generating semantic search embeddings for {embeddable_count} document(s)...",
                            )
                            session.commit()

                    res = service.ingest_dir(
                        str(target_dir),
                        bundle=name,
                        prune=True,
                        namespace_ids=namespace_ids,
                        on_before_embed=_mark_in_progress,
                    )
                    final_status = "ok" if not res.errors else "partial"
                    if sync_event is None:
                        sync_repo.record(
                            bundle=name,
                            source="webhook",
                            commit_sha=commit_sha,
                            commit_message=commit_message,
                            pusher=pusher,
                            ref=ref,
                            created_count=res.created,
                            updated_count=res.updated,
                            deleted_count=res.deleted,
                            error_count=len(res.errors),
                            status=final_status,
                            embedded_count=res.embedded_count,
                            embed_status=res.embed_status,
                            embed_detail=res.embed_detail,
                        )
                    else:
                        sync_event.created_count = res.created
                        sync_event.updated_count = res.updated
                        sync_event.deleted_count = res.deleted
                        sync_event.error_count = len(res.errors)
                        sync_event.status = final_status
                        sync_event.embedded_count = res.embedded_count
                        sync_event.embed_status = res.embed_status
                        sync_event.embed_detail = res.embed_detail
                    session.commit()
            except Exception as exc:
                with Session(get_engine()) as session:
                    SqlSyncEventRepository(session).record(
                        bundle=name,
                        source="webhook",
                        commit_sha=commit_sha,
                        commit_message=f"{commit_message or ''} ({type(exc).__name__}: {exc})".strip(),
                        pusher=pusher,
                        ref=ref,
                        error_count=1,
                        status="error",
                    )
                    session.commit()
                raise

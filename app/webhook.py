"""GitHub webhook signature verification + repo sync.

Security: GitHub signs each delivery with HMAC-SHA256 over the raw body in `X-Hub-Signature-256`.
Verify against the shared secret with a constant-time compare BEFORE trusting any payload field.
"""

from __future__ import annotations

import hashlib
import hmac
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import make_engine
from app.embeddings import Embedder
from app.ingest import IngestService
from app.repository import SqlConceptRepository, SqlEdgeRepository, SqlSyncEventRepository


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
    ) -> None:
        self.embedder = embedder
        self.sync_subdir = sync_subdir
        self.sync_branch = sync_branch
        self.github_token = github_token

    def _auth_clone_url(self, clone_url: str) -> str:
        if self.github_token and clone_url.startswith("https://"):
            return clone_url.replace("https://", f"https://x-access-token:{self.github_token}@", 1)
        return clone_url

    def sync(self, payload: dict) -> None:
        repo = payload.get("repository", {})
        clone_url = repo.get("clone_url")
        if not clone_url:
            return
        ref = payload.get("ref")
        target_branch = self.sync_branch or repo.get("default_branch")
        if ref and target_branch and ref != f"refs/heads/{target_branch}":
            return

        name = repo.get("name", "default")
        head_commit = payload.get("head_commit") or {}
        commit_sha = payload.get("after")
        commit_message = head_commit.get("message")
        pusher = (payload.get("pusher") or {}).get("name")

        with tempfile.TemporaryDirectory() as tmp:
            cmd = ["git", "clone", "--depth", "1"]
            if target_branch:
                cmd.extend(["--branch", target_branch])
            cmd.extend([self._auth_clone_url(clone_url), tmp])
            subprocess.run(cmd, check=True, capture_output=True)

            target_dir = Path(tmp) / self.sync_subdir if self.sync_subdir else Path(tmp)
            with Session(make_engine()) as session:
                service = IngestService(
                    SqlConceptRepository(session),
                    SqlEdgeRepository(session),
                    session,
                    embedder=self.embedder,
                )
                res = service.ingest_dir(str(target_dir), bundle=name, prune=True)
                SqlSyncEventRepository(session).record(
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
                    status="ok" if not res.errors else "partial",
                )
                session.commit()

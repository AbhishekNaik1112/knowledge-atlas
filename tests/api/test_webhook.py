"""M13 — GitHub webhook: HMAC-SHA256 verification + background re-ingest."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_session
from app.dependencies import get_repo_syncer
from app.main import create_app
from app.webhook import verify_signature

SECRET = "whsecret"


def _sig(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


class _SpySyncer:
    def __init__(self):
        self.calls: list[dict] = []

    def sync(self, payload: dict) -> None:
        self.calls.append(payload)


@pytest.fixture
def webhook_client(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(github_webhook_secret=SECRET)
    spy = _SpySyncer()
    app.dependency_overrides[get_repo_syncer] = lambda: spy
    with TestClient(app) as c:
        yield c, spy
    app.dependency_overrides.clear()


def test_verify_signature_valid():
    body = b'{"a":1}'
    assert verify_signature(SECRET, body, _sig(body))


def test_verify_signature_invalid():
    assert not verify_signature(SECRET, b"{}", "sha256=deadbeef")


def test_verify_signature_missing():
    assert not verify_signature(SECRET, b"{}", None)


def test_webhook_valid_signature_accepts_and_syncs(webhook_client):
    client, spy = webhook_client
    body = json.dumps({"repository": {"clone_url": "https://x/y.git", "name": "y"}}).encode()
    r = client.post("/webhooks/github", content=body, headers={"X-Hub-Signature-256": _sig(body)})
    assert r.status_code == 202
    assert len(spy.calls) == 1
    assert spy.calls[0]["repository"]["name"] == "y"


def test_webhook_bad_signature_401(webhook_client):
    client, spy = webhook_client
    r = client.post(
        "/webhooks/github", content=b"{}", headers={"X-Hub-Signature-256": "sha256=deadbeef"}
    )
    assert r.status_code == 401 and spy.calls == []


def test_webhook_missing_signature_401(webhook_client):
    client, spy = webhook_client
    r = client.post("/webhooks/github", content=b"{}")
    assert r.status_code == 401 and spy.calls == []


def test_webhook_bad_json_400(webhook_client):
    client, spy = webhook_client
    body = b"{not-json"
    r = client.post("/webhooks/github", content=body, headers={"X-Hub-Signature-256": _sig(body)})
    assert r.status_code == 400 and spy.calls == []


def test_repo_syncer_clones_and_ingests_real_git_repo(db_session, tmp_path, monkeypatch):
    import subprocess
    from app.db import Concept
    from app.webhook import RepoSyncer
    from tests.api.test_semantic import FakeEmbedder

    work = tmp_path / "work"
    bare = tmp_path / "remote.git"
    work.mkdir()
    subprocess.run(["git", "init", str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "Test"], check=True)
    (work / "note.md").write_text("---\ntype: Doc\ntitle: Fast Car\n---\nautomobile", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(["git", "clone", "--bare", str(work), str(bare)], check=True, capture_output=True)

    monkeypatch.setattr("app.webhook.make_engine", lambda: db_session.get_bind())
    syncer = RepoSyncer(embedder=FakeEmbedder())
    syncer.sync({"repository": {"clone_url": str(bare), "name": "git-bundle"}})

    obj = db_session.get(Concept, "note")
    assert obj is not None
    assert obj.bundle == "git-bundle"
    assert obj.embedding is not None
    db_session.delete(obj)
    db_session.commit()


def test_repo_syncer_prunes_deleted_and_records_sync_event(db_session, tmp_path, monkeypatch, client):
    import subprocess
    from app.db import Concept, SyncEvent
    from app.webhook import RepoSyncer

    work = tmp_path / "work"
    bare = tmp_path / "remote.git"
    work.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "Test"], check=True)
    (work / "README.md").write_text("# Non-OKF README", encoding="utf-8")
    (work / "docs").mkdir()
    (work / "docs" / "a.md").write_text("---\ntype: Doc\ntitle: A\n---\na", encoding="utf-8")
    (work / "docs" / "b.md").write_text("---\ntype: Doc\ntitle: B\n---\nb", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "add docs"], check=True, capture_output=True)
    subprocess.run(["git", "clone", "--bare", str(work), str(bare)], check=True, capture_output=True)

    monkeypatch.setattr("app.webhook.make_engine", lambda: db_session.get_bind())
    syncer = RepoSyncer(sync_subdir="docs")

    # Non-default branch is ignored
    syncer.sync({
        "ref": "refs/heads/feature",
        "repository": {"clone_url": str(bare), "name": "team-docs", "default_branch": "main"},
    })
    assert db_session.get(Concept, "a") is None

    # Default branch syncs docs/ (ignoring root README.md) and records SyncEvent
    syncer.sync({
        "ref": "refs/heads/main",
        "after": "abc1234567890",
        "pusher": {"name": "alice"},
        "head_commit": {"message": "add docs"},
        "repository": {"clone_url": str(bare), "name": "team-docs", "default_branch": "main"},
    })
    assert db_session.get(Concept, "a") is not None
    assert db_session.get(Concept, "b") is not None

    # Delete b.md and re-sync -> b is pruned
    (work / "docs" / "b.md").unlink()
    subprocess.run(["git", "-C", str(work), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "remove b"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "push", str(bare), "main"], check=True, capture_output=True)

    syncer.sync({
        "ref": "refs/heads/main",
        "after": "def9876543210",
        "pusher": {"name": "bob"},
        "head_commit": {"message": "remove b"},
        "repository": {"clone_url": str(bare), "name": "team-docs", "default_branch": "main"},
    })
    db_session.expire_all()
    assert db_session.get(Concept, "a") is not None
    assert db_session.get(Concept, "b") is None

    syncs = client.get("/syncs").json()
    assert len(syncs) >= 2
    assert syncs[0]["commit_sha"] == "def9876543210"
    assert syncs[0]["deleted_count"] == 1
    assert syncs[0]["pusher"] == "bob"

    db_session.query(SyncEvent).delete()
    if (obj := db_session.get(Concept, "a")) is not None:
        db_session.delete(obj)
    db_session.commit()


def test_repo_syncer_records_embed_status_ok_skipped_and_error(db_session, tmp_path, monkeypatch, client):
    import subprocess
    from app.db import Concept, SyncEvent
    from app.webhook import RepoSyncer
    from tests.api.test_semantic import FakeEmbedder

    class _FailingEmbedder:
        def encode(self, texts: list[str]) -> list[list[float]]:
            raise RuntimeError("429 rate limit")

    work = tmp_path / "work"
    bare = tmp_path / "remote.git"
    work.mkdir()
    subprocess.run(["git", "init", str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "Test"], check=True)
    (work / "note.md").write_text("---\ntype: Doc\ntitle: Note\n---\nbody", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(["git", "clone", "--bare", str(work), str(bare)], check=True, capture_output=True)

    monkeypatch.setattr("app.webhook.make_engine", lambda: db_session.get_bind())
    payload = {"repository": {"clone_url": str(bare), "name": "embed-test"}}

    RepoSyncer(embedder=FakeEmbedder()).sync(payload)
    RepoSyncer(embedder=None).sync(payload)
    RepoSyncer(embedder=_FailingEmbedder()).sync(payload)

    db_session.expire_all()
    assert db_session.get(Concept, "note") is not None

    syncs = client.get("/syncs").json()
    assert syncs[0]["status"] == "ok"
    assert syncs[0]["embed_status"] == "error"
    assert syncs[0]["embedded_count"] == 0
    assert syncs[1]["embed_status"] == "skipped"
    assert syncs[1]["embedded_count"] == 0
    assert syncs[2]["embed_status"] == "ok"
    assert syncs[2]["embedded_count"] == 1

    db_session.query(SyncEvent).delete()
    if (obj := db_session.get(Concept, "note")) is not None:
        db_session.delete(obj)
    db_session.commit()


def test_repo_syncer_sets_in_progress_before_embedding(db_session, tmp_path, monkeypatch):
    import subprocess
    from sqlalchemy.orm import Session
    from app.db import Concept, SyncEvent
    from app.webhook import RepoSyncer

    seen_statuses: list[str] = []

    class _SpyEmbedder:
        def encode(self, texts: list[str]) -> list[list[float]]:
            with Session(db_session.get_bind()) as check_sess:
                ev = check_sess.query(SyncEvent).order_by(SyncEvent.id.desc()).first()
                if ev is not None:
                    seen_statuses.append(ev.embed_status)
            return [[0.0] * 384 for _ in texts]

    work = tmp_path / "work"
    bare = tmp_path / "remote.git"
    work.mkdir()
    subprocess.run(["git", "init", str(work)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "Test"], check=True)
    (work / "note.md").write_text("---\ntype: Doc\ntitle: Note\n---\nbody", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(["git", "clone", "--bare", str(work), str(bare)], check=True, capture_output=True)

    monkeypatch.setattr("app.webhook.make_engine", lambda: db_session.get_bind())
    RepoSyncer(embedder=_SpyEmbedder()).sync(
        {"repository": {"clone_url": str(bare), "name": "progress-test"}}
    )

    assert seen_statuses == ["in_progress"]
    db_session.expire_all()
    ev = db_session.query(SyncEvent).order_by(SyncEvent.id.desc()).first()
    assert ev is not None and ev.embed_status == "ok" and ev.embedded_count == 1

    db_session.query(SyncEvent).delete()
    if (obj := db_session.get(Concept, "note")) is not None:
        db_session.delete(obj)
    db_session.commit()

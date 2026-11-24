"""M10 — ingest end-to-end against a trimmed REAL crypto_bitcoin OKF bundle."""

import io
import zipfile
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "bundles" / "crypto_bitcoin"


def test_ingest_dir_path(client):
    r = client.post("/ingest", params={"path": str(FIXTURE)})
    assert r.status_code == 200
    body = r.json()
    assert body["bundle"] == "crypto_bitcoin"
    assert body["created"] == 3  # dataset + 2 tables
    assert body["skipped"] == 3  # 3 index.md files
    assert body["errors"] == []


def test_ingest_skips_index_and_log(client):
    client.post("/ingest", params={"path": str(FIXTURE)})
    assert client.get("/concepts/index").status_code == 404
    assert client.get("/concepts/datasets/index").status_code == 404
    assert client.get("/concepts").json()["total"] == 3


def test_ingest_populates_edges(client):
    client.post("/ingest", params={"path": str(FIXTURE)})
    links = client.get("/concepts/datasets/crypto_bitcoin/links").json()
    resolved = {ln["target_id"]: ln["resolved"] for ln in links["outgoing"]}
    assert resolved["tables/blocks"] is True
    assert resolved["tables/transactions"] is True
    # inputs/outputs are linked but not in the trimmed fixture -> dangling
    assert resolved["tables/inputs"] is False
    assert resolved["tables/outputs"] is False


def test_ingest_is_idempotent_on_reingest(client):
    client.post("/ingest", params={"path": str(FIXTURE)})
    second = client.post("/ingest", params={"path": str(FIXTURE)}).json()
    assert second["created"] == 0 and second["updated"] == 3
    assert client.get("/concepts").json()["total"] == 3


def test_ingest_zip(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for p in FIXTURE.rglob("*.md"):
            zf.write(p, p.relative_to(FIXTURE).as_posix())
    r = client.post(
        "/ingest",
        params={"bundle": "crypto_bitcoin"},
        files={"file": ("bundle.zip", buf.getvalue(), "application/zip")},
    )
    assert r.status_code == 200 and r.json()["created"] == 3


def test_ingest_type_errors_nonfatal(client, tmp_path):
    (tmp_path / "good.md").write_text("---\ntype: Doc\n---\nok", encoding="utf-8")
    (tmp_path / "bad.md").write_text("---\ntitle: no type\n---\nnope", encoding="utf-8")
    body = client.post("/ingest", params={"path": str(tmp_path)}).json()
    assert body["created"] == 1
    assert [e["path"] for e in body["errors"]] == ["bad.md"]


def test_ingest_corrupt_zip_400(client):
    r = client.post("/ingest", files={"file": ("bad.zip", b"not-a-zip", "application/zip")})
    assert r.status_code == 400


def test_ingest_non_utf8_zip_400(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("bad.md", b"\xff\xfe\x00\x00invalid")
    r = client.post("/ingest", files={"file": ("bad_enc.zip", buf.getvalue(), "application/zip")})
    assert r.status_code == 400


def test_ingest_bad_yaml_nonfatal(client, tmp_path):
    (tmp_path / "good.md").write_text("---\ntype: Doc\n---\nok", encoding="utf-8")
    (tmp_path / "broken.md").write_text("---\ntype: [unclosed\n---\nbad", encoding="utf-8")
    r = client.post("/ingest", params={"path": str(tmp_path)})
    assert r.status_code == 200
    body = r.json()
    assert body["created"] == 1
    assert [e["path"] for e in body["errors"]] == ["broken.md"]


def test_ingest_prune_deletes_removed_concepts(client, tmp_path):
    (tmp_path / "keep.md").write_text("---\ntype: Doc\n---\nkeep", encoding="utf-8")
    (tmp_path / "drop.md").write_text("---\ntype: Doc\n---\ndrop", encoding="utf-8")
    r1 = client.post("/ingest", params={"path": str(tmp_path), "bundle": "b1", "prune": "true"})
    assert r1.status_code == 200 and r1.json()["created"] == 2

    (tmp_path / "drop.md").unlink()
    r2 = client.post("/ingest", params={"path": str(tmp_path), "bundle": "b1", "prune": "true"})
    assert r2.status_code == 200
    assert r2.json()["deleted"] == 1
    assert client.get("/concepts/drop").status_code == 404
    assert client.get("/concepts/keep").status_code == 200


def test_ingest_namespace_ids_prevents_multi_repo_collision(client, tmp_path):
    repo_a = tmp_path / "repo_a"
    repo_b = tmp_path / "repo_b"
    repo_a.mkdir()
    repo_b.mkdir()
    (repo_a / "auth.md").write_text("---\ntype: Doc\ntitle: Repo A Auth\n---\nsee [b](@repo_b/auth.md)", encoding="utf-8")
    (repo_b / "auth.md").write_text("---\ntype: Doc\ntitle: Repo B Auth\n---\nhello", encoding="utf-8")

    ra = client.post("/ingest", params={"path": str(repo_a), "bundle": "repo_a", "namespace_ids": "true"})
    rb = client.post("/ingest", params={"path": str(repo_b), "bundle": "repo_b", "namespace_ids": "true"})
    assert ra.status_code == 200 and rb.status_code == 200

    a = client.get("/concepts/repo_a/auth").json()
    b = client.get("/concepts/repo_b/auth").json()
    assert a["title"] == "Repo A Auth" and b["title"] == "Repo B Auth"
    links = client.get("/concepts/repo_a/auth/links").json()
    assert links["outgoing"][0]["target_id"] == "repo_b/auth"
    assert links["outgoing"][0]["resolved"] is True


class _FailingEmbedder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("429 rate limit exceeded")


def _make_zip(src: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for p in src.rglob("*.md"):
            zf.write(p, p.relative_to(src).as_posix())
    return buf.getvalue()


def _make_client(db_session, *, embeddings_enabled: bool, embedder=None):
    from fastapi.testclient import TestClient
    from app.config import Settings, get_settings
    from app.db import get_session
    from app.embeddings import get_embedder
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        embeddings_enabled=embeddings_enabled
    )
    if embedder is not None:
        app.dependency_overrides[get_embedder] = embedder
    return app


def test_ingest_reports_embed_status_skipped_when_disabled(db_session):
    from fastapi.testclient import TestClient

    app = _make_client(db_session, embeddings_enabled=False)
    with TestClient(app) as c:
        body = c.post("/ingest", params={"path": str(FIXTURE)}).json()
        assert body["embed_status"] == "skipped"
        assert body["embedded_count"] == 0
    app.dependency_overrides.clear()


def test_ingest_reports_embed_status_ok_for_dir_and_zip(db_session):
    from fastapi.testclient import TestClient
    from tests.api.test_semantic import FakeEmbedder

    app = _make_client(db_session, embeddings_enabled=True, embedder=FakeEmbedder)
    with TestClient(app) as c:
        dir_body = c.post("/ingest", params={"path": str(FIXTURE)}).json()
        assert dir_body["embed_status"] == "ok"
        assert dir_body["embedded_count"] == 3

        zip_body = c.post(
            "/ingest",
            params={"bundle": "crypto_bitcoin"},
            files={"file": ("bundle.zip", _make_zip(FIXTURE), "application/zip")},
        ).json()
        assert zip_body["embed_status"] == "ok"
        assert zip_body["embedded_count"] == 3
    app.dependency_overrides.clear()


def test_ingest_embed_failure_is_nonfatal(db_session):
    from fastapi.testclient import TestClient

    app = _make_client(db_session, embeddings_enabled=True, embedder=_FailingEmbedder)
    with TestClient(app) as c:
        r = c.post("/ingest", params={"path": str(FIXTURE)})
        assert r.status_code == 200
        body = r.json()
        assert body["created"] == 3
        assert body["embed_status"] == "error"
        assert body["embedded_count"] == 0
        assert c.get("/concepts").json()["total"] == 3
    app.dependency_overrides.clear()


def test_ingest_zero_embeddable_docs_is_ok(db_session, tmp_path):
    from fastapi.testclient import TestClient
    from tests.api.test_semantic import FakeEmbedder

    (tmp_path / "index.md").write_text("# Structural only", encoding="utf-8")
    app = _make_client(db_session, embeddings_enabled=True, embedder=FakeEmbedder)
    with TestClient(app) as c:
        body = c.post("/ingest", params={"path": str(tmp_path)}).json()
        assert body["created"] == 0
        assert body["embed_status"] == "ok"
        assert body["embedded_count"] == 0
    app.dependency_overrides.clear()

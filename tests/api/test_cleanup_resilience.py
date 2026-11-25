"""TDD regression tests for codebase cleanup & resilience improvements."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_session
from app.embeddings import get_embedder
from app.main import create_app


class _FailingEmbedder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("429 rate limit exceeded")


def test_crud_create_and_update_survive_embedder_failure(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(embeddings_enabled=True)
    app.dependency_overrides[get_embedder] = _FailingEmbedder
    with TestClient(app) as c:
        r_create = c.post("/concepts", json={"id": "a", "type": "Doc", "title": "Alpha"})
        assert r_create.status_code == 201
        assert c.get("/concepts/a").status_code == 200

        r_update = c.put("/concepts/a", json={"type": "Doc", "title": "Alpha 2"})
        assert r_update.status_code == 200
        assert c.get("/concepts/a").json()["title"] == "Alpha 2"
    app.dependency_overrides.clear()


def test_ui_search_and_hybrid_search_fallback_to_keyword_on_embed_error(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(embeddings_enabled=True)
    app.dependency_overrides[get_embedder] = _FailingEmbedder
    with TestClient(app) as c:
        c.post("/concepts", json={"id": "btc", "type": "Doc", "title": "Bitcoin", "body": "ledger"})

        ui_r = c.get("/ui/search", params={"q": "bitcoin"})
        assert ui_r.status_code == 200
        assert "Bitcoin" in ui_r.text

        api_r = c.get("/search", params={"q": "bitcoin", "mode": "hybrid"})
        assert api_r.status_code == 200
        assert api_r.json()["total"] == 1
        assert api_r.json()["items"][0]["id"] == "btc"
    app.dependency_overrides.clear()


def test_private_mode_gates_openapi_docs_behind_auth(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: Settings(private_mode=True, api_key="k-secret"),
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        private_mode=True, api_key="k-secret"
    )
    with TestClient(app) as c:
        anon_docs = c.get("/docs", follow_redirects=False)
        assert anon_docs.status_code == 302
        assert anon_docs.headers["location"] == "/auth/login"
        assert c.get("/openapi.json").status_code == 401

        hdrs = {"Authorization": "Bearer k-secret"}
        ok_docs = c.get("/docs", headers=hdrs)
        assert ok_docs.status_code == 200
        assert "swagger-ui" in ok_docs.text.lower()
        assert "https://cdn.jsdelivr.net" in ok_docs.headers["content-security-policy"]

        ok_schema = c.get("/openapi.json", headers=hdrs)
        assert ok_schema.status_code == 200
        assert "paths" in ok_schema.json()
    app.dependency_overrides.clear()

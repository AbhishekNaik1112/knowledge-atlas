"""M12 — API-key auth on write endpoints (reads stay open; disabled when no key configured)."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_session
from app.main import create_app


@pytest.fixture
def auth_client(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(api_key="secret")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _payload():
    return {"id": "a", "type": "Doc"}


def test_write_without_key_401(auth_client):
    assert auth_client.post("/concepts", json=_payload()).status_code == 401


def test_write_bad_key_403(auth_client):
    r = auth_client.post("/concepts", json=_payload(), headers={"X-API-Key": "wrong"})
    assert r.status_code == 403


def test_write_good_key_201(auth_client):
    r = auth_client.post("/concepts", json=_payload(), headers={"X-API-Key": "secret"})
    assert r.status_code == 201


def test_read_not_protected(auth_client):
    assert auth_client.get("/concepts").status_code == 200


def test_auth_disabled_by_default(client):
    # default client fixture has api_key=None -> writes are open
    assert client.post("/concepts", json=_payload()).status_code == 201


def test_validate_requires_key_when_configured(auth_client, tmp_path):
    (tmp_path / "a.md").write_text("---\ntype: Doc\n---\nx", encoding="utf-8")
    assert auth_client.post("/validate", params={"path": str(tmp_path)}).status_code == 401
    assert (
        auth_client.post(
            "/validate", params={"path": str(tmp_path)}, headers={"X-API-Key": "secret"}
        ).status_code
        == 200
    )

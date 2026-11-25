"""TDD tests for OKF Markdown .zip export (Phase 4)."""

from __future__ import annotations

import io
import zipfile

from fastapi.testclient import TestClient

from app.bundle import read_zip
from app.config import Settings, get_settings
from app.db import get_session
from app.main import create_app
from app.rules import validate_bundle


def test_export_zip_roundtrips_valid_okf_markdown(client):
    client.post(
        "/concepts",
        json={
            "id": "notes/alpha",
            "type": "technical-note",
            "bundle": "mcp",
            "title": "Alpha",
            "description": "Desc",
            "tags": ["ai"],
            "body": "See [beta](beta.md)",
        },
    )
    client.post(
        "/concepts",
        json={
            "id": "notes/beta",
            "type": "technical-note",
            "bundle": "other",
            "title": "Beta",
            "body": "Hello",
        },
    )

    r = client.get("/export.zip")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert set(zf.namelist()) == {"notes/alpha.md", "notes/beta.md"}

    entries = read_zip(r.content)
    report = validate_bundle([(e.rel_path, e.text) for e in entries])
    assert report.concept_count == 2
    assert [i for i in report.issues if i.severity == "error"] == []

    filtered = client.get("/export.zip", params={"bundle": "mcp"})
    assert filtered.status_code == 200
    with zipfile.ZipFile(io.BytesIO(filtered.content)) as zf:
        assert zf.namelist() == ["notes/alpha.md"]


def test_export_zip_protected_in_private_mode(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        private_mode=True, api_key="k-secret"
    )
    with TestClient(app) as c:
        assert c.get("/export.zip").status_code == 401
        ok = c.get("/export.zip", headers={"Authorization": "Bearer k-secret"})
        assert ok.status_code == 200
    app.dependency_overrides.clear()

"""TDD & abuse-case tests for private mode, GitHub OAuth allowlist, and hardening (Phase 2)."""

from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_session
from app.main import create_app


def _private_settings(**over) -> Settings:
    base = dict(
        private_mode=True,
        api_key="k-secret",
        session_secret="s-secret-32bytes-minimum-key!",
        github_client_id="cid",
        github_client_secret="csec",
        allowed_github_login="AbhishekNaik1112",
        rate_limit_auth_per_5min=10,
        rate_limit_api_per_min=120,
    )
    base.update(over)
    return Settings(**base)


@pytest.fixture
def private_client(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: _private_settings()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_private_mode_blocks_unauthenticated_reads_and_redirects_ui(private_client):
    assert private_client.get("/concepts").status_code == 401
    assert private_client.get("/search", params={"q": "x"}).status_code == 401
    assert private_client.get("/graph").status_code == 401
    assert private_client.get("/syncs").status_code == 401

    ui = private_client.get("/ui", follow_redirects=False)
    assert ui.status_code == 302
    assert ui.headers["location"] == "/auth/login"

    assert private_client.get("/health").status_code == 200


def test_private_mode_fails_closed_when_secrets_missing(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(private_mode=True)
    with TestClient(app) as c:
        assert c.get("/concepts").status_code == 503
        assert c.post("/concepts", json={"id": "a", "type": "Doc"}).status_code == 503
    app.dependency_overrides.clear()


def test_bearer_token_allows_api_and_rejects_bad_token(private_client):
    ok = private_client.get("/concepts", headers={"Authorization": "Bearer k-secret"})
    assert ok.status_code == 200
    bad = private_client.get("/concepts", headers={"Authorization": "Bearer wrong"})
    assert bad.status_code == 403


def test_github_oauth_flow_allowlist_and_abuse_cases(private_client, monkeypatch):
    # 1. Start OAuth sets state cookie and redirects to GitHub
    start = private_client.get("/auth/github", follow_redirects=False)
    assert start.status_code == 302
    assert "https://github.com/login/oauth/authorize" in start.headers["location"]
    assert "state=" in start.headers["location"]
    state_cookie = start.cookies.get("ka_oauth_state")
    assert state_cookie

    # 2. Bad state rejected (CSRF check)
    bad_state = private_client.get(
        "/auth/github/callback", params={"code": "abc", "state": "wrong"}, follow_redirects=False
    )
    assert bad_state.status_code == 400

    # Extract actual state value from redirect URL
    from urllib.parse import parse_qs, urlparse

    real_state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]

    # 3. Wrong GitHub user rejected (403, no session cookie)
    monkeypatch.setattr("app.routers.auth._exchange_github_code", lambda code, s: "gh-tok")
    monkeypatch.setattr("app.routers.auth._fetch_github_login", lambda tok: "evil-user")
    evil = private_client.get(
        "/auth/github/callback", params={"code": "abc", "state": real_state}, follow_redirects=False
    )
    assert evil.status_code == 403
    assert "ka_session" not in evil.cookies

    # 4. Allowed owner login sets HttpOnly session cookie and grants /ui access
    start2 = private_client.get("/auth/github", follow_redirects=False)
    real_state2 = parse_qs(urlparse(start2.headers["location"]).query)["state"][0]
    monkeypatch.setattr("app.routers.auth._fetch_github_login", lambda tok: "AbhishekNaik1112")
    good = private_client.get(
        "/auth/github/callback", params={"code": "abc", "state": real_state2}, follow_redirects=False
    )
    assert good.status_code == 302
    assert good.headers["location"] == "/ui"
    assert "ka_session" in good.cookies
    set_cookie_hdr = good.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie_hdr

    assert private_client.get("/ui").status_code == 200

    # 5. Tampered session cookie rejected
    private_client.cookies.set("ka_session", "tampered.cookie")
    tampered = private_client.get("/ui", follow_redirects=False)
    assert tampered.status_code == 302 and tampered.headers["location"] == "/auth/login"

    # 6. Logout requires POST (no GET logout CSRF)
    assert private_client.get("/auth/logout").status_code == 405
    logout = private_client.post("/auth/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/auth/login"


def test_auth_rate_limit_triggers_429(private_client):
    for _ in range(10):
        r = private_client.get("/auth/login")
        assert r.status_code == 200
    blocked = private_client.get("/auth/login")
    assert blocked.status_code == 429


def test_security_headers_present(private_client):
    r = private_client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "referrer-policy" in r.headers
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_zip_path_traversal_and_file_count_rejected(private_client):
    headers = {"Authorization": "Bearer k-secret"}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../escape.md", "---\ntype: Doc\n---\nevil")
    r_trav = private_client.post(
        "/ingest",
        headers=headers,
        files={"file": ("trav.zip", buf.getvalue(), "application/zip")},
    )
    assert r_trav.status_code == 400

    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, "w") as zf:
        for i in range(501):
            zf.writestr(f"n{i}.md", "---\ntype: Doc\n---\nok")
    r_many = private_client.post(
        "/ingest",
        headers=headers,
        files={"file": ("many.zip", buf2.getvalue(), "application/zip")},
    )
    assert r_many.status_code == 400


def test_private_mode_blocks_server_path_ingest(private_client, tmp_path):
    (tmp_path / "a.md").write_text("---\ntype: Doc\n---\nx", encoding="utf-8")
    r = private_client.post(
        "/ingest",
        params={"path": str(tmp_path)},
        headers={"Authorization": "Bearer k-secret"},
    )
    assert r.status_code == 403


def test_repo_syncer_cloud_mode_blocks_non_github_ssrf(monkeypatch):
    import subprocess
    from app.webhook import RepoSyncer

    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(subprocess, "run", fake_run)
    RepoSyncer(cloud_mode=True).sync(
        {"repository": {"clone_url": "http://169.254.169.254/latest", "name": "evil"}}
    )
    assert not called

"""GitHub OAuth login/callback/logout routes for private mode."""

from __future__ import annotations

import hmac
import logging
import secrets
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.security import (
    OAUTH_STATE_COOKIE,
    SESSION_COOKIE,
    is_https_request,
    sign_token,
    verify_token,
)

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
router = APIRouter(prefix="/auth", tags=["auth"])

_OAUTH_TIMEOUT = 15.0
_SESSION_TTL_SECONDS = 86400  # 24 hours
_STATE_TTL_SECONDS = 300      # 5 minutes


def _exchange_github_code(code: str, settings: Settings) -> str:
    resp = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
        },
        timeout=_OAUTH_TIMEOUT,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="GitHub OAuth token exchange failed")
    return str(token)


def _fetch_github_login(access_token: str) -> str:
    resp = httpx.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=_OAUTH_TIMEOUT,
    )
    resp.raise_for_status()
    login = resp.json().get("login")
    if not login:
        raise HTTPException(status_code=400, detail="GitHub user profile missing login")
    return str(login)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="login.html", context={})


@router.get("/github")
def github_login(request: Request, settings: Settings = Depends(get_settings)) -> RedirectResponse:
    if not (
        settings.github_client_id
        and settings.github_client_secret
        and settings.session_secret
        and settings.allowed_github_login
    ):
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    state = secrets.token_urlsafe(32)
    signed_state = sign_token({"state": state}, settings.session_secret, _STATE_TTL_SECONDS)
    callback_url = str(request.url_for("github_callback"))
    params = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": callback_url,
            "scope": "read:user",
            "state": state,
        }
    )
    resp = RedirectResponse(
        url=f"https://github.com/login/oauth/authorize?{params}", status_code=302
    )
    resp.set_cookie(
        OAUTH_STATE_COOKIE,
        signed_state,
        httponly=True,
        secure=is_https_request(request),
        samesite="lax",
        max_age=_STATE_TTL_SECONDS,
        path="/",
    )
    return resp


@router.get("/github/callback", name="github_callback")
def github_callback(
    request: Request,
    code: str = Query(min_length=1),
    state: str = Query(min_length=1),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if not (
        settings.github_client_id
        and settings.github_client_secret
        and settings.session_secret
        and settings.allowed_github_login
    ):
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    state_cookie = request.cookies.get(OAUTH_STATE_COOKIE)
    parsed_state = verify_token(state_cookie or "", settings.session_secret)
    if not parsed_state or not hmac.compare_digest(str(parsed_state.get("state", "")), state):
        logger.warning("Rejected GitHub OAuth callback with invalid state")
        raise HTTPException(status_code=400, detail="invalid OAuth state")

    access_token = _exchange_github_code(code, settings)
    login = _fetch_github_login(access_token)
    if login.lower() != settings.allowed_github_login.lower():
        logger.warning("Rejected unauthorized GitHub OAuth login attempt for user=%s", login)
        raise HTTPException(status_code=403, detail="not authorized")

    session_token = sign_token({"sub": login}, settings.session_secret, _SESSION_TTL_SECONDS)
    resp = RedirectResponse(url="/ui", status_code=302)
    resp.delete_cookie(OAUTH_STATE_COOKIE, path="/")
    resp.set_cookie(
        SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=is_https_request(request),
        samesite="lax",
        max_age=_SESSION_TTL_SECONDS,
        path="/",
    )
    return resp


@router.post("/logout")
def logout() -> RedirectResponse:
    resp = RedirectResponse(url="/auth/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    resp.delete_cookie(OAUTH_STATE_COOKIE, path="/")
    return resp

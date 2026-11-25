"""Authentication & abuse-proof access control.

- Local/self-host default (`private_mode=False`, `api_key=None`): open for convenience.
- Once `api_key` is set (non-private mode): mutating routes require `X-API-Key` or `Bearer`.
- In `private_mode=True` (cloud): ALL read, write, UI, and MCP routes fail-closed unless
  authorized via a signed GitHub-allowlisted session cookie or `API_KEY`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time

from fastapi import Depends, HTTPException, Request

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

SESSION_COOKIE = "ka_session"
OAUTH_STATE_COOKIE = "ka_oauth_state"


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(raw: str) -> bytes:
    pad = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + pad)


def sign_token(payload: dict, secret: str, ttl_seconds: int) -> str:
    body = dict(payload)
    body["exp"] = int(time.time()) + ttl_seconds
    encoded = _b64_encode(json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64_encode(hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest())
    return f"{encoded}.{sig}"


def verify_token(token: str, secret: str) -> dict | None:
    if not token or "." not in token:
        return None
    encoded, sig = token.split(".", 1)
    expected = _b64_encode(
        hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_b64_decode(encoded).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict) or int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


def is_https_request(request: Request) -> bool:
    proto = request.headers.get("x-forwarded-proto", "")
    return request.url.scheme == "https" or proto.split(",")[0].strip().lower() == "https"


def extract_api_key(request: Request) -> str | None:
    if x_key := request.headers.get("x-api-key"):
        return x_key
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        return token or None
    return None


def get_authenticated_user(request: Request, settings: Settings) -> str | None:
    if not settings.session_secret or not settings.allowed_github_login:
        return None
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie:
        return None
    payload = verify_token(cookie, settings.session_secret)
    if not payload:
        return None
    sub = payload.get("sub")
    if isinstance(sub, str) and sub.lower() == settings.allowed_github_login.lower():
        return sub
    return None


def _has_private_auth_config(settings: Settings) -> bool:
    has_api = bool(settings.api_key)
    has_oauth = bool(settings.session_secret and settings.allowed_github_login)
    return has_api or has_oauth


def _check_api_key_or_session(request: Request, settings: Settings) -> bool:
    """Return True if authenticated, raise 401/403 on failure."""
    if get_authenticated_user(request, settings) is not None:
        return True
    provided = extract_api_key(request)
    if provided is None:
        return False
    if settings.api_key and hmac.compare_digest(provided, settings.api_key):
        return True
    logger.warning("Rejected invalid API key for %s", request.url.path)
    raise HTTPException(status_code=403, detail="invalid API key")


def require_api_key(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.private_mode:
        require_private_access(request, settings)
        return
    if settings.api_key is None:
        return
    if _check_api_key_or_session(request, settings):
        return
    raise HTTPException(status_code=401, detail="missing API key")


def require_private_access(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.private_mode:
        return
    if not _has_private_auth_config(settings):
        raise HTTPException(status_code=503, detail="private auth not configured")
    if _check_api_key_or_session(request, settings):
        return
    if request.url.path.startswith("/ui"):
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"}, detail="login required")
    raise HTTPException(status_code=401, detail="authentication required")

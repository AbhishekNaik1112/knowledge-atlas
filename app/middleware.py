"""Security headers, request body limits, and bounded IP rate-limiting middlewares."""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import Settings, get_settings
from app.security import is_https_request

logger = logging.getLogger(__name__)

_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://unpkg.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "object-src 'none'"
)
_MAX_TRACKED_IPS = 10_000
_MAX_JSON_BODY = 1 * 1024 * 1024     # 1 MB
_MAX_UPLOAD_BODY = 10 * 1024 * 1024  # 10 MB


def _current_settings(app: Any) -> Settings:
    overrides = getattr(app, "dependency_overrides", None)
    provider = overrides.get(get_settings, get_settings) if overrides else get_settings
    return provider()


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault("Content-Security-Policy", _CSP)
        if is_https_request(request):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        raw_len = request.headers.get("content-length")
        if raw_len is not None:
            try:
                size = int(raw_len)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "invalid content-length"})
            limit = (
                _MAX_UPLOAD_BODY
                if request.url.path.startswith(("/ingest", "/validate"))
                else _MAX_JSON_BODY
            )
            if size > limit:
                return JSONResponse(status_code=413, content={"detail": "request body too large"})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._hits: dict[tuple[str, str], deque[float]] = {}

    def _allow(self, key: tuple[str, str], limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        if len(self._hits) >= _MAX_TRACKED_IPS and key not in self._hits:
            # Drop stale buckets first; fallback to clearing oldest entry if full.
            stale = [k for k, dq in self._hits.items() if not dq or now - dq[-1] > window_seconds]
            for k in stale:
                del self._hits[k]
            if len(self._hits) >= _MAX_TRACKED_IPS:
                self._hits.pop(next(iter(self._hits)))
        bucket = self._hits.setdefault(key, deque())
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path == "/health":
            return await call_next(request)
        settings = _current_settings(request.app)
        if not settings.private_mode:
            return await call_next(request)

        ip = _client_ip(request)
        if path.startswith("/auth/"):
            allowed = self._allow(("auth", ip), settings.rate_limit_auth_per_5min, 300)
        else:
            allowed = self._allow(("api", ip), settings.rate_limit_api_per_min, 60)

        if not allowed:
            logger.warning("Rate limit exceeded for ip=%s path=%s", ip, path)
            return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
        return await call_next(request)

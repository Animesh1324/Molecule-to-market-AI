"""Access control, rate limiting, and hardening for the API.

The app holds pre-launch commercial strategy — molecule selection, positioning,
forecasts — which is exactly the material a competitor would want. Until now
every endpoint was open to anyone who could reach the port.

Auth is a shared access token rather than user accounts: this is a single-team
internal tool, and a token in an env var is something the owner can rotate in
seconds without running a user database. When no token is configured the app
refuses to start in production, and warns loudly in development.
"""
import hmac
import logging
import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings

logger = logging.getLogger(__name__)

# Endpoints reachable without a token: liveness probes and the API's own docs.
PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}

ACCESS_TOKEN_HEADER = "X-API-Key"


def _configured_token() -> str:
    return os.getenv("API_ACCESS_TOKEN", "").strip()


def auth_required() -> bool:
    """Whether requests must present a token."""
    return bool(_configured_token())


def verify_token(supplied: Optional[str]) -> bool:
    """Constant-time comparison so a token cannot be recovered by timing."""
    expected = _configured_token()
    if not expected:
        return True
    if not supplied:
        return False
    return hmac.compare_digest(supplied.strip(), expected)


async def require_access(request: Request) -> None:
    """FastAPI dependency enforcing the access token on protected routes."""
    if not auth_required():
        return
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return

    supplied = request.headers.get(ACCESS_TOKEN_HEADER)
    if not supplied:
        # Allow a bearer token too, so the API is usable from tools that only
        # speak Authorization headers.
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:]

    if not verify_token(supplied):
        # Log the source but never the supplied value.
        logger.warning(
            "Rejected unauthenticated request to %s from %s",
            request.url.path,
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API access token.",
            headers={"WWW-Authenticate": ACCESS_TOKEN_HEADER},
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Response headers that blunt clickjacking, sniffing, and referrer leaks."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        # The API returns JSON and Office documents, never HTML that should run
        # script, so the strictest CSP is safe here.
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
        if get_settings()["app_env"] == "production":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client limit.

    Guards against credential-stuffing against the token and against a scripted
    caller exhausting the upstream PubMed / ClinicalTrials.gov / FDA quotas that
    every user of this deployment shares.
    """

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        # Behind a proxy the real client is the first hop in X-Forwarded-For.
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        key = self._client_key(request)
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - hits[0])) + 1
            logger.warning("Rate limit hit for %s on %s", key, request.url.path)
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": f"Rate limit exceeded. Retry in {retry_after}s."},
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(hits)))
        return response


def enforce_startup_policy() -> None:
    """Refuse to run an unauthenticated instance in production."""
    settings = get_settings()
    if settings["app_env"] == "production" and not auth_required():
        raise RuntimeError(
            "API_ACCESS_TOKEN is not set. Refusing to start an unauthenticated "
            "production instance — this API serves confidential brand strategy. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    if not auth_required():
        logger.warning(
            "API_ACCESS_TOKEN is not set: every endpoint is open. Acceptable on "
            "localhost only. Set it before exposing this app on any network."
        )

"""API key auth for MemoryAgent HTTP API."""

from typing import Optional, Set

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.config import settings

PUBLIC_PATHS: Set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}


def _extract_api_key(request: Request) -> Optional[str]:
    header = request.headers.get("X-API-Key")
    if header:
        return header.strip()
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def is_auth_enabled() -> bool:
    return bool(settings.MEMORYAGENT_API_KEY)


def verify_api_key(provided: Optional[str]) -> bool:
    if not is_auth_enabled():
        return True
    return provided == settings.MEMORYAGENT_API_KEY


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or not path.startswith("/api"):
            return await call_next(request)
        if not is_auth_enabled():
            return await call_next(request)
        if not verify_api_key(_extract_api_key(request)):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key. Use X-API-Key or Authorization: Bearer."},
            )
        return await call_next(request)

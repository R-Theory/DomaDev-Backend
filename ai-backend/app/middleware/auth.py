from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import get_settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
        settings = get_settings()
        path = request.url.path
        if path.startswith("/health") or path.startswith("/api/health"):
            return await call_next(request)
        if path.startswith("/metrics") and settings.metrics_public:
            return await call_next(request)
        if not settings.auth_required:
            return await call_next(request)
        if not settings.api_key:
            # No API key configured => open access
            return await call_next(request)
        provided = request.headers.get("X-API-Key")
        if not provided or provided != settings.api_key:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")
        return await call_next(request)

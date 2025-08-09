from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "request",
                path=request.url.path,
                method=request.method,
                status=status_code,
                duration_ms=duration_ms,
                request_id=request_id,
            )
        # Ensure X-Request-Id is set
        response.headers.setdefault("X-Request-Id", request_id)
        return response

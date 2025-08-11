from __future__ import annotations

from typing import List

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from .config import get_settings
from .middleware.auth import ApiKeyMiddleware
from .middleware.logging import RequestLoggingMiddleware
from .middleware.ratelimit import RateLimitMiddleware
from .routers import chat, embeddings, health, models


# Configure structlog basic setup
structlog.configure(processors=[structlog.processors.JSONRenderer()])


def create_app() -> FastAPI:
    # Reload settings to reflect current environment (useful for tests)
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    settings = get_settings()

    # Initialize database and tables
    try:
        from .db.base import create_all  # lazy import so env is loaded
        create_all()
    except Exception:
        # Avoid failing app startup if DB init fails; routes may still be useful
        pass

    app = FastAPI(title="AI Backend Gateway", version="0.1.0", openapi_url="/openapi.json")

    # Middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(ApiKeyMiddleware)

    # CORS
    allow_origins: List[str] = settings.allow_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Routers under /api
    api = FastAPI(openapi_url=None)
    api.include_router(health.router)
    api.include_router(models.router)
    api.include_router(chat.router)
    api.include_router(embeddings.router)
    # Storage/search APIs
    from .routers import conversations, messages, search, backup
    api.include_router(conversations.router)
    api.include_router(messages.router)
    api.include_router(search.router)
    api.include_router(backup.router)

    app.mount("/api", api)

    # Expose health at root too for convenience
    app.include_router(health.router)

    if settings.prometheus_enable:
        @app.get("/metrics")
        async def metrics():  # type: ignore[no-redef]
            # Using default registry
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()

from __future__ import annotations

import time
from typing import Callable, Optional

import structlog
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import get_settings

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


logger = structlog.get_logger()


class InMemoryBucket:
    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.allowance = {}
        self.last_check = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        last = self.last_check.get(key, now)
        self.last_check[key] = now
        allowance = self.allowance.get(key, self.capacity)
        allowance += (now - last) * self.refill_per_second
        if allowance > self.capacity:
            allowance = self.capacity
        if allowance < 1.0:
            self.allowance[key] = allowance
            return False
        else:
            self.allowance[key] = allowance - 1.0
            return True


class RedisBucket:
    def __init__(self, client, capacity: int, refill_per_second: float) -> None:
        self.client = client
        self.capacity = capacity
        self.refill_per_second = refill_per_second

    def allow(self, key: str) -> bool:
        # Simple approximation using TTL counters
        # Key design: rate:{key}
        pipe = self.client.pipeline(transaction=True)
        key_name = f"rate:{key}"
        try:
            pipe.incr(key_name, 1)
            pipe.expire(key_name, 60)
            count, _ = pipe.execute()
            return int(count) <= self.capacity
        except Exception:
            # Fail-open
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        settings = get_settings()
        capacity = max(1, settings.rate_limit_per_minute)
        refill = capacity / 60.0
        if settings.use_redis and settings.redis_url and redis is not None:
            try:
                client = redis.from_url(settings.redis_url)
                # test ping
                client.ping()
                self.bucket = RedisBucket(client, capacity, refill)
                logger.info("ratelimit", backend="redis")
            except Exception:
                self.bucket = InMemoryBucket(capacity, refill)
                logger.info("ratelimit", backend="memory_fallback")
        else:
            self.bucket = InMemoryBucket(capacity, refill)
            logger.info("ratelimit", backend="memory")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
        client_ip = request.client.host if request.client else "unknown"
        if not self.bucket.allow(client_ip):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        return await call_next(request)

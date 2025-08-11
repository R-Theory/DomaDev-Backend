from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    api_port: int = Field(default_factory=lambda: int(os.getenv("API_PORT", os.getenv("PORT", 5050))))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    # CORS
    allow_origins: List[str] = Field(default_factory=lambda: _parse_csv(os.getenv("ALLOW_ORIGINS", "*")))

    # Auth
    api_key: Optional[str] = Field(default=os.getenv("API_KEY"))
    auth_required: bool = Field(default=os.getenv("AUTH_REQUIRED", "true").lower() in {"1", "true", "yes"})
    metrics_public: bool = Field(default=os.getenv("METRICS_PUBLIC", "false").lower() in {"1", "true", "yes"})

    # Prometheus
    prometheus_enable: bool = Field(default=os.getenv("PROMETHEUS_ENABLE", "true").lower() in {"1", "true", "yes"})

    # Rate limiting
    rate_limit_per_minute: int = Field(default=int(os.getenv("RATE_LIMIT_PER_MIN", "60")))
    use_redis: bool = Field(default=os.getenv("USE_REDIS", "false").lower() in {"1", "true", "yes"})
    redis_url: Optional[str] = Field(default=os.getenv("REDIS_URL"))

    # vLLM routing
    default_model_key: str = Field(default=os.getenv("DEFAULT_MODEL_KEY", ""))
    default_model_name: str = Field(default=os.getenv("DEFAULT_MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"))

    # Back-compat single route (if no MODEL_ROUTE_* provided)
    vllm_base_url: Optional[str] = Field(default=os.getenv("VLLM_BASE_URL"))

    # Allowlist
    allowed_models: List[str] = Field(default_factory=lambda: _parse_csv(os.getenv("ALLOWED_MODELS")))

    # HTTP timeouts
    connect_timeout_seconds: float = Field(default=float(os.getenv("CONNECT_TIMEOUT_SECONDS", "10")))
    read_timeout_seconds: float = Field(default=float(os.getenv("READ_TIMEOUT_SECONDS", "60")))
    write_timeout_seconds: float = Field(default=float(os.getenv("WRITE_TIMEOUT_SECONDS", "60")))
    total_timeout_seconds: float = Field(default=float(os.getenv("TOTAL_TIMEOUT_SECONDS", "180")))

    # Database
    database_url: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./data/ai_backend.db"))
    db_echo: bool = Field(default=os.getenv("DB_ECHO", "false").lower() in {"1", "true", "yes"})

    def get_route_map(self) -> Dict[str, str]:
        routes: Dict[str, str] = {}
        for key, value in os.environ.items():
            if not key.startswith("MODEL_ROUTE_"):
                continue
            route_key = key[len("MODEL_ROUTE_") :].strip()
            if not route_key or not value:
                continue
            routes[route_key.lower()] = value.rstrip("/")
        # Fallback to VLLM_BASE_URL if provided and no explicit routes
        if not routes and self.vllm_base_url:
            routes["default"] = self.vllm_base_url.rstrip("/")
            if not self.default_model_key:
                self.default_model_key = "default"
        return routes


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

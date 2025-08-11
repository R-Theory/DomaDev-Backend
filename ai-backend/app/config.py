from __future__ import annotations

import os
import socket
from functools import lru_cache
from typing import Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def find_free_port(start_port: int = 5050, max_attempts: int = 100) -> int:
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    api_port: int = Field(default_factory=lambda: int(os.getenv("API_PORT", os.getenv("PORT", 5050))))
    host: str = Field(default=os.getenv("HOST", "0.0.0.0"))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    
    # Dynamic Port Allocation
    auto_find_port: bool = Field(default=os.getenv("AUTO_FIND_PORT", "false").lower() in {"1", "true", "yes"})
    port_range_start: int = Field(default=int(os.getenv("PORT_RANGE_START", "5050")))
    port_range_end: int = Field(default=int(os.getenv("PORT_RANGE_END", "5100")))

    # CORS
    allow_origins: str = Field(default="*")

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
    allowed_models: str = Field(default="")

    # HTTP timeouts
    connect_timeout_seconds: float = Field(default=float(os.getenv("CONNECT_TIMEOUT_SECONDS", "10")))
    read_timeout_seconds: float = Field(default=float(os.getenv("READ_TIMEOUT_SECONDS", "60")))
    write_timeout_seconds: float = Field(default=float(os.getenv("WRITE_TIMEOUT_SECONDS", "60")))
    total_timeout_seconds: float = Field(default=float(os.getenv("TOTAL_TIMEOUT_SECONDS", "180")))

    # Database
    database_url: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./data/ai_backend.db"))
    db_echo: bool = Field(default=os.getenv("DB_ECHO", "false").lower() in {"1", "true", "yes"})

    # Development
    debug: bool = Field(default=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"})
    reload: bool = Field(default=os.getenv("RELOAD", "true").lower() in {"1", "true", "yes"})

    def get_available_port(self) -> int:
        """Get an available port, either from config or by finding a free one"""
        if self.auto_find_port:
            return find_free_port(self.port_range_start, self.port_range_end - self.port_range_start)
        return self.api_port

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

    @property
    def allow_origins_list(self) -> List[str]:
        """Get allow_origins as a list"""
        return _parse_csv(self.allow_origins)

    @property
    def allowed_models_list(self) -> List[str]:
        """Get allowed_models as a list"""
        return _parse_csv(self.allowed_models)




@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

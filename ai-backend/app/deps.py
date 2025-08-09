from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx

from .config import get_settings


class RouteRegistry:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.route_key_to_base_url: Dict[str, str] = self.settings.get_route_map()
        self._clients: Dict[str, httpx.AsyncClient] = {}
        # Cache: route_key -> (timestamp, models)
        self._models_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._models_cache_ttl_seconds: float = 10.0
        # Aggregate cache
        self._aggregate_models_cache: Optional[Tuple[float, List[Dict[str, Any]]]] = None

    def get_client(self, route_key: str) -> httpx.AsyncClient:
        route_key_norm = route_key.lower()
        base_url = self.route_key_to_base_url.get(route_key_norm)
        if base_url is None:
            raise KeyError(f"Unknown route key: {route_key}")
        if route_key_norm not in self._clients:
            timeout = httpx.Timeout(
                connect=self.settings.connect_timeout_seconds,
                read=self.settings.read_timeout_seconds,
                write=self.settings.write_timeout_seconds,
                pool=None,
            )
            self._clients[route_key_norm] = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        return self._clients[route_key_norm]

    def list_route_keys(self) -> List[str]:
        return list(self.route_key_to_base_url.keys())

    def get_base_url(self, route_key: str) -> str:
        base_url = self.route_key_to_base_url.get(route_key.lower())
        if not base_url:
            raise KeyError(f"Unknown route: {route_key}")
        return base_url

    async def _fetch_models_for_route(self, route_key: str) -> List[Dict[str, Any]]:
        route_key_norm = route_key.lower()
        now = time.time()
        cached = self._models_cache.get(route_key_norm)
        if cached and (now - cached[0]) <= self._models_cache_ttl_seconds:
            return cached[1]

        client = self.get_client(route_key_norm)
        start = time.perf_counter()
        try:
            resp = await client.get("/models")
            latency_ms = int((time.perf_counter() - start) * 1000)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("data", [])
            # Annotate each with source and latency
            enriched = []
            for m in models:
                m_id = m.get("id")
                enriched.append(
                    {
                        "id": m_id,
                        "object": m.get("object", "model"),
                        "owned_by": m.get("owned_by", ""),
                        "source": route_key_norm,
                        "latency_ms": latency_ms,
                    }
                )
            self._models_cache[route_key_norm] = (now, enriched)
            # Invalidate aggregate cache
            self._aggregate_models_cache = None
            return enriched
        except httpx.HTTPError:
            # Treat as empty for this route; cache briefly
            self._models_cache[route_key_norm] = (now, [])
            self._aggregate_models_cache = None
            return []

    async def aggregate_models(self) -> List[Dict[str, Any]]:
        now = time.time()
        if self._aggregate_models_cache and (now - self._aggregate_models_cache[0]) <= self._models_cache_ttl_seconds:
            return self._aggregate_models_cache[1]

        tasks = [self._fetch_models_for_route(k) for k in self.list_route_keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Combine
        id_to_sources: Dict[str, List[Dict[str, Any]]] = {}
        for res in results:
            if isinstance(res, Exception):
                continue
            for m in res:
                m_id = m.get("id")
                if not m_id:
                    continue
                id_to_sources.setdefault(m_id, []).append({"source": m["source"], "latency_ms": m["latency_ms"]})
        aggregated: List[Dict[str, Any]] = []
        for m_id, sources in id_to_sources.items():
            aggregated.append({"id": m_id, "object": "model", "sources": sources})

        self._aggregate_models_cache = (now, aggregated)
        return aggregated

    async def infer_route_by_model(self, model_id: str) -> Optional[str]:
        if not model_id:
            return None
        models = await self.aggregate_models()
        candidates = [m for m in models if m.get("id") == model_id]
        if len(candidates) == 1:
            # Return the first/only source key
            sources = candidates[0].get("sources", [])
            if len(sources) == 1:
                return sources[0]["source"]
            # Multiple instances serve it; ambiguous
            return None
        # 0 or >1 aggregated entries: ambiguous
        return None


route_registry = RouteRegistry()


async def iter_upstream_stream(
    client: httpx.AsyncClient, path: str, json: Dict[str, Any]
) -> AsyncIterator[bytes]:
    async with client.stream("POST", path, json=json) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line:
                continue
            yield (line + "\n").encode("utf-8")

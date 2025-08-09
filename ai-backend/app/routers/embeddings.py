from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..clients import vllm_client
from ..config import get_settings
from ..routing.router import resolve_embeddings_route_and_model


class EmbeddingsRequest(BaseModel):
    input: Any
    model: Optional[str] = None
    modelKey: Optional[str] = Field(default=None, description="Routing key to select vLLM instance")


router = APIRouter(prefix="/embeddings")


async def _resolve_route_and_model(payload: EmbeddingsRequest) -> Tuple[str, str]:
    return await resolve_embeddings_route_and_model(payload.model, payload.modelKey)


@router.post("")
async def create_embeddings(payload: EmbeddingsRequest):
    route_key, model = await _resolve_route_and_model(payload)
    body: Dict[str, Any] = {"input": payload.input, "model": model}
    return await vllm_client.create_embedding(route_key, body)

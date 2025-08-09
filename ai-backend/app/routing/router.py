from __future__ import annotations

from typing import Optional, Tuple, Literal, List, Dict, Any

from fastapi import HTTPException, status

from ..config import get_settings
from ..deps import route_registry


def _validate_model_allowed(model: str) -> None:
    settings = get_settings()
    if settings.allowed_models and model not in settings.allowed_models:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Model is not allowed by ALLOWED_MODELS",
        )


async def _resolve_static_route(
    task: Literal["chat", "embeddings"],
    model: Optional[str],
    model_key: Optional[str],
) -> Tuple[str, str]:
    """
    Static routing resolution replicating existing behavior:
    - If modelKey provided: ensure route exists and serves the model
    - Else try to infer route by model id across known routes
    - If model explicit but ambiguous/unavailable: return 409 w/ guidance
    - Else fallback to default route and default model name
    """
    settings = get_settings()
    model_provided = model is not None
    effective_model = model or settings.default_model_name

    _validate_model_allowed(effective_model)

    if model_key:
        route_key = model_key.lower()
        # Validate route exists and model is served there
        try:
            models_on_route = await route_registry._fetch_models_for_route(route_key)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Unknown modelKey; configure MODEL_ROUTE_<KEY> in environment",
                    "provided_modelKey": route_key,
                    "available_modelKeys": route_registry.list_route_keys(),
                },
            )
        valid_ids = {m.get("id") for m in models_on_route}
        if effective_model not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Requested model is not served by the selected route",
                    "route": route_key,
                    "valid_model_ids": sorted(list(valid_ids)),
                },
            )
        return route_key, effective_model

    # No modelKey: try inference by model
    inferred = await route_registry.infer_route_by_model(effective_model)
    if inferred:
        return inferred, effective_model

    # If model was explicitly provided but inference failed/ambiguous, return 409
    if model_provided:
        # Build guidance using aggregate info
        models = await route_registry.aggregate_models()
        candidates = [m for m in models if m.get("id") == effective_model]
        detail = {
            "message": "Unable to route by model; provide modelKey or start an instance serving this model",
            "requested_model": effective_model,
            "matches": candidates,
            "available_modelKeys": route_registry.list_route_keys(),
        }
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    # Neither modelKey nor model provided: fallback to default route and default model name
    route_key = settings.default_model_key or (
        route_registry.list_route_keys()[0] if route_registry.list_route_keys() else ""
    )
    if not route_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No routes configured. Set MODEL_ROUTE_* env vars",
        )
    return route_key, effective_model


async def resolve_chat_route_and_model(
    model: Optional[str], model_key: Optional[str]
) -> Tuple[str, str]:
    # Placeholder for future strategies; default to static
    return await _resolve_static_route("chat", model, model_key)


async def resolve_embeddings_route_and_model(
    model: Optional[str], model_key: Optional[str]
) -> Tuple[str, str]:
    # Placeholder for future strategies; default to static
    return await _resolve_static_route("embeddings", model, model_key)



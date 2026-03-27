"""Health-check router."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse, summary="Liveness and model status")
async def health_check(request: Request) -> HealthResponse:
    registry = getattr(request.app.state, "registry", None)
    loaded = registry is not None and registry.is_loaded
    model_name = registry.active_model_name if loaded else "none"
    return HealthResponse(
        status="ok",
        model_loaded=loaded,
        active_model=model_name,
    )

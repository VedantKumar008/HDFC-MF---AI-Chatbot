"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    state = request.app.state.app_state
    settings = request.app.state.settings

    if state.ready:
        message = "Backend is ready."
        status = "ok"
    elif state.load_error:
        message = f"Backend failed to load knowledge base: {state.load_error}"
        status = "error"
    else:
        message = "Backend is starting."
        status = "starting"

    return HealthResponse(
        status=status,
        phase="4",
        ready=state.ready,
        schemes_loaded=state.schemes_loaded,
        index_loaded=state.index_loaded,
        embedding_model_loaded=state.embedding_model_loaded,
        chunk_count=state.chunk_count,
        index_built_at=state.index_manifest.get("built_at"),
        embedding_model=settings.embedding_model,
        startup_seconds=state.startup_seconds,
        message=message,
    )

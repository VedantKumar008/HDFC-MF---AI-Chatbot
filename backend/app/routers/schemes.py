"""Scheme directory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from backend.app.schemas import SchemesResponse

router = APIRouter(tags=["schemes"])


@router.get("/schemes", response_model=SchemesResponse)
def list_schemes(request: Request) -> SchemesResponse:
    state = request.app.state.app_state
    if not state.ready:
        raise HTTPException(
            status_code=503,
            detail="Backend is still loading scheme data. Please retry shortly.",
        )

    return SchemesResponse(count=len(state.schemes), schemes=state.schemes)

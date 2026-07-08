"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check that doesn't load any heavy dependencies."""
    return {"status": "ok"}

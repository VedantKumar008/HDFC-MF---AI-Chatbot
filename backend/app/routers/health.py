"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check that doesn't load any heavy dependencies."""
    return {"status": "ok"}


@router.get("/cors-test")
def cors_test(request: Request) -> dict[str, str]:
    """Test endpoint to verify CORS headers are being applied."""
    return {
        "status": "ok",
        "origin": request.headers.get("origin", "none"),
        "message": "CORS test endpoint - check response headers for Access-Control-Allow-Origin"
    }

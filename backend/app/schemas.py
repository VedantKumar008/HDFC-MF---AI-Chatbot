"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SchemeSummary(BaseModel):
    id: str
    name: str
    url: str
    category: str | None = None
    sub_category: str | None = None
    nav: float | None = None
    nav_date: str | None = None
    aum: float | None = None
    expense_ratio: float | None = None
    risk_level: str | None = None
    scraped_at: str | None = None


class SchemesResponse(BaseModel):
    count: int
    schemes: list[SchemeSummary]


class HealthResponse(BaseModel):
    status: str
    phase: str
    ready: bool
    schemes_loaded: int
    index_loaded: bool
    embedding_model_loaded: bool
    chunk_count: int = 0
    index_built_at: str | None = None
    embedding_model: str | None = None
    startup_seconds: float | None = None
    message: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(min_length=1, max_length=128)


class ChatResponse(BaseModel):
    session_id: str
    message: str
    placeholder: bool = True
    detail: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    extra: dict[str, Any] | None = None

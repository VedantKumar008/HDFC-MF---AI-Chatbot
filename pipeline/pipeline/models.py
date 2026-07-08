"""Typed structures for FAISS index chunks."""

from __future__ import annotations

from typing import TypedDict


class ChunkRecord(TypedDict):
    chunk_id: int
    scheme_id: str
    scheme_name: str
    scheme_url: str
    section: str
    scraped_at: str
    text: str

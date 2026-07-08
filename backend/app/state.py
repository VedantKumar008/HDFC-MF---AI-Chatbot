"""Application runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Defer heavy imports to reduce startup memory
# from pipeline.pipeline.faiss_index import FaissRetriever

from backend.app.schemas import SchemeSummary
from backend.app.session.store import SessionStore


@dataclass
class AppState:
    ready: bool = False
    startup_seconds: float | None = None
    schemes: list[SchemeSummary] = field(default_factory=list)
    retriever: Any = None  # Deferred: FaissRetriever
    index_manifest: dict[str, Any] = field(default_factory=dict)
    embedding_model_name: str = "all-MiniLM-L6-v2"
    load_error: str | None = None
    session_store: SessionStore = field(default_factory=SessionStore)

    @property
    def schemes_loaded(self) -> int:
        return len(self.schemes)

    @property
    def index_loaded(self) -> bool:
        return self.retriever is not None

    @property
    def embedding_model_loaded(self) -> bool:
        return self.retriever is not None

    @property
    def chunk_count(self) -> int:
        if not self.retriever:
            return 0
        return len(self.retriever.chunks)

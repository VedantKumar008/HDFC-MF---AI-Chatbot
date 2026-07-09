"""Vector retrieval helpers for chat queries."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

# Defer FAISS imports to avoid loading when using Pinecone
# from pipeline.pipeline.faiss_index import FaissRetriever
# from pipeline.pipeline.models import ChunkRecord

from backend.app.schemas import SchemeSummary


# Type alias for compatibility with both FAISS and Pinecone
ChunkRecord = dict[str, Any]


@dataclass
class RetrievedChunk:
    chunk: ChunkRecord
    score: float


@dataclass
class RetrievalOutput:
    chunks: list[RetrievedChunk]
    elapsed_seconds: float
    filtered_scheme_ids: list[str]


class RetrievalService:
    def __init__(
        self,
        retriever: Any,  # Can be FaissRetriever or PineconeRetriever
        schemes: list[SchemeSummary],
        *,
        top_k: int = 5,
        min_score: float = 0.4,
    ) -> None:
        self.retriever = retriever
        self.schemes = schemes
        self.top_k = top_k
        self.min_score = min_score

    def retrieve(self, query: str) -> RetrievalOutput:
        started = time.perf_counter()
        scheme_ids = detect_scheme_ids(query, self.schemes)
        
        # Handle both FAISS and Pinecone retrievers
        raw_results = self.retriever.search(query, top_k=self.top_k * 2)
        
        # Convert Pinecone results to expected format
        if hasattr(raw_results[0], 'text'):  # PineconeChunk objects
            raw_results = [
                (
                    {
                        'text': chunk.text,
                        'scheme_id': chunk.scheme_id,
                        'scheme_name': chunk.scheme_name,
                        'section': 'unknown',
                    },
                    chunk.score
                )
                for chunk in raw_results
            ]

        filtered: list[RetrievedChunk] = []
        for chunk, score in raw_results:
            if score < self.min_score:
                continue
            if scheme_ids and chunk["scheme_id"] not in scheme_ids:
                continue
            filtered.append(RetrievedChunk(chunk=chunk, score=score))

        if scheme_ids and not filtered:
            for chunk, score in raw_results:
                if score >= self.min_score:
                    filtered.append(RetrievedChunk(chunk=chunk, score=score))

        filtered = filtered[: self.top_k]
        elapsed = time.perf_counter() - started
        return RetrievalOutput(
            chunks=filtered,
            elapsed_seconds=elapsed,
            filtered_scheme_ids=scheme_ids,
        )


def detect_scheme_ids(query: str, schemes: list[SchemeSummary]) -> list[str]:
    normalized_query = _normalize(query)
    matches: list[str] = []

    for scheme in schemes:
        candidates = {
            scheme.name,
            scheme.id.replace("-", " "),
            scheme.id,
        }
        if scheme.sub_category:
            candidates.add(scheme.sub_category)

        for candidate in candidates:
            normalized_candidate = _normalize(candidate)
            if len(normalized_candidate) < 6:
                continue
            if normalized_candidate in normalized_query:
                matches.append(scheme.id)
                break

    return matches


def format_context(chunks: list[RetrievedChunk]) -> str:
    sections: list[str] = []
    for index, item in enumerate(chunks, start=1):
        chunk = item.chunk
        sections.append(
            "\n".join(
                [
                    f"[Context {index}]",
                    f"Scheme: {chunk['scheme_name']}",
                    f"Section: {chunk['section']}",
                    chunk["text"],
                ]
            )
        )
    return "\n\n".join(sections)


def _normalize(value: str) -> str:
    lowered = value.lower()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()

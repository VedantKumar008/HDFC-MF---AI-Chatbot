"""End-to-end RAG pipeline: retrieve context and stream Groq responses."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass

from pipeline.pipeline.faiss_index import FaissRetriever

from backend.app.rag.groq_client import GroqChatClient
from backend.app.rag.prompts import (
    NOT_FOUND_MESSAGE,
    SYSTEM_PROMPT,
    build_user_prompt,
    enhance_query_with_context,
)
from backend.app.rag.retrieval import RetrievalService, RetrievedChunk, format_context
from backend.app.schemas import SchemeSummary

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    retrieval_seconds: float
    has_context: bool


class RagPipeline:
    def __init__(
        self,
        retriever: FaissRetriever,
        schemes: list[SchemeSummary],
        groq_client: GroqChatClient,
        *,
        top_k: int = 5,
        min_score: float = 0.4,
        min_top_score: float = 0.45,
    ) -> None:
        self.retrieval = RetrievalService(
            retriever,
            schemes,
            top_k=top_k,
            min_score=min_score,
        )
        self.groq_client = groq_client
        self.min_top_score = min_top_score

    def retrieve(self, query: str) -> RetrievalResult:
        output = self.retrieval.retrieve(query)
        has_context = bool(output.chunks) and output.chunks[0].score >= self.min_top_score
        return RetrievalResult(
            chunks=output.chunks,
            retrieval_seconds=output.elapsed_seconds,
            has_context=has_context,
        )

    def build_messages(
        self,
        query: str,
        retrieval: RetrievalResult,
    ) -> list[dict[str, str]]:
        context = format_context(retrieval.chunks)
        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append(
            {
                "role": "user",
                "content": build_user_prompt(query, context),
            }
        )
        return messages

    def stream_answer(
        self,
        query: str,
        retrieval: RetrievalResult | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        # Enhance query with context for pronoun resolution
        enhanced_query = enhance_query_with_context(query, history)
        
        result = retrieval or self.retrieve(enhanced_query)
        if not result.has_context:
            yield NOT_FOUND_MESSAGE
            return

        messages = self.build_messages(query, result)
        if history:
            messages = [messages[0], *history, messages[-1]]

        logger.info(
            "Streaming Groq response (retrieval=%.3fs, chunks=%s, query_enhanced=%s)",
            result.retrieval_seconds,
            len(result.chunks),
            enhanced_query != query,
        )
        yield from self.groq_client.stream_completion(messages)

"""Groq streaming LLM client."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from groq import Groq

logger = logging.getLogger(__name__)


class GroqChatClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = Groq(api_key=api_key)
        self.model = model

    def stream_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Iterator[str]:
        logger.info(f"[Groq] Starting stream completion with model: {self.model}")
        logger.info(f"[Groq] Message count: {len(messages)}")
        
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        logger.info("[Groq] Stream created, yielding chunks...")
        chunk_count = 0
        first_token_received = False
        for chunk in stream:
            delta: Any = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                chunk_count += 1
                if not first_token_received:
                    logger.info("[Groq] First token received")
                    first_token_received = True
                yield content
        
        logger.info(f"[Groq] Stream complete, yielded {chunk_count} chunks")

"""Groq streaming LLM client."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from groq import Groq


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
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta: Any = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

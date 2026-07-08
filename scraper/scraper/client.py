"""HTTP client for fetching Groww mutual fund pages."""

from __future__ import annotations

import time
from typing import Final

import httpx

DEFAULT_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
DEFAULT_DELAY_SECONDS: Final[float] = 1.5


class GrowwClient:
    def __init__(
        self,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self._last_request_at = 0.0

    def fetch_html(self, url: str) -> str:
        self._respect_rate_limit()
        headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "en-IN,en;q=0.9"}
        with httpx.Client(headers=headers, follow_redirects=True, timeout=self.timeout_seconds) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_request_at = time.monotonic()

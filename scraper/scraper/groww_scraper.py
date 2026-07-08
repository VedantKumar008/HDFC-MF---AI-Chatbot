"""Groww mutual fund scraper orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from shared.schemes import Scheme, load_schemes

from .client import GrowwClient
from .extractor import build_scheme_record
from .parser import GrowwParseError, extract_html_sections, extract_mf_server_side_data
from .writer import SchemeValidationError, write_scheme_record

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    scheme_id: str
    success: bool
    output_path: Path | None = None
    error: str | None = None


@dataclass
class ScrapeSummary:
    results: list[ScrapeResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for result in self.results if result.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for result in self.results if not result.success)


class GrowwScraper:
    def __init__(
        self,
        output_dir: Path,
        delay_seconds: float = 1.5,
    ) -> None:
        self.output_dir = output_dir
        self.client = GrowwClient(delay_seconds=delay_seconds)

    def scrape_scheme(self, scheme: Scheme) -> ScrapeResult:
        scheme_id = scheme["id"]
        groww_url = scheme["url"]
        try:
            html = self.client.fetch_html(groww_url)
            mf_data = extract_mf_server_side_data(html)
            html_sections = extract_html_sections(html)
            record = build_scheme_record(scheme_id, groww_url, mf_data, html_sections)
            output_path = write_scheme_record(self.output_dir, record)
            return ScrapeResult(scheme_id=scheme_id, success=True, output_path=output_path)
        except (GrowwParseError, SchemeValidationError, Exception) as exc:
            logger.exception("Failed to scrape %s", scheme_id)
            return ScrapeResult(scheme_id=scheme_id, success=False, error=str(exc))

    def scrape_all(self, schemes: list[Scheme] | None = None) -> ScrapeSummary:
        scheme_list = schemes or load_schemes()
        summary = ScrapeSummary()
        for scheme in scheme_list:
            logger.info("Scraping %s", scheme["name"])
            summary.results.append(self.scrape_scheme(scheme))
        return summary

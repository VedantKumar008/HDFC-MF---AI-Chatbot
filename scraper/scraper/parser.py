"""Parse Groww Next.js pages into server-side mutual fund payloads."""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup


class GrowwParseError(ValueError):
    pass


def extract_mf_server_side_data(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None or not script.string:
        raise GrowwParseError("Missing __NEXT_DATA__ script on Groww page.")

    try:
        payload = json.loads(script.string)
    except json.JSONDecodeError as exc:
        raise GrowwParseError("Invalid JSON in __NEXT_DATA__.") from exc

    try:
        return payload["props"]["pageProps"]["mfServerSideData"]
    except (KeyError, TypeError) as exc:
        raise GrowwParseError("mfServerSideData not found in Groww page payload.") from exc


def extract_html_sections(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.body
    if main is None:
        return {}

    sections: dict[str, str] = {}
    for heading in main.find_all(["h2", "h3", "h4"]):
        title = _normalize_text(heading.get_text(" ", strip=True))
        if not title or len(title) > 120:
            continue

        content_parts: list[str] = []
        for sibling in heading.find_next_siblings():
            if sibling.name in {"h1", "h2", "h3", "h4"}:
                break
            text = _normalize_text(sibling.get_text(" ", strip=True))
            if text:
                content_parts.append(text)

        if content_parts:
            key = _section_key(title)
            sections[key] = "\n".join(content_parts)

    return sections


def _section_key(title: str) -> str:
    normalized = title.lower()
    replacements = {
        "about": "about",
        "investment objective": "investment_objective",
        "tax implication": "tax_implication",
        "exit load": "exit_load_section",
        "exit load, stamp duty and tax": "exit_tax_section",
        "fund management": "fund_management",
        "fund house": "fund_house",
        "minimum investments": "minimum_investments",
        "returns and rankings": "returns_and_rankings",
        "understand terms": "understand_terms",
    }
    for needle, key in replacements.items():
        if needle in normalized:
            return key
    return normalized.replace(" ", "_")[:80]


def _normalize_text(value: str) -> str:
    return " ".join(value.split())

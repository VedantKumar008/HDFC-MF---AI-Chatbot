"""Load scheme summaries from scraped JSON files."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from shared.schemes import APPROVED_SCHEME_COUNT, Scheme, load_schemes

from backend.app.schemas import SchemeSummary

logger = logging.getLogger(__name__)


def load_scheme_summaries(schemes_dir: Path) -> list[SchemeSummary]:
    manifest = load_schemes()
    summaries: list[SchemeSummary] = []

    for scheme in manifest:
        json_path = schemes_dir / f"{scheme['id']}.json"
        if not json_path.exists():
            raise FileNotFoundError(f"Missing scraped JSON for scheme: {scheme['id']}")

        with json_path.open(encoding="utf-8") as handle:
            record = json.load(handle)

        summaries.append(_to_summary(scheme, record))

    if len(summaries) != APPROVED_SCHEME_COUNT:
        raise ValueError(
            f"Expected {APPROVED_SCHEME_COUNT} scheme summaries, found {len(summaries)}."
        )

    logger.info("Loaded %s scheme summaries from %s", len(summaries), schemes_dir)
    return summaries


def _to_summary(manifest_scheme: Scheme, record: dict) -> SchemeSummary:
    groww_url = str(record.get("groww_url") or manifest_scheme["url"])
    return SchemeSummary(
        id=str(record.get("id") or manifest_scheme["id"]),
        name=str(record.get("scheme_name") or manifest_scheme["name"]),
        url=groww_url,
        category=record.get("category"),
        sub_category=record.get("sub_category"),
        nav=_as_float(record.get("nav")),
        nav_date=record.get("nav_date"),
        aum=_as_float(record.get("aum")),
        expense_ratio=_as_float(record.get("expense_ratio")),
        risk_level=record.get("risk_level"),
        scraped_at=record.get("scraped_at"),
    )


def _as_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None

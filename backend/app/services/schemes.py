"""Load scheme summaries from scraped JSON files."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from shared.schemes import APPROVED_SCHEME_COUNT, Scheme, load_schemes

from backend.app.schemas import SchemeSummary

logger = logging.getLogger(__name__)


def load_scheme_summaries(schemes_dir: Path | str) -> list[SchemeSummary]:
    manifest = load_schemes()
    summaries: list[SchemeSummary] = []

    # Convert to Path and force absolute path
    schemes_dir = Path(schemes_dir).resolve()
    
    logger.info(f"Loading schemes from directory: {schemes_dir}")
    logger.info(f"Directory exists: {schemes_dir.exists()}")
    logger.info(f"Directory absolute: {schemes_dir.absolute()}")
    
    # List all JSON files in the directory using os.listdir for better debugging
    try:
        all_files = list(schemes_dir.iterdir())
        logger.info(f"Total files in directory: {len(all_files)}")
        for f in all_files[:5]:
            logger.info(f"  - {f.name} (is_file: {f.is_file()})")
    except Exception as e:
        logger.error(f"Error listing directory: {e}")
    
    # Try glob pattern
    json_files = list(schemes_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files via glob")
    for jf in json_files[:3]:
        logger.info(f"  - {jf.name}")

    # Load all available JSON files instead of relying on manifest
    for json_file in json_files:
        try:
            with json_file.open(encoding="utf-8") as handle:
                record = json.load(handle)
            
            # Find matching scheme in manifest
            scheme_id = json_file.stem
            matching_scheme = None
            for scheme in manifest:
                if scheme['id'] == scheme_id:
                    matching_scheme = scheme
                    break
            
            if matching_scheme:
                summaries.append(_to_summary(matching_scheme, record))
                logger.info(f"Loaded scheme: {scheme_id}")
            else:
                logger.warning(f"No matching manifest entry for: {scheme_id}")
        except Exception as e:
            logger.error(f"Error loading {json_file.name}: {e}")

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

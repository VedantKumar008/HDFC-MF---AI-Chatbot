"""Validate and persist scraped scheme JSON files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .models import SchemeRecord

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = (
    "id",
    "scheme_name",
    "groww_url",
    "scraped_at",
    "category",
    "description",
    "nav",
    "aum",
    "expense_ratio",
    "exit_load",
    "risk_level",
)


class SchemeValidationError(ValueError):
    pass


def validate_scheme_record(record: SchemeRecord) -> None:
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        value = record.get(field)  # type: ignore[literal-required]
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)

    if missing:
        raise SchemeValidationError(f"Missing required fields: {', '.join(missing)}")

    if not record.get("fund_manager") and not record.get("fund_manager_details"):
        raise SchemeValidationError("Missing fund manager information.")

    if record.get("groww_url") and "groww.in/mutual-funds/" not in str(record.get("groww_url")):
        raise SchemeValidationError("Invalid Groww URL.")


def write_scheme_record(output_dir: Path, record: SchemeRecord) -> Path:
    validate_scheme_record(record)
    output_dir.mkdir(parents=True, exist_ok=True)

    scheme_id = str(record["id"])
    output_path = output_dir / f"{scheme_id}.json"
    temp_path = output_dir / f"{scheme_id}.json.tmp"

    with temp_path.open("w", encoding="utf-8") as output_file:
        json.dump(record, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")

    temp_path.replace(output_path)
    logger.info("Wrote %s", output_path.name)
    return output_path


def load_scheme_record(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)

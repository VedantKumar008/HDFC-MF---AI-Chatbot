"""Validate Phase 1 scraped scheme JSON files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.schemes import APPROVED_SCHEME_COUNT, load_schemes
from scraper.scraper.writer import REQUIRED_FIELDS, validate_scheme_record


def main() -> int:
    output_dir = PROJECT_ROOT / "data" / "schemes"
    schemes = load_schemes()
    errors: list[str] = []

    if not output_dir.exists():
        print("FAIL: data/schemes directory missing")
        return 1

    json_files = sorted(output_dir.glob("*.json"))
    if len(json_files) != APPROVED_SCHEME_COUNT:
        errors.append(f"Expected {APPROVED_SCHEME_COUNT} JSON files, found {len(json_files)}")

    manifest_ids = {scheme["id"] for scheme in schemes}
    file_ids = {path.stem for path in json_files}
    missing = manifest_ids - file_ids
    extra = file_ids - manifest_ids
    if missing:
        errors.append(f"Missing scheme files: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unexpected scheme files: {', '.join(sorted(extra))}")

    url_by_id = {scheme["id"]: scheme["url"] for scheme in schemes}

    for path in json_files:
        with path.open(encoding="utf-8") as handle:
            record = json.load(handle)
        try:
            validate_scheme_record(record)
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        if record.get("groww_url") != url_by_id.get(path.stem):
            errors.append(f"{path.name}: groww_url mismatch")

        for field in ("holdings", "historical_returns", "tax_information", "faq_content"):
            if field not in record:
                errors.append(f"{path.name}: missing section '{field}'")

    if errors:
        print("Phase 1 verification FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"OK: {len(json_files)} scheme JSON files validated")
    print(f"Required fields checked: {', '.join(REQUIRED_FIELDS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI entry point for the Groww scraper."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.schemes import APPROVED_SCHEME_COUNT, load_schemes

from .groww_scraper import GrowwScraper

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "schemes"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape approved HDFC Mutual Fund schemes from Groww."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for structured scheme JSON files.",
    )
    parser.add_argument(
        "--scheme-id",
        action="append",
        dest="scheme_ids",
        help="Scrape only the given scheme id(s). Can be passed multiple times.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Delay between HTTP requests in seconds.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    schemes = load_schemes()
    if args.scheme_ids:
        selected_ids = set(args.scheme_ids)
        schemes = [scheme for scheme in schemes if scheme["id"] in selected_ids]
        if not schemes:
            logging.error("No matching schemes found for ids: %s", ", ".join(args.scheme_ids))
            return 1

    scraper = GrowwScraper(output_dir=args.output_dir, delay_seconds=args.delay)
    summary = scraper.scrape_all(schemes)

    logging.info(
        "Scrape finished: %s succeeded, %s failed (expected %s schemes).",
        summary.success_count,
        summary.failure_count,
        len(schemes),
    )

    for result in summary.results:
        if not result.success:
            logging.error("  FAILED %s: %s", result.scheme_id, result.error)

    if summary.failure_count:
        return 1

    if summary.success_count != len(schemes):
        logging.error("Unexpected success count.")
        return 1

    if len(load_schemes()) != APPROVED_SCHEME_COUNT:
        logging.error("Approved scheme manifest count mismatch.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

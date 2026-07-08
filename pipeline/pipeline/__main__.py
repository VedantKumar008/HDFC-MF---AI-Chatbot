"""CLI entry point for the FAISS index builder."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.pipeline.builder import IndexBuildPipeline

DEFAULT_SCHEMES_DIR = PROJECT_ROOT / "data" / "schemes"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "faiss"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build FAISS vector index from scraped HDFC scheme JSON files."
    )
    parser.add_argument(
        "--schemes-dir",
        type=Path,
        default=DEFAULT_SCHEMES_DIR,
        help="Directory containing scraped scheme JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for FAISS index artifacts.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="Sentence Transformers model name.",
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

    pipeline = IndexBuildPipeline(
        schemes_dir=args.schemes_dir,
        output_dir=args.output_dir,
        embedding_model_name=args.embedding_model,
    )

    try:
        summary = pipeline.build()
    except Exception as exc:
        logging.error("Index build failed: %s", exc)
        return 1

    logging.info(
        "Built index with %s chunks from %s schemes in %.2fs",
        summary.chunk_count,
        summary.scheme_count,
        summary.elapsed_seconds,
    )
    logging.info("Artifacts written to %s", summary.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

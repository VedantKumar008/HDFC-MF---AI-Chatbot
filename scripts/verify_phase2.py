"""Validate Phase 2 FAISS index artifacts and sample retrieval."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.schemes import APPROVED_SCHEME_COUNT

from pipeline.pipeline.builder import IndexBuildPipeline
from pipeline.pipeline.storage import IndexStorage


SAMPLE_QUERIES = [
    {
        "query": "What is the expense ratio of HDFC Defence Fund?",
        "expected_scheme_id": "hdfc-defence-fund-direct-growth",
        "keywords": ["expense ratio", "0.87"],
    },
    {
        "query": "What are the top holdings of HDFC Large Cap Fund?",
        "expected_scheme_id": "hdfc-large-cap-fund-direct-growth",
        "keywords": ["holdings", "large cap"],
    },
    {
        "query": "Explain tax implications for HDFC ELSS Tax Saver Fund",
        "expected_scheme_id": "hdfc-elss-tax-saver-fund-direct-plan-growth",
        "keywords": ["tax", "elss"],
    },
]


def main() -> int:
    faiss_dir = PROJECT_ROOT / "data" / "faiss"
    storage = IndexStorage(faiss_dir)
    errors: list[str] = []

    required_files = [
        faiss_dir / IndexStorage.INDEX_FILE,
        faiss_dir / IndexStorage.CHUNKS_FILE,
        faiss_dir / IndexStorage.MANIFEST_FILE,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"Missing artifact: {path.name}")

    if errors:
        _print_errors(errors)
        return 1

    with (faiss_dir / IndexStorage.MANIFEST_FILE).open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    if manifest.get("scheme_count") != APPROVED_SCHEME_COUNT:
        errors.append(
            f"Manifest scheme_count={manifest.get('scheme_count')} expected {APPROVED_SCHEME_COUNT}"
        )

    chunk_count = manifest.get("chunk_count")
    if not chunk_count or chunk_count < APPROVED_SCHEME_COUNT:
        errors.append(f"Unexpected chunk_count: {chunk_count}")

    pipeline = IndexBuildPipeline(
        schemes_dir=PROJECT_ROOT / "data" / "schemes",
        output_dir=faiss_dir,
        embedding_model_name=manifest.get("embedding_model", "all-MiniLM-L6-v2"),
    )

    started = time.perf_counter()
    retriever = pipeline.load_retriever()
    load_seconds = time.perf_counter() - started
    if load_seconds > 30:
        errors.append(f"Index load took too long: {load_seconds:.2f}s")

    for sample in SAMPLE_QUERIES:
        started = time.perf_counter()
        results = retriever.search(sample["query"], top_k=5)
        retrieval_seconds = time.perf_counter() - started
        if retrieval_seconds > 1.0:
            errors.append(
                f"Retrieval for '{sample['query']}' took {retrieval_seconds:.2f}s (target < 1s warm)"
            )
        if not results:
            errors.append(f"No retrieval results for query: {sample['query']}")
            continue

        matched_scheme = any(
            chunk["scheme_id"] == sample["expected_scheme_id"] for chunk, _score in results
        )
        if not matched_scheme:
            top = results[0]
            errors.append(
                f"Query '{sample['query']}' did not retrieve expected scheme "
                f"{sample['expected_scheme_id']} in top 5 "
                f"(top={top[0]['scheme_id']}, score={top[1]:.3f})"
            )
            continue

        relevant_text = " ".join(
            chunk["text"].lower()
            for chunk, _score in results
            if chunk["scheme_id"] == sample["expected_scheme_id"]
        )
        if not any(keyword in relevant_text for keyword in sample["keywords"]):
            errors.append(
                f"Query '{sample['query']}' retrieved expected scheme but missing keywords "
                f"{sample['keywords']}"
            )

    if errors:
        _print_errors(errors)
        return 1

    print(f"OK: FAISS artifacts validated ({chunk_count} chunks, {manifest.get('embedding_model')})")
    print(f"OK: Sample retrieval queries passed (load={load_seconds:.2f}s)")
    return 0


def _print_errors(errors: list[str]) -> None:
    print("Phase 2 verification FAILED:")
    for error in errors:
        print(f"  - {error}")


if __name__ == "__main__":
    raise SystemExit(main())

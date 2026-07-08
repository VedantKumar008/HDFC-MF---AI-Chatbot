"""Load FAISS index and embedding model for retrieval."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pipeline.pipeline.builder import IndexBuildPipeline
from pipeline.pipeline.faiss_index import FaissRetriever

logger = logging.getLogger(__name__)


def load_knowledge_base(
    schemes_dir: Path,
    faiss_dir: Path,
    embedding_model: str,
) -> tuple[FaissRetriever, dict[str, Any]]:
    pipeline = IndexBuildPipeline(
        schemes_dir=schemes_dir,
        output_dir=faiss_dir,
        embedding_model_name=embedding_model,
    )
    retriever = pipeline.load_retriever()
    manifest = _read_manifest(faiss_dir)
    logger.info(
        "Loaded FAISS index with %s chunks (model=%s)",
        len(retriever.chunks),
        embedding_model,
    )
    return retriever, manifest


def _read_manifest(faiss_dir: Path) -> dict[str, Any]:
    manifest_path = faiss_dir / "manifest.json"
    if not manifest_path.exists():
        return {}

    with manifest_path.open(encoding="utf-8") as handle:
        return json.load(handle)

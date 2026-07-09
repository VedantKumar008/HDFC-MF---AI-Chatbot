"""Load knowledge base from FAISS or Pinecone for retrieval."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_knowledge_base(
    schemes_dir: Path,
    faiss_dir: Path,
    embedding_model: str,
    use_pinecone: bool = False,
    pinecone_api_key: str = "",
    pinecone_index_name: str = "",
    pinecone_environment: str = "",
) -> tuple:  # Deferred: (Retriever, dict[str, Any])
    """Load knowledge base from either FAISS or Pinecone."""
    
    if use_pinecone:
        return _load_pinecone_knowledge_base(
            pinecone_api_key=pinecone_api_key,
            pinecone_index_name=pinecone_index_name,
            pinecone_environment=pinecone_environment,
            embedding_model=embedding_model,
        )
    else:
        return _load_faiss_knowledge_base(
            schemes_dir=schemes_dir,
            faiss_dir=faiss_dir,
            embedding_model=embedding_model,
        )


def _load_faiss_knowledge_base(
    schemes_dir: Path,
    faiss_dir: Path,
    embedding_model: str,
) -> tuple:
    """Load FAISS-based knowledge base."""
    # Import heavy modules only when loading knowledge base
    from pipeline.pipeline.builder import IndexBuildPipeline
    from pipeline.pipeline.faiss_index import FaissRetriever
    
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


def _load_pinecone_knowledge_base(
    pinecone_api_key: str,
    pinecone_index_name: str,
    pinecone_environment: str,
    embedding_model: str,
) -> tuple:
    """Load Pinecone-based knowledge base."""
    from backend.app.services.pinecone_store import PineconeRetriever
    
    retriever = PineconeRetriever(
        api_key=pinecone_api_key,
        index_name=pinecone_index_name,
        environment=pinecone_environment,
        embedding_model=embedding_model,
    )
    
    if not retriever.initialize():
        raise RuntimeError("Failed to initialize Pinecone retriever")
    
    manifest = {
        "type": "pinecone",
        "index_name": pinecone_index_name,
        "environment": pinecone_environment,
        "embedding_model": embedding_model,
    }
    
    logger.info(
        "Loaded Pinecone index: %s (model=%s)",
        pinecone_index_name,
        embedding_model,
    )
    return retriever, manifest


def _read_manifest(faiss_dir: Path) -> dict[str, Any]:
    manifest_path = faiss_dir / "manifest.json"
    if not manifest_path.exists():
        return {}

    with manifest_path.open(encoding="utf-8") as handle:
        return json.load(handle)

"""Orchestrate chunking, embedding, and FAISS index creation."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from shared.schemes import APPROVED_SCHEME_COUNT

from .chunker import chunk_scheme_files
from .embedder import EmbeddingModel
from .faiss_index import FaissIndexBuilder, FaissRetriever
from .storage import IndexStorage

logger = logging.getLogger(__name__)


@dataclass
class BuildSummary:
    scheme_count: int
    chunk_count: int
    elapsed_seconds: float
    output_dir: Path
    embedding_model: str


class IndexBuildPipeline:
    def __init__(
        self,
        schemes_dir: Path,
        output_dir: Path,
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.schemes_dir = schemes_dir
        self.output_dir = output_dir
        self.embedding_model_name = embedding_model_name

    def build(self) -> BuildSummary:
        started = time.perf_counter()
        scheme_files = sorted(self.schemes_dir.glob("*.json"))
        if len(scheme_files) != APPROVED_SCHEME_COUNT:
            raise ValueError(
                f"Expected {APPROVED_SCHEME_COUNT} scheme JSON files in {self.schemes_dir}, "
                f"found {len(scheme_files)}."
            )

        logger.info("Chunking %s scheme files...", len(scheme_files))
        chunks = chunk_scheme_files(scheme_files)
        if not chunks:
            raise ValueError("No chunks generated from scheme JSON files.")

        logger.info("Generated %s chunks. Encoding with %s...", len(chunks), self.embedding_model_name)
        embedder = EmbeddingModel(self.embedding_model_name)
        builder = FaissIndexBuilder(embedder)
        index, _ = builder.build(chunks)

        storage = IndexStorage(self.output_dir)
        storage.save(
            index,
            chunks,
            embedding_model=self.embedding_model_name,
            embedding_dimension=embedder.dimension,
            scheme_count=len(scheme_files),
        )

        elapsed = time.perf_counter() - started
        logger.info("Index build completed in %.2fs", elapsed)
        return BuildSummary(
            scheme_count=len(scheme_files),
            chunk_count=len(chunks),
            elapsed_seconds=elapsed,
            output_dir=self.output_dir,
            embedding_model=self.embedding_model_name,
        )

    def load_retriever(self) -> FaissRetriever:
        storage = IndexStorage(self.output_dir)
        index, chunks, _manifest = storage.load()
        embedder = EmbeddingModel(self.embedding_model_name)
        return FaissRetriever(index, chunks, embedder)

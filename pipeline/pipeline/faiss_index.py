"""Build and query FAISS vector indexes."""

from __future__ import annotations

import faiss
import numpy as np

from .embedder import EmbeddingModel
from .models import ChunkRecord


class FaissIndexBuilder:
    def __init__(self, embedding_model: EmbeddingModel) -> None:
        self.embedding_model = embedding_model

    def build(self, chunks: list[ChunkRecord]) -> tuple[faiss.Index, np.ndarray]:
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts)
        if embeddings.shape[0] == 0:
            raise ValueError("Cannot build FAISS index without chunks.")

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        return index, embeddings

class FaissRetriever:
    def __init__(self, index: faiss.Index, chunks: list[ChunkRecord], embedding_model: EmbeddingModel) -> None:
        self.index = index
        self.chunks = chunks
        self.embedding_model = embedding_model

    def search(self, query: str, top_k: int = 5) -> list[tuple[ChunkRecord, float]]:
        query_vector = self.embedding_model.encode([query])
        scores, indices = self.index.search(query_vector, top_k)
        results: list[tuple[ChunkRecord, float]] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0:
                continue
            results.append((self.chunks[int(idx)], float(score)))
        return results

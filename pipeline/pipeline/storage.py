"""Persist and load FAISS index artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import faiss

from .models import ChunkRecord


class IndexStorage:
    INDEX_FILE = "index.faiss"
    CHUNKS_FILE = "chunks.json"
    MANIFEST_FILE = "manifest.json"

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def save(
        self,
        index: faiss.Index,
        chunks: list[ChunkRecord],
        *,
        embedding_model: str,
        embedding_dimension: int,
        scheme_count: int,
    ) -> dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        index_path = self.output_dir / self.INDEX_FILE
        chunks_path = self.output_dir / self.CHUNKS_FILE
        manifest_path = self.output_dir / self.MANIFEST_FILE

        temp_index = self.output_dir / f"{self.INDEX_FILE}.tmp"
        temp_chunks = self.output_dir / f"{self.CHUNKS_FILE}.tmp"
        temp_manifest = self.output_dir / f"{self.MANIFEST_FILE}.tmp"

        faiss.write_index(index, str(temp_index))

        chunks_payload = {"chunks": chunks}
        with temp_chunks.open("w", encoding="utf-8") as handle:
            json.dump(chunks_payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        manifest = {
            "built_at": datetime.now(UTC).isoformat(),
            "scheme_count": scheme_count,
            "chunk_count": len(chunks),
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension,
            "index_type": "IndexFlatIP",
            "similarity": "cosine",
            "artifacts": {
                "index": self.INDEX_FILE,
                "chunks": self.CHUNKS_FILE,
            },
        }
        with temp_manifest.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        temp_index.replace(index_path)
        temp_chunks.replace(chunks_path)
        temp_manifest.replace(manifest_path)

        return {
            "index": index_path,
            "chunks": chunks_path,
            "manifest": manifest_path,
        }

    def load(self) -> tuple[faiss.Index, list[ChunkRecord], dict[str, Any]]:
        index_path = self.output_dir / self.INDEX_FILE
        chunks_path = self.output_dir / self.CHUNKS_FILE
        manifest_path = self.output_dir / self.MANIFEST_FILE

        if not index_path.exists() or not chunks_path.exists() or not manifest_path.exists():
            raise FileNotFoundError("FAISS artifacts are missing. Run the index builder first.")

        index = faiss.read_index(str(index_path))
        with chunks_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        with manifest_path.open(encoding="utf-8") as handle:
            manifest = json.load(handle)

        chunks = payload.get("chunks") or []
        return index, chunks, manifest

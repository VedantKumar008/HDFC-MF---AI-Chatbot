"""Pinecone vector store adapter for RAG pipeline."""

from __future__ import annotations

import logging
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PineconeChunk:
    """Represents a text chunk with metadata."""
    text: str
    scheme_id: str
    scheme_name: str
    chunk_id: str
    score: float = 0.0


class PineconeRetriever:
    """Pinecone-based retriever compatible with existing RAG pipeline."""
    
    def __init__(
        self,
        api_key: str,
        index_name: str,
        environment: str,
        embedding_model: str,
    ):
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.embedding_model = embedding_model
        self._index = None
        self._chunks: list[PineconeChunk] = []
        
    def initialize(self):
        """Initialize Pinecone client and index."""
        try:
            from pinecone import Pinecone, ServerlessSpec
            
            pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            existing_indexes = [index.name for index in pc.list_indexes()]
            if self.index_name not in existing_indexes:
                logger.warning(f"Pinecone index '{self.index_name}' not found. Please create it first.")
                return False
            
            self._index = pc.Index(self.index_name)
            
            # Get index stats for logging
            stats = self._index.describe_index_stats()
            vector_count = stats.get('total_vector_count', 0)
            
            logger.info(f"✓ Pinecone connection successful")
            logger.info(f"✓ Index: {self.index_name}")
            logger.info(f"✓ Vectors loaded: {vector_count}")
            logger.info(f"✓ Retrieval source: Pinecone (cloud)")
            logger.info(f"✓ Embedding model: {self.embedding_model}")
            
            return True
            
        except Exception as exc:
            logger.exception("Failed to initialize Pinecone")
            return False
    
    def search(self, query: str, top_k: int = 5) -> list[PineconeChunk]:
        """Search for similar chunks in Pinecone."""
        if not self._index:
            logger.warning("Pinecone index not initialized")
            return []
        
        try:
            # Import embedding model only when needed
            from sentence_transformers import SentenceTransformer
            
            # Load embedding model
            model = SentenceTransformer(self.embedding_model)
            query_embedding = model.encode(query).tolist()
            
            # Search Pinecone
            results = self._index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=""
            )
            
            # Convert results to PineconeChunk objects
            chunks = []
            for match in results.matches:
                metadata = match.metadata or {}
                chunk = PineconeChunk(
                    text=metadata.get("text", ""),
                    scheme_id=metadata.get("scheme_id", ""),
                    scheme_name=metadata.get("scheme_name", ""),
                    chunk_id=match.id,
                    score=match.score or 0.0
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as exc:
            logger.exception("Pinecone search failed")
            return []
    
    @property
    def chunks(self) -> list[PineconeChunk]:
        """Return cached chunks for compatibility with existing pipeline."""
        return self._chunks

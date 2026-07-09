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
            
            # Log embedding provider info
            logger.info("[Embedding] Provider: HuggingFace Inference API")
            logger.info("[Embedding] Model: sentence-transformers/all-MiniLM-L6-v2")
            logger.info("[Embedding] Dimensions: 384")
            logger.info("[Embedding] Local model loading: DISABLED")
            
            return True
            
        except Exception as exc:
            logger.exception("Failed to initialize Pinecone")
            return False
    
    def search(self, query: str, top_k: int = 5) -> list[PineconeChunk]:
        """Search for similar chunks in Pinecone using HuggingFace Inference API."""
        if not self._index:
            logger.warning("Pinecone index not initialized")
            return []
        
        try:
            logger.info(f"[Pinecone] Starting search for query: '{query[:50]}...'")
            
            # Use HuggingFace Inference API for query embeddings (no local model loading)
            logger.info("[Pinecone] Requesting query embedding from HuggingFace")
            import requests
            import os
            
            hf_api_key = os.getenv("HF_API_KEY", "")
            if not hf_api_key:
                raise RuntimeError("HF_API_KEY environment variable not set. HuggingFace API key is required for embeddings.")
            
            # HuggingFace Inference API for all-MiniLM-L6-v2
            model_id = "sentence-transformers/all-MiniLM-L6-v2"
            api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"
            
            headers = {"Authorization": f"Bearer {hf_api_key}"}
            response = requests.post(api_url, headers=headers, json={"inputs": query})
            
            if response.status_code != 200:
                raise RuntimeError(f"HuggingFace API error: {response.status_code} - {response.text}")
            
            query_embedding = response.json()
            logger.info(f"[Pinecone] Query embedding received ({len(query_embedding)} dimensions)")
            
            # Search Pinecone
            logger.info("[Pinecone] Searching Pinecone index")
            results = self._index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=""
            )
            logger.info(f"[Pinecone] Pinecone returned {len(results.matches)} results")
            
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
            
            logger.info("[Pinecone] Retrieval complete")
            return chunks
            
        except Exception as exc:
            logger.exception("[Pinecone] Search failed")
            return []
    
    @property
    def chunks(self) -> list[PineconeChunk]:
        """Return cached chunks for compatibility with existing pipeline."""
        return self._chunks

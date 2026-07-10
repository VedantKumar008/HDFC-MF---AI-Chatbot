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
        """Search for similar chunks in Pinecone using HuggingFace Inference Client."""
        if not self._index:
            logger.warning("Pinecone index not initialized")
            return []
        
        try:
            logger.info(f"[Pinecone] Starting search for query: '{query[:50]}...'")
            
            # Use HuggingFace Inference Client for query embeddings (no local model loading)
            logger.info("[Pinecone] Requesting query embedding from HuggingFace")
            import os
            
            hf_api_key = os.getenv("HF_API_KEY", "")
            if not hf_api_key:
                raise RuntimeError("HF_API_KEY environment variable not set. HuggingFace API key is required for embeddings.")
            
            from huggingface_hub import InferenceClient
            
            client = InferenceClient(token=hf_api_key)
            model_id = "sentence-transformers/all-MiniLM-L6-v2"
            
            # Generate embedding using feature extraction
            query_embedding = client.feature_extraction(text=query, model=model_id)
            
            # Convert to list if needed
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            elif not isinstance(query_embedding, list):
                query_embedding = list(query_embedding)
            
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
            
            # Log raw results before filtering
            logger.info("[Pinecone] Raw Pinecone results (before filtering):")
            for i, match in enumerate(results.matches):
                score = match.score if match.score is not None else 0.0
                metadata = match.metadata or {}
                scheme_name = metadata.get("scheme_name", "Unknown")
                chunk_id = match.id
                logger.info(f"[Pinecone]   Result {i+1}: score={score:.4f}, scheme={scheme_name}, chunk_id={chunk_id}")
            
            # Convert results to PineconeChunk objects
            chunks = []
            for match in results.matches:
                metadata = match.metadata or {}
                chunk_text = metadata.get("text", "")
                chunk = PineconeChunk(
                    text=chunk_text,
                    scheme_id=metadata.get("scheme_id", ""),
                    scheme_name=metadata.get("scheme_name", ""),
                    chunk_id=match.id,
                    score=match.score or 0.0
                )
                chunks.append(chunk)
            
            # Log chunk content for verification
            logger.info("[Pinecone] Chunk content preview (first 1000 chars):")
            for i, chunk in enumerate(chunks):
                preview = chunk.text[:1000] if chunk.text else "[empty]"
                logger.info(f"[Pinecone]   Chunk {i+1} (scheme={chunk.scheme_name}):")
                logger.info(f"[Pinecone]   {preview}")
            
            logger.info("[Pinecone] Retrieval complete")
            return chunks
            
        except Exception as exc:
            logger.exception("[Pinecone] Search failed")
            return []
    
    @property
    def chunks(self) -> list[PineconeChunk]:
        """Return cached chunks for compatibility with existing pipeline."""
        return self._chunks

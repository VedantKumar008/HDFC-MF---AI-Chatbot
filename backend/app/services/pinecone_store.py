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
            logger.info(f"[Pinecone] Starting search for query: '{query[:50]}...'")
            
            # Try OpenAI embeddings first (no local model loading)
            logger.info("[Pinecone] Attempting OpenAI embeddings...")
            try:
                from openai import OpenAI
                import os
                
                openai_api_key = os.getenv("OPENAI_API_KEY", "")
                if openai_api_key:
                    logger.info("[Pinecone] Using OpenAI API for embeddings")
                    openai_client = OpenAI(api_key=openai_api_key)
                    
                    response = openai_client.embeddings.create(
                        input=query,
                        model="text-embedding-3-small"
                    )
                    query_embedding = response.data[0].embedding
                    logger.info(f"[Pinecone] OpenAI embedding generated (dimension: {len(query_embedding)})")
                else:
                    raise ValueError("OPENAI_API_KEY not set")
            except Exception as e:
                logger.warning(f"[Pinecone] OpenAI embeddings failed: {e}, falling back to local model")
                # Fallback to local sentence-transformers
                logger.info("[Pinecone] Loading sentence-transformers model for query embedding...")
                from sentence_transformers import SentenceTransformer
                
                model = SentenceTransformer(self.embedding_model)
                logger.info(f"[Pinecone] Local embedding model loaded: {self.embedding_model}")
                
                logger.info("[Pinecone] Generating query embedding...")
                query_embedding = model.encode(query).tolist()
                logger.info(f"[Pinecone] Local query embedding generated (dimension: {len(query_embedding)})")
            
            # Search Pinecone
            logger.info(f"[Pinecone] Querying Pinecone index with top_k={top_k}...")
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
            
            logger.info(f"[Pinecone] Search complete, returning {len(chunks)} chunks")
            return chunks
            
        except Exception as exc:
            logger.exception("[Pinecone] Search failed")
            return []
    
    @property
    def chunks(self) -> list[PineconeChunk]:
        """Return cached chunks for compatibility with existing pipeline."""
        return self._chunks

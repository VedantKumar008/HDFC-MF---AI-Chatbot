"""Upload HDFC scheme embeddings to Pinecone index."""

import json
import logging
import os
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in os.path.dirname(__file__):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_schemes(schemes_dir: Path) -> list[dict[str, Any]]:
    """Load all scheme JSON files."""
    schemes = []
    for json_file in schemes_dir.glob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
                schemes.append(data)
                logger.info(f"Loaded: {json_file.name}")
        except Exception as e:
            logger.error(f"Failed to load {json_file.name}: {e}")
    return schemes


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    words = text.split()
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def upload_to_pinecone(
    schemes_dir: Path,
    pinecone_api_key: str,
    index_name: str,
    embedding_model: str = "all-MiniLM-L6-v2",
):
    """Upload scheme embeddings to Pinecone."""
    
    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)
    
    # Check if index exists
    existing_indexes = [index.name for index in pc.list_indexes()]
    if index_name not in existing_indexes:
        logger.warning(f"Index '{index_name}' not found. Creating it...")
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        logger.info(f"Created index: {index_name}")
    
    index = pc.Index(index_name)
    
    # Load embedding model
    logger.info(f"Loading embedding model: {embedding_model}")
    model = SentenceTransformer(embedding_model)
    
    # Load schemes
    logger.info(f"Loading schemes from: {schemes_dir}")
    schemes = load_schemes(schemes_dir)
    logger.info(f"Loaded {len(schemes)} schemes")
    
    # Process and upload
    total_vectors = 0
    batch_size = 100
    vectors = []
    
    for scheme in schemes:
        scheme_id = scheme.get("id", "")
        scheme_name = scheme.get("name", "")
        description = scheme.get("description", "")
        key_features = scheme.get("key_features", "")
        
        # Combine text for embedding
        full_text = f"{scheme_name}\n{description}\n{key_features}"
        
        # Chunk the text
        chunks = chunk_text(full_text)
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = model.encode(chunk).tolist()
            
            # Create vector ID
            vector_id = f"{scheme_id}_chunk_{i}"
            
            # Create metadata
            metadata = {
                "text": chunk,
                "scheme_id": scheme_id,
                "scheme_name": scheme_name,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            vectors.append((vector_id, embedding, metadata))
            
            # Upload in batches
            if len(vectors) >= batch_size:
                index.upsert(vectors)
                total_vectors += len(vectors)
                logger.info(f"Uploaded {total_vectors} vectors...")
                vectors = []
    
    # Upload remaining vectors
    if vectors:
        index.upsert(vectors)
        total_vectors += len(vectors)
    
    logger.info(f"Upload complete! Total vectors: {total_vectors}")
    
    # Verify upload
    stats = index.describe_index_stats()
    logger.info(f"Index stats: {stats}")


if __name__ == "__main__":
    # Configuration
    schemes_dir = PROJECT_ROOT / "data" / "schemes"
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
    index_name = "hdfc-mf-index"
    
    if not pinecone_api_key:
        logger.error("PINECONE_API_KEY environment variable not set")
        exit(1)
    
    if not schemes_dir.exists():
        logger.error(f"Schemes directory not found: {schemes_dir}")
        exit(1)
    
    upload_to_pinecone(
        schemes_dir=schemes_dir,
        pinecone_api_key=pinecone_api_key,
        index_name=index_name,
    )

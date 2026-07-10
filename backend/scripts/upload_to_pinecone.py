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


def build_comprehensive_text(scheme: dict[str, Any]) -> str:
    """Build comprehensive text from all scheme fields for embedding."""
    text_parts = []
    
    # Basic info
    if scheme.get("scheme_name"):
        text_parts.append(f"Scheme Name: {scheme['scheme_name']}")
    if scheme.get("fund_name"):
        text_parts.append(f"Fund Name: {scheme['fund_name']}")
    if scheme.get("description"):
        text_parts.append(f"Description: {scheme['description']}")
    if scheme.get("fund_objective"):
        text_parts.append(f"Fund Objective: {scheme['fund_objective']}")
    
    # Financial metrics
    if scheme.get("nav"):
        text_parts.append(f"NAV: {scheme['nav']}")
    if scheme.get("nav_date"):
        text_parts.append(f"NAV Date: {scheme['nav_date']}")
    if scheme.get("aum"):
        text_parts.append(f"AUM: {scheme['aum']}")
    if scheme.get("expense_ratio"):
        text_parts.append(f"Expense Ratio: {scheme['expense_ratio']}")
    if scheme.get("exit_load"):
        text_parts.append(f"Exit Load: {scheme['exit_load']}")
    
    # Fund details
    if scheme.get("category"):
        text_parts.append(f"Category: {scheme['category']}")
    if scheme.get("sub_category"):
        text_parts.append(f"Sub Category: {scheme['sub_category']}")
    if scheme.get("risk_level"):
        text_parts.append(f"Risk Level: {scheme['risk_level']}")
    if scheme.get("fund_manager"):
        text_parts.append(f"Fund Manager: {scheme['fund_manager']}")
    if scheme.get("benchmark"):
        text_parts.append(f"Benchmark: {scheme['benchmark']}")
    
    # Investment terms
    investment_terms = scheme.get("investment_terms", {})
    if investment_terms.get("min_investment_amount"):
        text_parts.append(f"Minimum Investment: {investment_terms['min_investment_amount']}")
    if investment_terms.get("min_sip_investment"):
        text_parts.append(f"Minimum SIP: {investment_terms['min_sip_investment']}")
    if investment_terms.get("lock_in"):
        text_parts.append(f"Lock-in Period: {investment_terms['lock_in']}")
    
    # Holdings
    holdings = scheme.get("holdings", [])
    if holdings:
        text_parts.append("Top Holdings:")
        for holding in holdings[:10]:  # Top 10 holdings
            if holding.get("company_name"):
                text_parts.append(f"  - {holding['company_name']}: {holding.get('corpus_per', 'N/A')}%")
    
    # Asset allocation
    asset_allocation = scheme.get("asset_allocation", {})
    if asset_allocation.get("by_sector"):
        text_parts.append("Sector Allocation:")
        for sector in asset_allocation["by_sector"][:5]:
            text_parts.append(f"  - {sector['name']}: {sector['percentage']}%")
    
    # Historical returns
    historical_returns = scheme.get("historical_returns", {})
    if historical_returns.get("simple_return"):
        text_parts.append("Historical Returns:")
        for period, value in historical_returns["simple_return"].items():
            text_parts.append(f"  - {period}: {value}")
    
    # FAQ content
    faq_content = scheme.get("faq_content", [])
    if faq_content:
        text_parts.append("FAQ:")
        for faq in faq_content[:5]:
            if faq.get("question") and faq.get("answer"):
                text_parts.append(f"  Q: {faq['question']}")
                text_parts.append(f"  A: {faq['answer']}")
    
    # Additional text sections
    additional_text = scheme.get("additional_text", {})
    if additional_text.get("investment_objective"):
        text_parts.append(f"Investment Objective: {additional_text['investment_objective']}")
    if additional_text.get("about"):
        text_parts.append(f"About: {additional_text['about']}")
    
    return "\n\n".join(text_parts)


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
    
    # Log first scheme structure for verification
    if schemes:
        logger.info("=" * 80)
        logger.info("First scheme JSON structure for verification:")
        logger.info(f"Scheme ID: {schemes[0].get('id', 'N/A')}")
        logger.info(f"Scheme Name: {schemes[0].get('scheme_name', 'N/A')}")
        logger.info("JSON keys:")
        for key in sorted(schemes[0].keys()):
            value = schemes[0][key]
            value_preview = str(value)[:100] if value else "None"
            logger.info(f"  {key}: {value_preview}")
        logger.info("=" * 80)
    
    for scheme in schemes:
        scheme_id = scheme.get("id", "")
        scheme_name = scheme.get("scheme_name", "")
        
        # Build comprehensive text from all fields
        full_text = build_comprehensive_text(scheme)
        
        # Log text being embedded for first scheme
        if scheme_id == schemes[0].get("id"):
            logger.info("=" * 80)
            logger.info(f"Text being embedded for {scheme_name}:")
            logger.info(full_text[:2000])  # First 2000 chars
            logger.info(f"Total character count: {len(full_text)}")
            logger.info(f"Estimated token count: ~{len(full_text) // 4}")
            logger.info("=" * 80)
        
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
            
            # Log chunk details for first scheme
            if scheme_id == schemes[0].get("id") and i < 3:
                logger.info(f"Chunk {i+1} for {scheme_name}:")
                logger.info(f"  Character count: {len(chunk)}")
                logger.info(f"  Estimated tokens: ~{len(chunk) // 4}")
                logger.info(f"  Preview: {chunk[:200]}...")
                logger.info(f"  Metadata keys: {list(metadata.keys())}")
            
            vectors.append((vector_id, embedding, metadata))
            
            # Upload in batches
            if len(vectors) >= batch_size:
                index.upsert(vectors=vectors)
                total_vectors += len(vectors)
                logger.info(f"Uploaded {total_vectors} vectors...")
                vectors = []
    
    # Upload remaining vectors
    if vectors:
        index.upsert(vectors=vectors)
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

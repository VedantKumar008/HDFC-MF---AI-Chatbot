"""Streaming chat endpoint powered by RAG + Groq."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

# Defer heavy imports to reduce startup memory
# from backend.app.compliance.detector import ComplianceDetector
# from backend.app.rag.pipeline import RagPipeline
from backend.app.rag.prompts import NOT_FOUND_MESSAGE
from backend.app.schemas import ChatRequest

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


def _build_pipeline(request: Request):  # Deferred: RagPipeline
    state = request.app.state.app_state
    settings = request.app.state.settings

    if not state.ready:
        raise HTTPException(
            status_code=503,
            detail="Backend is not ready. Please retry shortly.",
        )
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured on the backend.",
        )

    # Check if RAG is disabled for memory-constrained environments
    if settings.disable_rag:
        logger.info("RAG disabled - using simple LLM mode")
        from backend.app.rag.groq_client import GroqChatClient
        return SimpleGroqPipeline(GroqChatClient(api_key=settings.groq_api_key, model=settings.groq_model))

    # Lazy load schemes on first request
    if not state.schemes:
        logger.info("Loading schemes on first request...")
        from backend.app.services.schemes import load_scheme_summaries
        
        state.schemes = load_scheme_summaries(settings.resolved_data_path)
        logger.info(f"Loaded {len(state.schemes)} schemes")

    # Lazy load retriever on first request
    if state.retriever is None:
        if settings.use_pinecone:
            logger.info("Loading Pinecone retriever on first request...")
            from backend.app.services.knowledge_base import load_knowledge_base
            
            retriever, manifest = load_knowledge_base(
                schemes_dir=settings.resolved_data_path,
                faiss_dir=settings.resolved_faiss_path,  # Not used when USE_PINECONE=true
                embedding_model=settings.embedding_model,
                use_pinecone=True,
                pinecone_api_key=settings.pinecone_api_key,
                pinecone_index_name=settings.pinecone_index_name,
                pinecone_environment=settings.pinecone_environment,
            )
        else:
            logger.info("Loading FAISS index and embedding model on first request...")
            from backend.app.services.knowledge_base import load_knowledge_base
            
            retriever, manifest = load_knowledge_base(
                schemes_dir=settings.resolved_data_path,
                faiss_dir=settings.resolved_faiss_path,
                embedding_model=settings.embedding_model,
                use_pinecone=False,
            )
        state.retriever = retriever
        state.index_manifest = manifest
        logger.info("Knowledge base loaded successfully")

    # Import heavy modules only when building pipeline
    from backend.app.rag.groq_client import GroqChatClient
    from backend.app.rag.pipeline import RagPipeline

    groq_client = GroqChatClient(api_key=settings.groq_api_key, model=settings.groq_model)
    return RagPipeline(
        retriever=state.retriever,
        schemes=state.schemes,
        groq_client=groq_client,
        top_k=settings.rag_top_k,
        min_score=settings.rag_min_score,
        min_top_score=settings.rag_min_top_score,
    )


class SimpleGroqPipeline:
    """Simple LLM-only pipeline for memory-constrained environments."""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
    
    def retrieve(self, query: str):
        """Mock retrieval for compatibility."""
        from backend.app.rag.pipeline import RetrievalResult
        return RetrievalResult(
            chunks=[],
            retrieval_seconds=0.0,
            has_context=False,
        )
    
    def stream_answer(self, query: str, retrieval=None, history=None):
        """Stream answer without RAG context."""
        from backend.app.rag.prompts import SYSTEM_PROMPT
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": query})
        
        if history:
            messages = [messages[0], *history, messages[-1]]
        
        yield from self.groq_client.stream_completion(messages)


async def _sse_stream(request: Request, payload: ChatRequest) -> AsyncIterator[str]:
    logger.info(f"[Chat] Starting SSE stream for session: {payload.session_id}")
    logger.info(f"[Chat] Message: '{payload.message[:50]}...'")
    
    state = request.app.state.app_state
    settings = request.app.state.settings
    
    logger.info("[Chat] Building pipeline...")
    pipeline = _build_pipeline(request)
    logger.info("[Chat] Pipeline built successfully")
    
    # Import compliance detector only when needed
    logger.info("[Chat] Loading compliance detector...")
    from backend.app.compliance.detector import ComplianceDetector
    compliance = ComplianceDetector()
    logger.info("[Chat] Compliance detector loaded")
    
    # Phase 6: Get or create session
    logger.info("[Chat] Getting or creating session...")
    session = state.session_store.get_or_create_session(payload.session_id)
    history_len = len(session.messages) if hasattr(session, 'messages') else 0
    logger.info(f"[Chat] Session ready, messages length: {history_len}")
    
    try:
        # Phase 5: Compliance check before retrieval
        logger.info("[Chat] Running compliance check on query...")
        query_result = compliance.check_query(payload.message)
        if query_result.action.value != "allow":
            logger.info(f"[Chat] Query blocked: {query_result.reason}")
            # Store user message even if blocked
            session.add_message("user", payload.message)
            yield _sse_event("blocked", {"reason": query_result.reason})
            yield _sse_event("token", {"content": query_result.message})
            # Store assistant response
            session.add_message("assistant", query_result.message)
            yield _sse_event("done", {"session_id": payload.session_id})
            return

        logger.info("[Chat] Query compliance check passed")

        # Skip retrieval if RAG is disabled
        if not settings.disable_rag:
            logger.info("[Chat] Starting retrieval...")
            retrieval = pipeline.retrieve(payload.message)
            chunks_len = len(retrieval.chunks) if hasattr(retrieval, 'chunks') else 0
            logger.info(f"[Chat] Retrieval complete: {chunks_len} chunks")
            
            yield _sse_event(
                "retrieval",
                {
                    "retrieval_seconds": round(retrieval.retrieval_seconds, 4) if hasattr(retrieval, 'retrieval_seconds') else 0,
                    "chunk_count": len(retrieval.chunks) if hasattr(retrieval, 'chunks') else 0,
                    "has_context": retrieval.has_context if hasattr(retrieval, 'has_context') else False,
                },
            )

            # Phase 5: Compliance check after retrieval (anti-hallucination)
            logger.info("[Chat] Running compliance check on retrieval...")
            has_context = retrieval.has_context if hasattr(retrieval, 'has_context') else False
            chunks_len = len(retrieval.chunks) if hasattr(retrieval, 'chunks') else 0
            retrieval_result = compliance.check_retrieval(has_context, chunks_len)
            if retrieval_result.action.value != "allow":
                logger.info(f"[Chat] Retrieval blocked: {retrieval_result.reason}")
                # Store user message
                session.add_message("user", payload.message)
                yield _sse_event("blocked", {"reason": retrieval_result.reason})
                yield _sse_event("token", {"content": retrieval_result.message})
                # Store assistant response
                session.add_message("assistant", retrieval_result.message)
                yield _sse_event("done", {"session_id": payload.session_id})
                return
        else:
            # Mock retrieval for simple mode
            logger.info("[Chat] RAG disabled, using mock retrieval")
            from backend.app.rag.pipeline import RetrievalResult
            retrieval = RetrievalResult(chunks=[], retrieval_seconds=0.0, has_context=False)

        logger.info("[Chat] Retrieval compliance check passed")

        # Phase 6: Get conversation history for context
        logger.info("[Chat] Retrieving conversation history...")
        history = session.get_recent_messages(limit=5) if hasattr(session, 'get_recent_messages') else []
        logger.info(f"[Chat] Retrieved {len(history)} history messages")
        
        # Store user message
        logger.info("[Chat] Storing user message...")
        session.add_message("user", payload.message)
        
        # Stream response with history
        logger.info("[Chat] Starting response stream...")
        full_response = ""
        token_count = 0
        for token in pipeline.stream_answer(payload.message, retrieval=retrieval, history=history):
            full_response += token
            token_count += 1
            yield _sse_event("token", {"content": token})
        
        logger.info(f"[Chat] Stream complete, yielded {token_count} tokens")
        
        # Store assistant response
        logger.info("[Chat] Storing assistant response...")
        session.add_message("assistant", full_response)

        logger.info("[Chat] SSE stream complete, returning done event to frontend")
        yield _sse_event("done", {"session_id": payload.session_id})
    except Exception as exc:
        logger.exception("Chat stream failed")
        yield _sse_event("error", {"message": str(exc)})


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(request: Request, payload: ChatRequest) -> StreamingResponse:
    logger.info(f"[Chat] Request received - session: {payload.session_id}, message: '{payload.message[:50]}...'")
    return StreamingResponse(
        _sse_stream(request, payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

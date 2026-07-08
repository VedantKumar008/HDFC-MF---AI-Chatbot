"""FastAPI lifespan hooks for startup/shutdown."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from backend.app.config import Settings
from backend.app.services.knowledge_base import load_knowledge_base
from backend.app.services.schemes import load_scheme_summaries
from backend.app.state import AppState

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    state: AppState = app.state.app_state
    started = time.perf_counter()

    logger.info("Starting backend startup sequence...")
    logger.info(f"Project root: {settings.resolved_data_path.parent.parent}")
    logger.info(f"Data path: {settings.resolved_data_path}")
    logger.info(f"Data path exists: {settings.resolved_data_path.exists()}")
    
    try:
        # Even more minimal startup - defer scheme loading too
        state.schemes = []
        state.retriever = None
        state.index_manifest = None
        state.embedding_model_name = settings.embedding_model
        state.ready = True
        state.load_error = None
        logger.info("Backend ready (schemes and FAISS index will load on first request)")
    except Exception as exc:
        state.ready = False
        state.load_error = str(exc)
        logger.exception("Backend startup failed")
        raise

    state.startup_seconds = round(time.perf_counter() - started, 2)
    logger.info("Backend startup completed in %.2fs", state.startup_seconds)
    yield
    logger.info("Backend shutdown")

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import get_settings
from backend.app.lifespan import lifespan
from backend.app.state import AppState

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()

app = FastAPI(
    title="HDFC MF AI Assistant API",
    description="Factual HDFC Mutual Fund information assistant API.",
    version="0.4.0",
    lifespan=lifespan,
)

app.state.settings = settings
app.state.app_state = AppState()

# Log CORS configuration for debugging (minimal logging to avoid memory issues)
cors_origins = settings.cors_origin_list
print(f"CORS Origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defer router imports to reduce startup memory
from backend.app.routers import health, schemes, chat

app.include_router(health.router)
app.include_router(schemes.router)
app.include_router(chat.router)

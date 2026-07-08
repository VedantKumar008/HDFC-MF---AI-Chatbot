from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# Hardcode the project root based on the actual workspace location
PROJECT_ROOT = Path(r"c:\HDFC  MF - AI Chatbot\hdfc-mf-ai-assistant")

# Force absolute paths at module level
DATA_PATH = (PROJECT_ROOT / "data" / "schemes").resolve()
FAISS_PATH = (PROJECT_ROOT / "data" / "faiss").resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / "backend" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    cors_origins: str = "http://localhost:3000"
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 5
    rag_min_score: float = 0.4
    rag_min_top_score: float = 0.45

    @property
    def data_path(self) -> Path:
        return DATA_PATH

    @property
    def faiss_path(self) -> Path:
        return FAISS_PATH

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def get_settings() -> Settings:
    return Settings()

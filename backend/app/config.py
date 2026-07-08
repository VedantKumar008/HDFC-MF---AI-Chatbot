from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / "backend" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    cors_origins: str = "http://localhost:3000"
    data_path: Path = PROJECT_ROOT / "data" / "schemes"
    faiss_path: Path = PROJECT_ROOT / "data" / "faiss"
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 5
    rag_min_score: float = 0.4
    rag_min_top_score: float = 0.45

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

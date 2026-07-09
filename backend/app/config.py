from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root - works in both development and production
# In production (Render), the repo is cloned to /opt/render/project/src
# In development, it's the local workspace
if os.getenv("RENDER"):
    # Production: Render deployment
    PROJECT_ROOT = Path("/opt/render/project/src")
else:
    # Development: local workspace
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


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
    rag_top_k: int = 3  # Reduce from 5 to save memory
    rag_min_score: float = 0.4
    rag_min_top_score: float = 0.45
    disable_rag: bool = False  # Disable RAG for memory-constrained environments

    # Allow environment variables to override paths
    data_path: Path | None = None
    faiss_path: Path | None = None

    @property
    def resolved_data_path(self) -> Path:
        if self.data_path:
            return Path(self.data_path).resolve()
        return (PROJECT_ROOT / "data" / "schemes").resolve()

    @property
    def resolved_faiss_path(self) -> Path:
        if self.faiss_path:
            return Path(self.faiss_path).resolve()
        return (PROJECT_ROOT / "data" / "faiss").resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def get_settings() -> Settings:
    return Settings()

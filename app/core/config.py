"""Application configuration — reads all settings from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────
    app_name: str = "Ticket Triage System"
    app_env: str = "development"
    debug: bool = False

    # ── API Security ─────────────────────────────────────────
    api_key: str = Field(..., description="X-API-Key header value required on all endpoints")

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(
        ...,
        description="Async PostgreSQL URL (postgresql+asyncpg://...)",
    )
    sync_database_url: str = Field(
        ...,
        description="Sync PostgreSQL URL for Alembic migrations (postgresql://...)",
    )

    # ── Google Gemini ─────────────────────────────────────────
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # ── LLM Tuning ───────────────────────────────────────────
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    llm_retry_attempts: int = 2

    # ── RAG ──────────────────────────────────────────────────
    rag_top_k: int = 5

    # ── Pagination ───────────────────────────────────────────
    default_page_size: int = 20
    max_page_size: int = 100

    # ── Ticket Validation ────────────────────────────────────
    ticket_subject_max_len: int = 200
    ticket_description_max_len: int = 5000


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()

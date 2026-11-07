"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration for Citefolio backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field("", alias="DATABASE_URL")

    groq_api_key: str = Field("", alias="GROQ_API_KEY")
    cerebras_api_key: str = Field("", alias="CEREBRAS_API_KEY")
    groq_model: str = Field("openai/gpt-oss-120b", alias="GROQ_MODEL")
    cerebras_model: str = Field("gpt-oss-120b", alias="CEREBRAS_MODEL")
    groq_base_url: str = Field(
        "https://api.groq.com/openai/v1",
        alias="GROQ_BASE_URL",
    )
    cerebras_base_url: str = Field(
        "https://api.cerebras.ai/v1",
        alias="CEREBRAS_BASE_URL",
    )

    voyage_api_key: str = Field("", alias="VOYAGE_API_KEY")
    voyage_model: str = Field("voyage-4", alias="VOYAGE_MODEL")
    cohere_api_key: str = Field("", alias="COHERE_API_KEY")
    cohere_rerank_model: str = Field("rerank-v3.5", alias="COHERE_RERANK_MODEL")

    chunk_size: int = Field(512, alias="CHUNK_SIZE")
    chunk_overlap_ratio: float = Field(0.15, alias="CHUNK_OVERLAP_RATIO")

    max_file_size_mb: int = Field(4, alias="MAX_FILE_SIZE_MB")
    session_ttl_hours: int = Field(2, alias="SESSION_TTL_HOURS")
    confidence_threshold: float = Field(0.25, alias="CONFIDENCE_THRESHOLD")
    cache_similarity_threshold: float = Field(
        0.95,
        alias="CACHE_SIMILARITY_THRESHOLD",
    )

    cron_secret: str = Field("change_me", alias="CRON_SECRET")
    cors_origins: str = Field("http://localhost:3000", alias="CORS_ORIGINS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    embedding_dimensions: int = 1024
    retrieval_top_k: int = 20
    rerank_top_n: int = 5
    rrf_k: int = 60
    embed_batch_size: int = 32
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.0

    @field_validator("chunk_overlap_ratio")
    @classmethod
    def validate_overlap(cls, value: float) -> float:
        if not 0.0 <= value < 1.0:
            raise ValueError("CHUNK_OVERLAP_RATIO must be in [0, 1)")
        return value

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def chunk_overlap_tokens(self) -> int:
        return max(1, int(self.chunk_size * self.chunk_overlap_ratio))


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()  # type: ignore[call-arg]

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
        populate_by_name=True,
    )

    # Env names match field names uppercased by pydantic-settings.
    database_url: str = ""

    groq_api_key: str = ""
    cerebras_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    cerebras_model: str = "gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    cerebras_base_url: str = "https://api.cerebras.ai/v1"

    voyage_api_key: str = ""
    voyage_model: str = "voyage-4"
    mistral_api_key: str = ""
    mistral_embed_model: str = "mistral-embed"
    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-v3.5"

    chunk_size: int = 512
    chunk_overlap_ratio: float = 0.15

    max_file_size_mb: int = 4
    session_ttl_hours: int = 2
    confidence_threshold: float = 0.25
    cache_similarity_threshold: float = 0.95

    cron_secret: str = "change_me"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

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

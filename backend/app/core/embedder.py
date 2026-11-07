"""Voyage embedding client with batching and L2 normalization."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import voyageai

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

_embedder: Optional["DocumentEmbedder"] = None


class DocumentEmbedder:
    """Singleton Voyage embedder (1024-d)."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.voyage_api_key:
            raise RuntimeError("VOYAGE_API_KEY is not configured")
        self._client = voyageai.Client(api_key=settings.voyage_api_key)
        self._model = settings.voyage_model
        self._batch_size = settings.embed_batch_size
        self._dimensions = settings.embedding_dimensions

    def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        """Embed document chunks with document input_type."""
        return self._embed_many(chunks, input_type="document")

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query with query input_type."""
        vectors = self._embed_many([query], input_type="query")
        return vectors[0]

    def _embed_many(self, texts: list[str], input_type: str) -> list[list[float]]:
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            result = self._client.embed(
                texts=batch,
                model=self._model,
                input_type=input_type,
                output_dimension=self._dimensions,
            )
            for embedding in result.embeddings:
                vectors.append(self._l2_normalize(embedding))
        logger.debug("Embedded %s texts as %s", len(texts), input_type)
        return vectors

    @staticmethod
    def _l2_normalize(vector: list[float]) -> list[float]:
        arr = np.asarray(vector, dtype=np.float32)
        norm = float(np.linalg.norm(arr))
        if norm == 0.0:
            return arr.tolist()
        return (arr / norm).tolist()


def get_embedder() -> DocumentEmbedder:
    """Return process-wide embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = DocumentEmbedder()
    return _embedder

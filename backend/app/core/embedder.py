"""Embedding client: Voyage preferred, Mistral fallback (both 1024-d)."""

from __future__ import annotations

import logging
from typing import Optional

import httpx
import numpy as np

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

_embedder: Optional["DocumentEmbedder"] = None


class DocumentEmbedder:
    """Singleton embedder producing L2-normalized 1024-d vectors."""

    def __init__(self) -> None:
        settings = get_settings()
        self._batch_size = settings.embed_batch_size
        self._dimensions = settings.embedding_dimensions
        self._provider = "voyage" if settings.voyage_api_key else "mistral"
        if self._provider == "voyage":
            import voyageai

            self._voyage = voyageai.Client(api_key=settings.voyage_api_key)
            self._model = settings.voyage_model
        else:
            if not settings.mistral_api_key:
                raise RuntimeError(
                    "Set VOYAGE_API_KEY or MISTRAL_API_KEY for embeddings"
                )
            self._mistral_key = settings.mistral_api_key
            self._model = settings.mistral_embed_model
        logger.info("Embedder provider=%s model=%s", self._provider, self._model)

    def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        return self._embed_many(chunks, input_type="document")

    def embed_query(self, query: str) -> list[float]:
        return self._embed_many([query], input_type="query")[0]

    def _embed_many(self, texts: list[str], input_type: str) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            if self._provider == "voyage":
                vectors.extend(self._voyage_batch(batch, input_type))
            else:
                vectors.extend(self._mistral_batch(batch))
        return vectors

    def _voyage_batch(self, batch: list[str], input_type: str) -> list[list[float]]:
        result = self._voyage.embed(
            texts=batch,
            model=self._model,
            input_type=input_type,
            output_dimension=self._dimensions,
        )
        return [self._l2_normalize(e) for e in result.embeddings]

    def _mistral_batch(self, batch: list[str]) -> list[list[float]]:
        response = httpx.post(
            "https://api.mistral.ai/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self._mistral_key}",
                "Content-Type": "application/json",
            },
            json={"model": self._model, "input": batch},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()["data"]
        ordered = sorted(data, key=lambda row: row["index"])
        return [self._l2_normalize(row["embedding"]) for row in ordered]

    @staticmethod
    def _l2_normalize(vector: list[float]) -> list[float]:
        arr = np.asarray(vector, dtype=np.float32)
        norm = float(np.linalg.norm(arr))
        if norm == 0.0:
            return arr.tolist()
        return (arr / norm).tolist()


def get_embedder() -> DocumentEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = DocumentEmbedder()
    return _embedder

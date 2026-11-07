"""Background RAGAs evaluation helpers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Compute faithfulness / relevancy scores asynchronously."""

    async def evaluate_response(
        self,
        query: str,
        context_chunks: list[str],
        response: str,
    ) -> dict[str, float]:
        """Run ragas metrics without blocking the request path."""
        return await asyncio.to_thread(
            self._evaluate_sync,
            query,
            context_chunks,
            response,
        )

    def _evaluate_sync(
        self,
        query: str,
        context_chunks: list[str],
        response: str,
    ) -> dict[str, float]:
        try:
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import answer_relevancy, context_precision, faithfulness

            dataset = Dataset.from_dict(
                {
                    "question": [query],
                    "answer": [response],
                    "contexts": [context_chunks],
                }
            )
            result = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_precision],
            )
            row: dict[str, Any] = result.to_pandas().iloc[0].to_dict()
            return {
                "faithfulness": float(row.get("faithfulness") or 0.0),
                "answer_relevancy": float(row.get("answer_relevancy") or 0.0),
                "context_precision": float(row.get("context_precision") or 0.0),
            }
        except Exception:
            logger.exception("RAGAs evaluation failed")
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
            }

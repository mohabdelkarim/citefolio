"""Input, retrieval, and output safety checks."""

from __future__ import annotations

import re
from typing import Any

from app.utils.config import get_settings

INJECTION_PATTERNS = [
    "ignore previous",
    "ignore all",
    "system:",
    "you are now",
    "forget your instructions",
    "act as",
    "jailbreak",
    "dan",
]

TOKEN_RE = re.compile(r"[A-Za-zΑ-Ωα-ω]{2,}")
NUMBERISH_RE = re.compile(
    r"\b(\d{1,4}([./-]\d{1,2}){1,2}|\d{3,}|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
)


class InputGuardrail:
    """Reject empty, oversized, or injection-like queries."""

    def check(self, query: str) -> tuple[bool, str]:
        text = (query or "").strip()
        if len(text) < 3:
            return False, "Query too short"
        if len(text) > 1000:
            return False, "Query too long"
        lowered = text.lower()
        for pattern in INJECTION_PATTERNS:
            if pattern in lowered:
                return False, "Query blocked by safety filter"
        if not TOKEN_RE.search(text):
            return False, "Query must contain words"
        return True, ""


class RetrievalGuardrail:
    """Block generation when nothing retrieved is relevant enough."""

    def check(self, chunks: list[dict[str, Any]]) -> tuple[bool, float]:
        if not chunks:
            return False, 0.0
        # Prefer semantic cosine similarity; RRF ranks are much smaller (~0.01).
        similarities = [float(c.get("similarity", 0.0)) for c in chunks]
        max_score = max(similarities) if similarities else 0.0
        threshold = get_settings().confidence_threshold
        if max_score > 0:
            return max_score >= threshold, max_score
        rrf_scores = [float(c.get("rrf_score", c.get("score", 0.0))) for c in chunks]
        max_rrf = max(rrf_scores) if rrf_scores else 0.0
        return max_rrf > 0, max_rrf


class OutputGuardrail:
    """Lightweight faithfulness heuristic against context."""

    def check(self, response: str, context_chunks: list[str]) -> bool:
        if not response.strip():
            return False
        context = "\n".join(context_chunks).lower()
        suspects = NUMBERISH_RE.findall(response)
        # findall with groups can return tuples; normalize
        flat: list[str] = []
        for item in suspects:
            if isinstance(item, tuple):
                flat.append(item[0])
            else:
                flat.append(item)
        novel = [s for s in flat if s.lower() not in context and len(s) > 2]
        # Allow a few novel tokens; fail only when many appear unsupported
        return len(novel) <= 3

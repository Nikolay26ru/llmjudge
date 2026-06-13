"""Deterministic mock provider.

This makes the whole library testable offline with zero API keys and zero cost.
It returns a well-formed judge JSON payload derived deterministically from the
input, so tests are reproducible. It can also emit arbitrary raw text, which is
how the parser's robustness is exercised.
"""

from __future__ import annotations

import hashlib
import json

from llmjudge.providers.base import BaseProvider
from llmjudge.types import ProviderResponse


class MockProvider(BaseProvider):
    """A fake model that emits valid, deterministic judge JSON.

    Args:
        fixed_score: If set, always return this score. Otherwise the score is a
            stable function of the prompt hash (reproducible but arbitrary).
        confidence: Confidence value to embed in the payload.
        text: If set, ``complete`` returns this exact raw text instead of a
            generated payload — useful for exercising the parser with messy
            or malformed output.
        model: Model identifier reported on the response.

    Attributes:
        prompts: Every prompt passed to ``complete`` (handy for assertions in
            tests about caching, consensus, and call counts).
    """

    name = "mock"

    def __init__(
        self,
        *,
        fixed_score: float | None = None,
        confidence: float = 0.9,
        text: str | None = None,
        model: str = "mock-1",
    ) -> None:
        self.fixed_score = fixed_score
        self.confidence = confidence
        self.text = text
        self.model = model
        self.prompts: list[str] = []

    def _score_for(self, prompt: str) -> float:
        if self.fixed_score is not None:
            return self.fixed_score
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return (int(digest[:8], 16) % 1001) / 1000.0

    def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        """Return a deterministic judge payload (or the canned ``text``)."""
        self.prompts.append(prompt)
        if self.text is not None:
            raw = self.text
        else:
            score = round(self._score_for(prompt), 3)
            payload = {
                "score": score,
                "confidence": self.confidence,
                "reason": "Deterministic mock verdict.",
                "evidence": [],
                "violations": [] if score >= 0.5 else ["mock_violation"],
            }
            raw = json.dumps(payload)
        return ProviderResponse(
            text=raw,
            model=self.model,
            input_tokens=len(prompt.split()),
            output_tokens=16,
            latency_ms=0.0,
            cost_usd=0.0,
            finish_reason="stop",
            metadata={"provider": self.name},
        )

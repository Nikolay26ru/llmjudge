"""Core data types for llmjudge.

These are intentionally small, fully typed, and dependency-free so that any
downstream project can import them without pulling in heavy transitive deps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, SupportsFloat


@dataclass(frozen=True)
class ProviderResponse:
    """Raw output returned by a Provider for a single completion call.

    Attributes:
        text: The model's textual completion.
        model: Concrete model identifier that produced the text, if known.
        input_tokens: Prompt token count, if reported by the provider.
        output_tokens: Completion token count, if reported by the provider.
        latency_ms: Wall-clock latency of the call in milliseconds, if measured.
        cost_usd: Estimated cost of the call in USD, if computable.
        finish_reason: Why generation stopped (``"stop"``, ``"length"``, ...).
        metadata: Free-form provider-specific extras.
    """

    text: str
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float | None = None
    cost_usd: float | None = None
    finish_reason: str | None = None
    # hash=False: a dict is unhashable, so excluding it keeps the frozen
    # dataclass hashable (all other fields are). Equality still includes it.
    metadata: dict[str, Any] = field(default_factory=dict, hash=False)


@dataclass(frozen=True)
class JudgeResult:
    """The verdict produced by a Judge for a single (prompt, response) pair.

    A ``JudgeResult`` behaves like its score in numeric and ordering contexts,
    so you can write ``assert judge.score(...) > 0.8`` directly.

    Attributes:
        score: Normalized score in ``[0.0, 1.0]`` (1.0 = best).
        confidence: Judge's self-reported confidence in ``[0.0, 1.0]``.
        reason: Short natural-language justification.
        evidence: Quoted spans / facts supporting the verdict.
        violations: Named rubric criteria that were violated.
        rubric: Name of the rubric used.
        raw: Raw provider text (for debugging / auditing).
        metadata: Free-form extra data (model name, votes, token usage, ...).
    """

    score: float
    confidence: float = 1.0
    reason: str = ""
    evidence: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    rubric: str = ""
    raw: str = ""
    # hash=False: a dict is unhashable, so excluding it keeps the frozen
    # dataclass hashable (all other fields are). Equality still includes it.
    metadata: dict[str, Any] = field(default_factory=dict, hash=False)

    def passed(self, threshold: float = 0.5) -> bool:
        """Return whether the score meets ``threshold`` (default 0.5)."""
        return self.score >= threshold

    def __float__(self) -> float:
        return float(self.score)

    # Ordering dunders so comparisons like ``result > 0.8`` work. Python's
    # rich-comparison operators dispatch to these and never fall back to
    # ``__float__``, so they must be defined explicitly. ``__eq__`` is left to
    # the dataclass: it is value-equality between results (so ``result == 0.9``
    # is False — a result never equals a bare float), not score-comparison.
    def __lt__(self, other: SupportsFloat) -> bool:
        return self.score < float(other)

    def __le__(self, other: SupportsFloat) -> bool:
        return self.score <= float(other)

    def __gt__(self, other: SupportsFloat) -> bool:
        return self.score > float(other)

    def __ge__(self, other: SupportsFloat) -> bool:
        return self.score >= float(other)

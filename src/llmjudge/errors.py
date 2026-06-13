"""Typed exception hierarchy for llmjudge.

Every error raised by the library derives from :class:`LLMJudgeError`, so
downstream code can catch the whole family with a single ``except`` while still
being able to discriminate specific failure modes.
"""

from __future__ import annotations


class LLMJudgeError(Exception):
    """Base class for all llmjudge errors."""


class ConfigurationError(LLMJudgeError):
    """Raised when a Judge / provider / rubric is misconfigured.

    Examples: an unknown provider scheme, a rubric requiring context that was
    not supplied, or an optional provider extra that is not installed.
    """


class ParseError(LLMJudgeError):
    """Raised when a model's output cannot be parsed into a verdict.

    The offending raw text is preserved on :attr:`raw` for debugging.
    """

    def __init__(self, message: str, *, raw: str = "") -> None:
        super().__init__(message)
        self.raw = raw


class ProviderError(LLMJudgeError):
    """Raised when an underlying provider call fails (network, API, etc.)."""


class RubricError(LLMJudgeError):
    """Raised when a rubric is unknown or invalid."""

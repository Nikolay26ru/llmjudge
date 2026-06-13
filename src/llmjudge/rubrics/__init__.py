"""Rubrics package: the :class:`Rubric` type, registry, and built-ins.

Importing this package registers the built-in rubrics as a side effect.
"""

from __future__ import annotations

from llmjudge.rubrics import builtin  # noqa: F401  (registers built-in rubrics)
from llmjudge.rubrics.base import (
    Rubric,
    available_rubrics,
    get_rubric,
    register_rubric,
)
from llmjudge.rubrics.builtin import (
    FACTUALITY,
    GROUNDEDNESS,
    INSTRUCTION_FOLLOWING,
    RELEVANCE,
    SAFETY,
)

__all__ = [
    "FACTUALITY",
    "GROUNDEDNESS",
    "INSTRUCTION_FOLLOWING",
    "RELEVANCE",
    "SAFETY",
    "Rubric",
    "available_rubrics",
    "get_rubric",
    "register_rubric",
]

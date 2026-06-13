"""LLMJudge — provider-agnostic, reproducible, typed LLM-as-a-judge.

The public API is intentionally tiny so downstream projects can depend on it
without surprises. The headline primitive is :class:`Judge`::

    from llmjudge import Judge

    judge = Judge(provider="mock", rubric="factuality")
    result = judge.score("What is the capital of France?", "Paris.")
    assert result > 0.0          # JudgeResult compares like its score

See ``README.md`` for a runnable example.
"""

from __future__ import annotations

from llmjudge.errors import (
    ConfigurationError,
    LLMJudgeError,
    ParseError,
    ProviderError,
    RubricError,
)
from llmjudge.judge import Judge
from llmjudge.parsing import extract_json
from llmjudge.providers import (
    BaseProvider,
    MockProvider,
    Provider,
    available_providers,
    make_provider,
    register_provider,
)
from llmjudge.rubrics import (
    Rubric,
    available_rubrics,
    get_rubric,
    register_rubric,
)
from llmjudge.types import JudgeResult, ProviderResponse

__version__ = "0.1.0"

__all__ = [
    "BaseProvider",
    "ConfigurationError",
    "Judge",
    "JudgeResult",
    "LLMJudgeError",
    "MockProvider",
    "ParseError",
    "Provider",
    "ProviderError",
    "ProviderResponse",
    "Rubric",
    "RubricError",
    "__version__",
    "available_providers",
    "available_rubrics",
    "extract_json",
    "get_rubric",
    "make_provider",
    "register_provider",
    "register_rubric",
]

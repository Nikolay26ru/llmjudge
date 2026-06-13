"""LLMJudge Kit — provider-agnostic, reproducible, typed LLM-as-a-judge.

The public API is intentionally tiny so downstream projects can depend on it
without surprises. The headline primitive is :class:`Judge`::

    from llm_judge_kit import Judge

    judge = Judge(provider="mock", rubric="factuality")
    result = judge.score("What is the capital of France?", "Paris.")
    assert result > 0.0          # JudgeResult compares like its score

See ``README.md`` for a runnable example.
"""

from __future__ import annotations

from llm_judge_kit._logging import enable_debug_logging, get_logger
from llm_judge_kit._version import __version__
from llm_judge_kit.benchmark import CaseResult, Report, run_benchmark
from llm_judge_kit.caching import CachingProvider
from llm_judge_kit.consensus import ConsensusJudge
from llm_judge_kit.dataset import Case, load_dataset
from llm_judge_kit.errors import (
    ConfigurationError,
    DatasetError,
    LLMJudgeError,
    ParseError,
    ProviderError,
    RubricError,
)
from llm_judge_kit.judge import Judge
from llm_judge_kit.parsing import extract_json
from llm_judge_kit.providers import (
    AnthropicProvider,
    BaseProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
    Provider,
    available_providers,
    make_provider,
    register_provider,
)
from llm_judge_kit.reliability import RetryProvider
from llm_judge_kit.reporting import (
    load_report,
    render_html,
    render_json,
    render_markdown,
)
from llm_judge_kit.rubrics import (
    Rubric,
    available_rubrics,
    get_rubric,
    register_rubric,
)
from llm_judge_kit.types import JudgeResult, ProviderResponse

__all__ = [
    "AnthropicProvider",
    "BaseProvider",
    "CachingProvider",
    "Case",
    "CaseResult",
    "ConfigurationError",
    "ConsensusJudge",
    "DatasetError",
    "Judge",
    "JudgeResult",
    "LLMJudgeError",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "ParseError",
    "Provider",
    "ProviderError",
    "ProviderResponse",
    "Report",
    "RetryProvider",
    "Rubric",
    "RubricError",
    "__version__",
    "available_providers",
    "available_rubrics",
    "enable_debug_logging",
    "extract_json",
    "get_logger",
    "get_rubric",
    "load_dataset",
    "load_report",
    "make_provider",
    "register_provider",
    "register_rubric",
    "render_html",
    "render_json",
    "render_markdown",
    "run_benchmark",
]

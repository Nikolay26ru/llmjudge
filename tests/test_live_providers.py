"""Live provider tests — opt-in only.

These make real network calls and cost money/tokens, so they are SKIPPED unless
``LLMJUDGE_LIVE_TESTS=1``. Each test also skips if its provider's credentials or
endpoint are unavailable. Never run in CI or in the 24/7 loop.
"""

from __future__ import annotations

import os

import pytest

from llmjudge import Judge

_LIVE = os.environ.get("LLMJUDGE_LIVE_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not _LIVE, reason="set LLMJUDGE_LIVE_TESTS=1 to run live provider tests"
)


def _check_unit_range(judge: Judge) -> None:
    result = judge.score(
        prompt="What is the capital of France?",
        response="The capital of France is Paris.",
    )
    assert 0.0 <= result.score <= 1.0
    assert result.raw


def test_openai_live() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    _check_unit_range(Judge(provider="openai:gpt-4o-mini", rubric="factuality"))


def test_anthropic_live() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    _check_unit_range(Judge(provider="anthropic:claude-haiku-4-5", rubric="factuality"))


def test_ollama_live() -> None:
    model = os.environ.get("LLMJUDGE_OLLAMA_MODEL", "llama3")
    _check_unit_range(Judge(provider=f"ollama:{model}", rubric="factuality"))

"""The public surface must stay importable and the docstring example must run."""

from __future__ import annotations

import llmjudge


def test_all_names_are_importable() -> None:
    for name in llmjudge.__all__:
        assert hasattr(llmjudge, name), f"{name} missing from llmjudge"


def test_version_is_sane() -> None:
    assert isinstance(llmjudge.__version__, str)
    assert llmjudge.__version__.count(".") >= 2


def test_headline_snippet_runs() -> None:
    # Mirrors the README / package docstring above-the-fold example.
    from llmjudge import Judge, MockProvider

    judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="factuality")
    result = judge.score("What is the capital of France?", "Paris.")
    assert result > 0.8
    assert result.passed()

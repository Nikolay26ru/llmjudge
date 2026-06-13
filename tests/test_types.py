"""Tests for the core data types — especially the numeric/ordering behavior."""

from __future__ import annotations

import dataclasses

import pytest

from llmjudge.types import JudgeResult, ProviderResponse


def test_float_returns_score() -> None:
    assert float(JudgeResult(score=0.42)) == pytest.approx(0.42)


def test_passed_default_and_custom_threshold() -> None:
    assert JudgeResult(score=0.5).passed() is True
    assert JudgeResult(score=0.49).passed() is False
    assert JudgeResult(score=0.7).passed(0.8) is False
    assert JudgeResult(score=0.9).passed(0.8) is True


def test_literal_comparison_against_float() -> None:
    # The headline ergonomic: this must work without float(...) wrapping.
    result = JudgeResult(score=0.9)
    assert result > 0.8
    assert result >= 0.9
    assert result < 1.0
    assert result <= 0.9
    assert not (result > 0.95)


def test_comparison_between_results() -> None:
    low = JudgeResult(score=0.3)
    high = JudgeResult(score=0.8)
    assert high > low
    assert low < high
    assert low <= JudgeResult(score=0.3)


def test_comparison_with_int() -> None:
    assert JudgeResult(score=0.5) > 0
    assert JudgeResult(score=0.5) < 1


def test_equality_is_value_based() -> None:
    a = JudgeResult(score=0.5, reason="x")
    b = JudgeResult(score=0.5, reason="x")
    assert a == b
    assert a != JudgeResult(score=0.5, reason="y")


def test_result_is_frozen() -> None:
    result = JudgeResult(score=0.5)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.score = 0.6  # type: ignore[misc]


def test_defaults() -> None:
    result = JudgeResult(score=1.0)
    assert result.confidence == 1.0
    assert result.evidence == ()
    assert result.violations == ()
    assert result.rubric == ""
    assert result.raw == ""
    assert result.metadata == {}


def test_provider_response_defaults() -> None:
    resp = ProviderResponse(text="hello")
    assert resp.text == "hello"
    assert resp.model is None
    assert resp.input_tokens is None
    assert resp.metadata == {}

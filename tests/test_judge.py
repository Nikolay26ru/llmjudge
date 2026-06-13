"""Tests for the Judge — the wedge primitive — all offline on MockProvider."""

from __future__ import annotations

import pytest

from llmjudge import Judge, MockProvider
from llmjudge.errors import ConfigurationError, ParseError
from llmjudge.rubrics.base import Rubric
from llmjudge.types import ProviderResponse


class _Recorder:
    """Captures the judging prompt and provider kwargs; returns a fixed verdict."""

    name = "recorder"

    def __init__(self, text: str = '{"score": 0.6}') -> None:
        self.text = text
        self.last_prompt: str | None = None
        self.last_kwargs: dict[str, object] = {}

    def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        return ProviderResponse(text=self.text, model="rec-model")


def test_score_from_string_specs() -> None:
    judge = Judge(provider="mock", rubric="factuality")
    result = judge.score("What is 2+2?", "4")
    assert 0.0 <= result.score <= 1.0
    assert result.rubric == "factuality"
    assert result.raw  # raw provider text retained


def test_score_with_instances() -> None:
    rubric = Rubric(name="inst_test", description="x")
    judge = Judge(provider=MockProvider(fixed_score=0.9), rubric=rubric)
    result = judge.score("p", "r")
    assert result.score == 0.9
    assert result.rubric == "inst_test"


def test_call_alias_matches_score() -> None:
    judge = Judge(provider=MockProvider(fixed_score=0.7), rubric="relevance")
    assert judge("p", "r").score == judge.score("p", "r").score


def test_passed_uses_threshold() -> None:
    judge = Judge(provider=MockProvider(fixed_score=0.6), rubric="relevance", threshold=0.5)
    assert judge.passed("p", "r") is True
    strict = Judge(provider=MockProvider(fixed_score=0.6), rubric="relevance", threshold=0.8)
    assert strict.passed("p", "r") is False


def test_metadata_records_provider_and_usage() -> None:
    judge = Judge(provider=MockProvider(fixed_score=0.5), rubric="relevance")
    meta = judge.score("hello there", "hi").metadata
    assert meta["provider"] == "mock"
    assert meta["model"] == "mock-1"
    # input_tokens reflects the full rendered judging prompt, not just the input.
    assert isinstance(meta["input_tokens"], int)
    assert meta["input_tokens"] > 0
    assert meta["cost_usd"] == 0.0
    assert set(meta) == {
        "provider",
        "model",
        "input_tokens",
        "output_tokens",
        "latency_ms",
        "cost_usd",
    }


def test_provider_without_name_falls_back_to_class_name() -> None:
    class NoName:
        def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
            return ProviderResponse(text='{"score": 0.5}')

    judge = Judge(provider=NoName(), rubric="relevance")
    assert judge.score("p", "r").metadata["provider"] == "NoName"


def test_invalid_provider_raises() -> None:
    class Bad:
        pass

    with pytest.raises(ConfigurationError, match="complete"):
        Judge(provider=Bad(), rubric="relevance")  # type: ignore[arg-type]


def test_groundedness_requires_context() -> None:
    judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="groundedness")
    with pytest.raises(ConfigurationError, match="requires context"):
        judge.score("p", "r")


def test_groundedness_with_context_works() -> None:
    judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="groundedness")
    result = judge.score("p", "r", context="the source material")
    assert result.score == 0.9


def test_parse_error_propagates() -> None:
    judge = Judge(provider=MockProvider(text="no json here"), rubric="relevance")
    with pytest.raises(ParseError):
        judge.score("p", "r")


def test_score_is_clamped_to_unit_interval() -> None:
    high = Judge(provider=MockProvider(text='{"score": 1.5}'), rubric="relevance")
    assert high.score("p", "r").score == 1.0
    low = Judge(provider=MockProvider(text='{"score": -0.3}'), rubric="relevance")
    assert low.score("p", "r").score == 0.0


def test_missing_score_raises_parse_error() -> None:
    judge = Judge(provider=MockProvider(text='{"confidence": 0.5}'), rubric="relevance")
    with pytest.raises(ParseError, match="numeric 'score'"):
        judge.score("p", "r")


def test_boolean_score_rejected() -> None:
    judge = Judge(provider=MockProvider(text='{"score": true}'), rubric="relevance")
    with pytest.raises(ParseError):
        judge.score("p", "r")


def test_string_score_rejected() -> None:
    judge = Judge(provider=MockProvider(text='{"score": "0.5"}'), rubric="relevance")
    with pytest.raises(ParseError):
        judge.score("p", "r")


@pytest.mark.parametrize(
    "raw",
    ['{"score": NaN}', '{"score": Infinity}', '{"score": -Infinity}'],
)
def test_non_finite_score_is_rejected(raw: str) -> None:
    # json accepts NaN/Infinity; a non-finite "score" must NOT silently become
    # a perfect 1.0 (or 0.0) and sail through a `> 0.8` gate.
    judge = Judge(provider=MockProvider(text=raw), rubric="relevance")
    with pytest.raises(ParseError, match="finite numeric"):
        judge.score("p", "r")


def test_non_finite_confidence_falls_back_to_default() -> None:
    judge = Judge(
        provider=MockProvider(text='{"score": 0.5, "confidence": NaN}'),
        rubric="relevance",
    )
    assert judge.score("p", "r").confidence == 1.0


def test_confidence_defaults_when_missing() -> None:
    judge = Judge(provider=MockProvider(text='{"score": 0.5}'), rubric="relevance")
    assert judge.score("p", "r").confidence == 1.0


def test_confidence_defaults_when_non_numeric() -> None:
    judge = Judge(
        provider=MockProvider(text='{"score": 0.5, "confidence": "high"}'), rubric="relevance"
    )
    assert judge.score("p", "r").confidence == 1.0


def test_confidence_is_clamped() -> None:
    judge = Judge(
        provider=MockProvider(text='{"score": 0.5, "confidence": 2.0}'), rubric="relevance"
    )
    assert judge.score("p", "r").confidence == 1.0


def test_reason_none_becomes_empty_string() -> None:
    judge = Judge(provider=MockProvider(text='{"score": 0.5, "reason": null}'), rubric="relevance")
    assert judge.score("p", "r").reason == ""


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"score": 0.5, "evidence": ["a", "b"]}', ("a", "b")),
        ('{"score": 0.5, "evidence": "just one"}', ("just one",)),
        ('{"score": 0.5, "evidence": ""}', ()),
        ('{"score": 0.5, "evidence": null}', ()),
        ('{"score": 0.5, "evidence": 42}', ("42",)),
        ('{"score": 0.5, "evidence": ["a", null, "b"]}', ("a", "b")),
        ('{"score": 0.5}', ()),
    ],
)
def test_evidence_coercion(raw: str, expected: tuple[str, ...]) -> None:
    judge = Judge(provider=MockProvider(text=raw), rubric="relevance")
    assert judge.score("p", "r").evidence == expected


def test_violations_coercion() -> None:
    judge = Judge(
        provider=MockProvider(text='{"score": 0.2, "violations": ["a", "b"]}'),
        rubric="relevance",
    )
    assert judge.score("p", "r").violations == ("a", "b")


def test_provider_kwargs_are_forwarded() -> None:
    recorder = _Recorder()
    judge = Judge(provider=recorder, rubric="relevance")
    judge.score("the-prompt", "the-response", temperature=0.0, top_p=1)
    assert recorder.last_kwargs == {"temperature": 0.0, "top_p": 1}


def test_rendered_prompt_includes_inputs() -> None:
    recorder = _Recorder()
    judge = Judge(provider=recorder, rubric="relevance")
    judge.score("UNIQUE_PROMPT", "UNIQUE_RESPONSE")
    assert recorder.last_prompt is not None
    assert "UNIQUE_PROMPT" in recorder.last_prompt
    assert "UNIQUE_RESPONSE" in recorder.last_prompt

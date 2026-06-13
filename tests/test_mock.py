"""Tests for the deterministic MockProvider."""

from __future__ import annotations

import json

from llmjudge.parsing import extract_json
from llmjudge.providers.mock import MockProvider


def test_deterministic_for_same_prompt() -> None:
    provider = MockProvider()
    a = provider.complete("hello world")
    b = MockProvider().complete("hello world")
    assert a.text == b.text


def test_different_prompts_differ() -> None:
    provider = MockProvider()
    assert provider.complete("abc").text != provider.complete("xyz").text


def test_hash_based_score_in_unit_range() -> None:
    payload = extract_json(MockProvider().complete("anything").text)
    assert 0.0 <= payload["score"] <= 1.0


def test_fixed_score() -> None:
    payload = extract_json(MockProvider(fixed_score=0.83).complete("q").text)
    assert payload["score"] == 0.83
    assert payload["confidence"] == 0.9


def test_low_fixed_score_reports_violation() -> None:
    payload = extract_json(MockProvider(fixed_score=0.1).complete("q").text)
    assert payload["violations"] == ["mock_violation"]


def test_high_fixed_score_no_violation() -> None:
    payload = extract_json(MockProvider(fixed_score=0.9).complete("q").text)
    assert payload["violations"] == []


def test_canned_text_mode_passes_through() -> None:
    provider = MockProvider(text="not json at all")
    assert provider.complete("q").text == "not json at all"


def test_custom_confidence_and_model() -> None:
    provider = MockProvider(fixed_score=0.5, confidence=0.25, model="mock-x")
    resp = provider.complete("q")
    assert resp.model == "mock-x"
    assert json.loads(resp.text)["confidence"] == 0.25


def test_records_prompts() -> None:
    provider = MockProvider()
    provider.complete("first")
    provider.complete("second")
    assert provider.prompts == ["first", "second"]


def test_response_carries_usage_fields() -> None:
    resp = MockProvider().complete("two words")
    assert resp.input_tokens == 2
    assert resp.finish_reason == "stop"
    assert resp.cost_usd == 0.0

"""Offline tests for the real providers.

No network: each provider is driven through an injected fake client, and the
SDK-construction paths are exercised with dummy keys (client construction makes
no network call). Live API calls live in test_live_providers.py.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

import pytest

from llmjudge import (
    AnthropicProvider,
    Judge,
    OllamaProvider,
    OpenAIProvider,
)
from llmjudge.errors import ProviderError
from llmjudge.providers.registry import available_providers, make_provider

# --- fake clients ---------------------------------------------------------


def _openai_client(text: str = '{"score": 0.5}', capture: dict[str, Any] | None = None) -> Any:
    def create(**kwargs: Any) -> Any:
        if capture is not None:
            capture.update(kwargs)
        return SimpleNamespace(
            model="gpt-x",
            choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def _anthropic_client(text: str = '{"score": 0.5}', capture: dict[str, Any] | None = None) -> Any:
    def create(**kwargs: Any) -> Any:
        if capture is not None:
            capture.update(kwargs)
        return SimpleNamespace(
            model="claude-x",
            content=[
                SimpleNamespace(type="thinking", thinking="ignore me"),
                SimpleNamespace(type="text", text=text),
            ],
            usage=SimpleNamespace(input_tokens=12, output_tokens=8),
            stop_reason="end_turn",
        )

    return SimpleNamespace(messages=SimpleNamespace(create=create))


def _ollama_client(
    data: dict[str, Any] | None = None,
    capture: dict[str, Any] | None = None,
    fail: bool = False,
) -> Any:
    body = data or {
        "response": '{"score": 0.5}',
        "model": "llama3",
        "done": True,
        "prompt_eval_count": 13,
        "eval_count": 9,
    }

    def post(url: str, json: Any = None, timeout: Any = None) -> Any:
        if capture is not None:
            capture.update({"url": url, "json": json, "timeout": timeout})

        def raise_for_status() -> None:
            if fail:
                raise RuntimeError("HTTP 500")

        return SimpleNamespace(raise_for_status=raise_for_status, json=lambda: body)

    return SimpleNamespace(post=post)


# --- registration ---------------------------------------------------------


def test_all_schemes_registered() -> None:
    for scheme in ("openai", "anthropic", "ollama", "mock"):
        assert scheme in available_providers()


# --- OpenAI ----------------------------------------------------------------


def test_openai_complete_maps_response() -> None:
    provider = OpenAIProvider(client=_openai_client(text='{"score": 0.9}'))
    result = Judge(provider=provider, rubric="relevance").score("p", "r")
    assert result.score == 0.9
    assert result.metadata["provider"] == "openai"
    assert result.metadata["model"] == "gpt-x"
    assert result.metadata["input_tokens"] == 11
    assert result.metadata["output_tokens"] == 7


def test_openai_request_shape_and_kwargs() -> None:
    capture: dict[str, Any] = {}
    provider = OpenAIProvider(client=_openai_client(capture=capture))
    provider.complete("hello", max_tokens=42, temperature=0)
    assert capture["model"] == "gpt-4o-mini"
    assert capture["max_tokens"] == 42
    assert capture["temperature"] == 0
    assert capture["messages"] == [{"role": "user", "content": "hello"}]


def test_openai_errors_become_provider_error() -> None:
    def boom(**kwargs: Any) -> Any:
        raise RuntimeError("down")

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom)))
    with pytest.raises(ProviderError, match="OpenAI request failed"):
        OpenAIProvider(client=client).complete("p")


def test_openai_construction_via_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert make_provider("openai:gpt-5").model == "gpt-5"  # type: ignore[attr-defined]
    assert make_provider("openai").model == "gpt-4o-mini"  # type: ignore[attr-defined]


def test_openai_missing_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(ProviderError, match="llmjudge\\[openai\\]"):
        OpenAIProvider()


# --- Anthropic -------------------------------------------------------------


def test_anthropic_joins_only_text_blocks() -> None:
    provider = AnthropicProvider(client=_anthropic_client(text='{"score": 0.7}'))
    result = Judge(provider=provider, rubric="relevance").score("p", "r")
    assert result.score == 0.7
    assert result.metadata["provider"] == "anthropic"
    assert result.metadata["model"] == "claude-x"
    assert result.metadata["input_tokens"] == 12
    assert result.metadata["output_tokens"] == 8
    assert "ignore me" not in result.raw  # thinking block excluded


def test_anthropic_request_shape() -> None:
    capture: dict[str, Any] = {}
    provider = AnthropicProvider(client=_anthropic_client(capture=capture))
    provider.complete("hello", max_tokens=64)
    assert capture["model"] == "claude-opus-4-8"
    assert capture["max_tokens"] == 64
    assert capture["messages"] == [{"role": "user", "content": "hello"}]
    assert "temperature" not in capture  # never sent by default


def test_anthropic_errors_become_provider_error() -> None:
    def boom(**kwargs: Any) -> Any:
        raise RuntimeError("down")

    client = SimpleNamespace(messages=SimpleNamespace(create=boom))
    with pytest.raises(ProviderError, match="Anthropic request failed"):
        AnthropicProvider(client=client).complete("p")


def test_anthropic_construction_via_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert make_provider("anthropic:claude-x").model == "claude-x"  # type: ignore[attr-defined]
    assert make_provider("anthropic").model == "claude-opus-4-8"  # type: ignore[attr-defined]


def test_anthropic_missing_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with pytest.raises(ProviderError, match="llmjudge\\[anthropic\\]"):
        AnthropicProvider()


# --- Ollama ----------------------------------------------------------------


def test_ollama_complete_maps_response() -> None:
    provider = OllamaProvider(client=_ollama_client())
    result = Judge(provider=provider, rubric="relevance").score("p", "r")
    assert result.score == 0.5
    assert result.metadata["provider"] == "ollama"
    assert result.metadata["model"] == "llama3"
    assert result.metadata["input_tokens"] == 13
    assert result.metadata["output_tokens"] == 9


def test_ollama_request_shape() -> None:
    capture: dict[str, Any] = {}
    provider = OllamaProvider(client=_ollama_client(capture=capture), host="http://h:1234/")
    provider.complete("hello")
    assert capture["url"] == "http://h:1234/api/generate"
    assert capture["json"]["model"] == "llama3"
    assert capture["json"]["prompt"] == "hello"
    assert capture["json"]["stream"] is False


def test_ollama_errors_become_provider_error() -> None:
    with pytest.raises(ProviderError, match="Ollama request failed"):
        OllamaProvider(client=_ollama_client(fail=True)).complete("p")


def test_ollama_construction_preserves_multi_colon_model() -> None:
    provider = make_provider("ollama:llama3:8b")
    assert provider.model == "llama3:8b"  # type: ignore[attr-defined]
    assert make_provider("ollama").model == "llama3"  # type: ignore[attr-defined]


def test_ollama_missing_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "httpx", None)
    with pytest.raises(ProviderError, match="llmjudge\\[ollama\\]"):
        OllamaProvider()

"""OpenAI-compatible provider (Chat Completions).

Works with the official OpenAI API and any OpenAI-compatible endpoint via
``base_url`` (vLLM, Together, Groq, LM Studio, Ollama's OpenAI shim, ...).
The ``openai`` SDK is imported lazily so the core stays dependency-free; install
it with ``pip install 'llmjudge[openai]'``.
"""

from __future__ import annotations

from typing import Any

from llmjudge.errors import ProviderError
from llmjudge.providers.base import BaseProvider
from llmjudge.types import ProviderResponse

_DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(BaseProvider):
    """Calls an OpenAI-compatible Chat Completions endpoint.

    Args:
        model: Model id (defaults to ``gpt-4o-mini``).
        api_key: API key; falls back to the SDK's env resolution if omitted.
        base_url: Override for OpenAI-compatible servers.
        max_tokens: Default completion cap (overridable per call).
        client: Inject a pre-built client (mainly for tests); skips SDK import.
        **default_kwargs: Extra args merged into every ``create`` call.
    """

    name = "openai"

    def __init__(
        self,
        model: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int = 1024,
        client: Any = None,
        **default_kwargs: Any,
    ) -> None:
        self.model = model or _DEFAULT_MODEL
        self.max_tokens = max_tokens
        self._default_kwargs = default_kwargs
        if client is None:
            try:
                import openai
            except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
                raise ProviderError(
                    "The 'openai' provider needs the openai package: "
                    "pip install 'llmjudge[openai]'."
                ) from exc
            client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._client: Any = client

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        """Return a completion for ``prompt`` from the chat endpoint."""
        merged = {**self._default_kwargs, **kwargs}
        max_tokens = merged.pop("max_tokens", self.max_tokens)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                **merged,
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
        choice = response.choices[0]
        text = getattr(getattr(choice, "message", None), "content", None) or ""
        usage = getattr(response, "usage", None)
        return ProviderResponse(
            text=text,
            model=getattr(response, "model", self.model),
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            finish_reason=getattr(choice, "finish_reason", None),
            metadata={"provider": self.name},
        )

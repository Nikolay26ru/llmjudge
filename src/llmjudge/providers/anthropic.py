"""Anthropic (Claude) provider via the Messages API.

The ``anthropic`` SDK is imported lazily so the core stays dependency-free;
install it with ``pip install 'llmjudge[anthropic]'``.

Note: we deliberately do not send ``temperature`` (recent Claude models reject
sampling params). ``max_tokens`` is required by the Messages API and defaults to
a value large enough for a judge verdict.
"""

from __future__ import annotations

from typing import Any

from llmjudge.errors import ProviderError
from llmjudge.providers.base import BaseProvider
from llmjudge.types import ProviderResponse

_DEFAULT_MODEL = "claude-opus-4-8"


class AnthropicProvider(BaseProvider):
    """Calls Anthropic's Messages API.

    Args:
        model: Model id (defaults to ``claude-opus-4-8``).
        api_key: API key; falls back to the SDK's env resolution if omitted.
        max_tokens: Required by the Messages API; default suits a JSON verdict.
        client: Inject a pre-built client (mainly for tests); skips SDK import.
        **default_kwargs: Extra args merged into every ``messages.create`` call.
    """

    name = "anthropic"

    def __init__(
        self,
        model: str | None = None,
        *,
        api_key: str | None = None,
        max_tokens: int = 1024,
        client: Any = None,
        **default_kwargs: Any,
    ) -> None:
        self.model = model or _DEFAULT_MODEL
        self.max_tokens = max_tokens
        self._default_kwargs = default_kwargs
        if client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
                raise ProviderError(
                    "The 'anthropic' provider needs the anthropic package: "
                    "pip install 'llmjudge[anthropic]'."
                ) from exc
            client = anthropic.Anthropic(api_key=api_key)
        self._client: Any = client

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        """Return a completion for ``prompt`` from the Messages API."""
        merged = {**self._default_kwargs, **kwargs}
        max_tokens = merged.pop("max_tokens", self.max_tokens)
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                **merged,
            )
        except Exception as exc:
            raise ProviderError(f"Anthropic request failed: {exc}") from exc
        text = "".join(
            getattr(block, "text", "")
            for block in getattr(response, "content", [])
            if getattr(block, "type", None) == "text"
        )
        usage = getattr(response, "usage", None)
        return ProviderResponse(
            text=text,
            model=getattr(response, "model", self.model),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            finish_reason=getattr(response, "stop_reason", None),
            metadata={"provider": self.name},
        )

"""Ollama provider (local models over plain HTTP).

Talks to a local Ollama server's ``/api/generate`` endpoint using ``httpx`` —
no vendor SDK. Install the extra with ``pip install 'llmjudge[ollama]'``.
"""

from __future__ import annotations

from typing import Any

from llmjudge.errors import ProviderError
from llmjudge.providers.base import BaseProvider
from llmjudge.types import ProviderResponse

_DEFAULT_MODEL = "llama3"
_DEFAULT_HOST = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    """Calls a local Ollama server.

    Args:
        model: Model name pulled in Ollama (defaults to ``llama3``).
        host: Base URL of the Ollama server.
        timeout: Per-request timeout in seconds.
        client: Inject an HTTP client exposing ``post`` (mainly for tests);
            skips the ``httpx`` import.
        **default_kwargs: Extra fields merged into the request body (e.g.
            ``options={"temperature": 0}``).
    """

    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        *,
        host: str = _DEFAULT_HOST,
        timeout: float = 120.0,
        client: Any = None,
        **default_kwargs: Any,
    ) -> None:
        self.model = model or _DEFAULT_MODEL
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._default_kwargs = default_kwargs
        if client is None:
            try:
                import httpx
            except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
                raise ProviderError(
                    "The 'ollama' provider needs httpx: pip install 'llmjudge[ollama]'."
                ) from exc
            client = httpx
        self._client: Any = client

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        """Return a completion for ``prompt`` from Ollama's generate endpoint."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **self._default_kwargs,
            **kwargs,
        }
        try:
            response = self._client.post(
                f"{self.host}/api/generate", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc
        return ProviderResponse(
            text=data.get("response", ""),
            model=data.get("model", self.model),
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            finish_reason="stop" if data.get("done") else None,
            metadata={"provider": self.name},
        )

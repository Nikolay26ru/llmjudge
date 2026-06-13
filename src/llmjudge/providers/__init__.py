"""Provider backends and the provider registry.

The deterministic :class:`MockProvider` is registered eagerly (it has no
dependencies). Real providers are registered lazily so importing ``llmjudge``
never imports a heavy SDK or requires an optional extra to be installed; the
SDK import happens only when that scheme is actually resolved and a client is
built.
"""

from __future__ import annotations

from llmjudge.providers.anthropic import AnthropicProvider
from llmjudge.providers.base import BaseProvider, Provider
from llmjudge.providers.mock import MockProvider
from llmjudge.providers.ollama import OllamaProvider
from llmjudge.providers.openai import OpenAIProvider
from llmjudge.providers.registry import (
    ProviderFactory,
    available_providers,
    make_provider,
    register_provider,
)

register_provider("mock", lambda model: MockProvider())
register_provider("openai", lambda model: OpenAIProvider(model))
register_provider("anthropic", lambda model: AnthropicProvider(model))
register_provider("ollama", lambda model: OllamaProvider(model))

__all__ = [
    "AnthropicProvider",
    "BaseProvider",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "Provider",
    "ProviderFactory",
    "available_providers",
    "make_provider",
    "register_provider",
]

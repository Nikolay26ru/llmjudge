"""Provider backends and the provider registry.

The deterministic :class:`MockProvider` is registered eagerly (it has no
dependencies). Real providers are registered lazily so importing ``llmjudge``
never imports a heavy SDK or requires an optional extra to be installed; the
SDK import happens only when that scheme is actually resolved.
"""

from __future__ import annotations

from llmjudge.providers.base import BaseProvider, Provider
from llmjudge.providers.mock import MockProvider
from llmjudge.providers.registry import (
    ProviderFactory,
    available_providers,
    make_provider,
    register_provider,
)

register_provider("mock", lambda model: MockProvider())

__all__ = [
    "BaseProvider",
    "MockProvider",
    "Provider",
    "ProviderFactory",
    "available_providers",
    "make_provider",
    "register_provider",
]

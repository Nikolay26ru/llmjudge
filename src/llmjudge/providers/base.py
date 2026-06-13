"""Provider abstraction.

A Provider is the only place that talks to an actual model. Everything else in
llmjudge is provider-agnostic. To add a backend, implement ``complete()`` (and
optionally subclass :class:`BaseProvider` for a stable ``name`` attribute).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from llmjudge.types import ProviderResponse


@runtime_checkable
class Provider(Protocol):
    """Minimal interface every model backend must implement."""

    name: str

    def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        """Return a single completion for ``prompt``."""
        ...


class BaseProvider:
    """Optional convenience base class with a stable ``name`` attribute."""

    name: str = "base"

    def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        """Return a single completion for ``prompt`` (must be overridden)."""
        raise NotImplementedError

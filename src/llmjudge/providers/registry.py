"""Provider registry: map a string scheme to a Provider factory.

This is the extension point that lets ``Judge(provider="openai:gpt-5")`` work
without the core importing any provider SDK. Register a new backend with
:func:`register_provider`; resolve a spec with :func:`make_provider`.
"""

from __future__ import annotations

from collections.abc import Callable

from llmjudge.errors import ConfigurationError
from llmjudge.providers.base import Provider

# A factory receives the model name (the part after ``scheme:``) or ``None``.
ProviderFactory = Callable[[str | None], Provider]

_REGISTRY: dict[str, ProviderFactory] = {}


def register_provider(scheme: str, factory: ProviderFactory, *, overwrite: bool = False) -> None:
    """Register ``factory`` under ``scheme`` (e.g. ``"openai"``).

    Args:
        scheme: The prefix used in a provider spec, before the first ``:``.
        factory: Callable taking an optional model name and returning a Provider.
        overwrite: Allow replacing an already-registered scheme.

    Raises:
        ConfigurationError: If ``scheme`` is already registered and
            ``overwrite`` is False.
    """
    if not scheme:
        raise ConfigurationError("Provider scheme must be a non-empty string.")
    if scheme in _REGISTRY and not overwrite:
        raise ConfigurationError(
            f"Provider scheme {scheme!r} is already registered; pass overwrite=True to replace it."
        )
    _REGISTRY[scheme] = factory


def available_providers() -> list[str]:
    """Return the registered provider schemes, sorted."""
    return sorted(_REGISTRY)


def make_provider(spec: str) -> Provider:
    """Build a Provider from a ``"scheme:model"`` spec.

    The model part may itself contain colons (e.g. ``"ollama:llama3:8b"``);
    only the first colon separates scheme from model.

    Raises:
        ConfigurationError: If the scheme is unknown.
    """
    scheme, sep, model = spec.partition(":")
    scheme = scheme.strip()
    model_name = model.strip() if sep else None
    if not model_name:
        model_name = None
    factory = _REGISTRY.get(scheme)
    if factory is None:
        raise ConfigurationError(
            f"Unknown provider scheme {scheme!r}. "
            f"Registered schemes: {available_providers() or '[none]'}."
        )
    return factory(model_name)

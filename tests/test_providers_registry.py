"""Tests for the provider registry and spec parsing."""

from __future__ import annotations

import pytest

from llmjudge.errors import ConfigurationError
from llmjudge.providers.base import BaseProvider
from llmjudge.providers.registry import (
    available_providers,
    make_provider,
    register_provider,
)
from llmjudge.types import ProviderResponse


class _Recorder(BaseProvider):
    name = "recorder"

    def __init__(self, model: str | None) -> None:
        self.model_arg = model

    def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        return ProviderResponse(text="{}", model=self.model_arg)


def test_mock_scheme_is_registered() -> None:
    assert "mock" in available_providers()
    assert make_provider("mock").name == "mock"


def test_register_and_make_with_model() -> None:
    register_provider("rec_test", lambda model: _Recorder(model))
    provider = make_provider("rec_test:some-model")
    assert isinstance(provider, _Recorder)
    assert provider.model_arg == "some-model"


def test_multi_colon_model_is_preserved() -> None:
    register_provider("rec2_test", lambda model: _Recorder(model))
    provider = make_provider("rec2_test:llama3:8b")
    assert isinstance(provider, _Recorder)
    assert provider.model_arg == "llama3:8b"


def test_spec_without_model_passes_none() -> None:
    register_provider("rec3_test", lambda model: _Recorder(model))
    provider = make_provider("rec3_test")
    assert isinstance(provider, _Recorder)
    assert provider.model_arg is None


def test_empty_model_after_colon_is_none() -> None:
    register_provider("rec4_test", lambda model: _Recorder(model))
    provider = make_provider("rec4_test:")
    assert isinstance(provider, _Recorder)
    assert provider.model_arg is None


def test_unknown_scheme_raises() -> None:
    with pytest.raises(ConfigurationError, match="Unknown provider scheme"):
        make_provider("nope_scheme:x")


def test_register_duplicate_without_overwrite_raises() -> None:
    register_provider("dupp_test", lambda model: _Recorder(model))
    with pytest.raises(ConfigurationError, match="already registered"):
        register_provider("dupp_test", lambda model: _Recorder(model))


def test_register_overwrite_replaces() -> None:
    register_provider("oww_test", lambda model: _Recorder("first"))
    register_provider("oww_test", lambda model: _Recorder("second"), overwrite=True)
    provider = make_provider("oww_test")
    assert isinstance(provider, _Recorder)
    assert provider.model_arg == "second"


def test_empty_scheme_raises() -> None:
    with pytest.raises(ConfigurationError, match="non-empty"):
        register_provider("", lambda model: _Recorder(model))

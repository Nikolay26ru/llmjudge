"""The :class:`Judge` — the wedge primitive.

A ``Judge`` pairs a provider with a rubric and turns a (prompt, response) pair
into a typed :class:`~llmjudge.types.JudgeResult`. Providers and rubrics are
resolved from strings via their registries, so:

    >>> from llmjudge import Judge
    >>> judge = Judge(provider="mock", rubric="factuality")
    >>> isinstance(float(judge.score("2+2?", "4")), float)
    True

Swapping in a real backend is just a different spec, e.g.
``Judge(provider="openai:gpt-5", rubric="factuality")``.
"""

from __future__ import annotations

from typing import Any

from llmjudge.errors import ConfigurationError, ParseError
from llmjudge.parsing import extract_json
from llmjudge.providers.base import Provider
from llmjudge.providers.registry import make_provider
from llmjudge.rubrics.base import Rubric, get_rubric
from llmjudge.types import JudgeResult, ProviderResponse


class Judge:
    """Scores a model response against a rubric using a judge model.

    Args:
        provider: A provider spec string (``"scheme:model"``, e.g. ``"mock"`` or
            ``"openai:gpt-5"``) or any object with a ``complete()`` method.
        rubric: A registered rubric name (e.g. ``"factuality"``) or a
            :class:`~llmjudge.rubrics.base.Rubric` instance.
        threshold: Default pass/fail cutoff used by :meth:`passed`.
    """

    def __init__(
        self,
        provider: str | Provider,
        rubric: str | Rubric,
        *,
        threshold: float = 0.5,
    ) -> None:
        self.provider: Provider = _resolve_provider(provider)
        self.rubric: Rubric = _resolve_rubric(rubric)
        self.threshold = threshold

    def score(
        self,
        prompt: str,
        response: str,
        *,
        context: str | None = None,
        reference: str | None = None,
        **provider_kwargs: object,
    ) -> JudgeResult:
        """Judge ``response`` to ``prompt`` and return a :class:`JudgeResult`.

        Args:
            prompt: The original task/instruction.
            response: The model output to evaluate.
            context: Authoritative source material (required by some rubrics,
                e.g. groundedness).
            reference: A gold/expected answer, if available.
            **provider_kwargs: Forwarded verbatim to the provider's
                ``complete`` (e.g. ``temperature=0``).

        Raises:
            ConfigurationError: If the rubric requires context and none is given.
            ParseError: If the judge model's output has no parseable verdict.
        """
        if self.rubric.requires_context and not context:
            raise ConfigurationError(
                f"Rubric {self.rubric.name!r} requires context= to be supplied."
            )
        judge_prompt = self.rubric.render(
            prompt=prompt, response=response, context=context, reference=reference
        )
        provider_response = self.provider.complete(judge_prompt, **provider_kwargs)
        return self._build_result(provider_response)

    __call__ = score

    def passed(
        self,
        prompt: str,
        response: str,
        **kwargs: Any,
    ) -> bool:
        """Convenience: score and compare against the Judge's ``threshold``."""
        return self.score(prompt, response, **kwargs).passed(self.threshold)

    def _build_result(self, response: ProviderResponse) -> JudgeResult:
        data = extract_json(response.text)
        metadata: dict[str, Any] = {
            "provider": getattr(self.provider, "name", type(self.provider).__name__),
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms,
            "cost_usd": response.cost_usd,
        }
        reason = data.get("reason")
        return JudgeResult(
            score=_coerce_score(data.get("score")),
            confidence=_coerce_unit(data.get("confidence"), default=1.0),
            reason="" if reason is None else str(reason),
            evidence=_as_str_tuple(data.get("evidence")),
            violations=_as_str_tuple(data.get("violations")),
            rubric=self.rubric.name,
            raw=response.text,
            metadata=metadata,
        )


def _resolve_provider(provider: str | Provider) -> Provider:
    if isinstance(provider, str):
        return make_provider(provider)
    complete = getattr(provider, "complete", None)
    if not callable(complete):
        raise ConfigurationError(
            "provider must be a 'scheme:model' string or a Provider instance "
            f"with a callable complete(); got {type(provider).__name__!r}."
        )
    return provider


def _resolve_rubric(rubric: str | Rubric) -> Rubric:
    if isinstance(rubric, str):
        return get_rubric(rubric)
    return rubric


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def _coerce_score(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ParseError(f"Judge output missing a numeric 'score' (got {value!r}).")
    return _clamp_unit(float(value))


def _coerce_unit(value: Any, *, default: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return _clamp_unit(float(value))


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item is not None)
    return (str(value),)

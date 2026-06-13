"""Rubric definition, rendering, and registry.

A :class:`Rubric` is a small, declarative description of *what* to evaluate. It
knows how to render itself into a judging prompt that asks the model for a
strict JSON verdict. Rubrics are registered by name so they can be selected
with ``Judge(rubric="factuality")`` and extended without touching the core.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from llmjudge.errors import RubricError

# Shared output contract appended to every rendered rubric. Keeping it in one
# place means the parser and every rubric agree on the JSON shape.
_OUTPUT_INSTRUCTION = """\
Respond with ONLY a single JSON object (no markdown, no commentary) of the form:
{
  "score": <float between 0.0 and 1.0, where 1.0 fully satisfies the rubric>,
  "confidence": <float between 0.0 and 1.0 — how sure you are of this verdict>,
  "reason": "<one or two sentences justifying the score>",
  "evidence": ["<short quote or fact that informed the score>", ...],
  "violations": ["<name of any criterion that was not met>", ...]
}
Use an empty array when there is no evidence or no violations."""


@dataclass(frozen=True)
class Rubric:
    """A declarative evaluation rubric.

    Attributes:
        name: Stable identifier (used for registration and on ``JudgeResult``).
        description: One-line statement of what high quality means here.
        criteria: Specific things the judge should check.
        guidance: Extra free-form instructions appended to the prompt.
        requires_context: If True, ``Judge.score`` requires ``context=`` to be
            supplied (e.g. groundedness needs source material to check against).
    """

    name: str
    description: str
    criteria: tuple[str, ...] = ()
    guidance: str = ""
    requires_context: bool = False
    # Kept for forward-compatible per-rubric metadata without an API break.
    metadata: dict[str, str] = field(default_factory=dict)

    def render(
        self,
        *,
        prompt: str,
        response: str,
        context: str | None = None,
        reference: str | None = None,
    ) -> str:
        """Render the full judging prompt for one (prompt, response) pair.

        Args:
            prompt: The original task/instruction given to the evaluated model.
            response: The model output under evaluation.
            context: Authoritative source material (for grounded rubrics).
            reference: A gold/expected answer, if available.
        """
        parts: list[str] = [
            "You are an impartial, meticulous expert evaluator.",
            f"Evaluate the RESPONSE using the '{self.name}' rubric.",
            f"Rubric: {self.description}",
        ]
        if self.criteria:
            criteria = "\n".join(f"- {c}" for c in self.criteria)
            parts.append(f"Criteria:\n{criteria}")
        if self.guidance:
            parts.append(self.guidance)
        if context is not None:
            parts.append(f"CONTEXT (authoritative source material):\n{context}")
        if reference is not None:
            parts.append(f"REFERENCE (gold/expected answer):\n{reference}")
        parts.append(f"TASK / PROMPT:\n{prompt}")
        parts.append(f"RESPONSE TO EVALUATE:\n{response}")
        parts.append(_OUTPUT_INSTRUCTION)
        return "\n\n".join(parts)


_REGISTRY: dict[str, Rubric] = {}


def register_rubric(rubric: Rubric, *, overwrite: bool = False) -> None:
    """Register ``rubric`` under its ``name`` for lookup by string.

    Raises:
        RubricError: If the name is already registered and ``overwrite`` is False.
    """
    if rubric.name in _REGISTRY and not overwrite:
        raise RubricError(
            f"Rubric {rubric.name!r} is already registered; pass overwrite=True to replace it."
        )
    _REGISTRY[rubric.name] = rubric


def get_rubric(name: str) -> Rubric:
    """Return the registered rubric named ``name``.

    Raises:
        RubricError: If no rubric is registered under that name.
    """
    try:
        return _REGISTRY[name]
    except KeyError:
        raise RubricError(
            f"Unknown rubric {name!r}. Available: {available_rubrics() or '[none]'}."
        ) from None


def available_rubrics() -> list[str]:
    """Return the registered rubric names, sorted."""
    return sorted(_REGISTRY)

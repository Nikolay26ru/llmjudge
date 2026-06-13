"""Tests for rubric definition, rendering, and the registry."""

from __future__ import annotations

import pytest

from llmjudge.errors import RubricError
from llmjudge.rubrics import (
    available_rubrics,
    get_rubric,
    register_rubric,
)
from llmjudge.rubrics.base import Rubric


def test_builtins_are_registered() -> None:
    for name in (
        "factuality",
        "groundedness",
        "relevance",
        "instruction_following",
        "safety",
    ):
        assert name in available_rubrics()
        assert get_rubric(name).name == name


def test_get_unknown_rubric_raises() -> None:
    with pytest.raises(RubricError, match="Unknown rubric"):
        get_rubric("does_not_exist")


def test_register_and_retrieve() -> None:
    rubric = Rubric(name="brevity_test", description="Be brief.")
    register_rubric(rubric)
    assert get_rubric("brevity_test") is rubric


def test_register_duplicate_without_overwrite_raises() -> None:
    rubric = Rubric(name="dup_test", description="x")
    register_rubric(rubric)
    with pytest.raises(RubricError, match="already registered"):
        register_rubric(rubric)


def test_register_duplicate_with_overwrite() -> None:
    register_rubric(Rubric(name="ow_test", description="first"))
    register_rubric(Rubric(name="ow_test", description="second"), overwrite=True)
    assert get_rubric("ow_test").description == "second"


def test_render_contains_prompt_and_response() -> None:
    rubric = get_rubric("relevance")
    rendered = rubric.render(prompt="What is X?", response="X is Y.")
    assert "What is X?" in rendered
    assert "X is Y." in rendered
    assert "JSON" in rendered


def test_render_includes_criteria_and_guidance() -> None:
    rubric = get_rubric("factuality")
    rendered = rubric.render(prompt="p", response="r")
    assert "Criteria:" in rendered
    assert rubric.criteria[0] in rendered
    assert rubric.guidance in rendered


def test_render_without_criteria_or_guidance() -> None:
    rubric = Rubric(name="bare_test", description="bare")
    rendered = rubric.render(prompt="p", response="r")
    assert "Criteria:" not in rendered
    assert "p" in rendered


def test_render_includes_context_and_reference_when_given() -> None:
    rubric = get_rubric("groundedness")
    rendered = rubric.render(prompt="p", response="r", context="SOURCE FACT", reference="GOLD")
    assert "CONTEXT" in rendered
    assert "SOURCE FACT" in rendered
    assert "REFERENCE" in rendered
    assert "GOLD" in rendered


def test_render_omits_context_section_when_absent() -> None:
    rendered = get_rubric("relevance").render(prompt="p", response="r")
    assert "CONTEXT" not in rendered
    assert "REFERENCE" not in rendered


def test_groundedness_requires_context_flag() -> None:
    assert get_rubric("groundedness").requires_context is True
    assert get_rubric("factuality").requires_context is False

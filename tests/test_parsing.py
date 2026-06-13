"""Tests for robust JSON extraction from messy model output."""

from __future__ import annotations

import pytest

from llmjudge.errors import ParseError
from llmjudge.parsing import extract_json


def test_clean_json() -> None:
    assert extract_json('{"score": 0.5}') == {"score": 0.5}


def test_json_with_surrounding_whitespace() -> None:
    assert extract_json('   \n {"a": 1} \n ') == {"a": 1}


def test_markdown_fenced_json() -> None:
    text = 'Here is the verdict:\n```json\n{"score": 0.9}\n```\nThanks!'
    assert extract_json(text) == {"score": 0.9}


def test_plain_fenced_json() -> None:
    text = '```\n{"ok": true}\n```'
    assert extract_json(text) == {"ok": True}


def test_prose_wrapped_json() -> None:
    text = 'Sure! The answer is {"score": 0.3, "reason": "meh"} — hope that helps.'
    assert extract_json(text) == {"score": 0.3, "reason": "meh"}


def test_nested_braces_returns_outer_object() -> None:
    text = '{"score": 0.5, "metadata": {"k": {"deep": 1}}}'
    assert extract_json(text) == {"score": 0.5, "metadata": {"k": {"deep": 1}}}


def test_braces_inside_strings_do_not_confuse_scanner() -> None:
    # The closing brace inside the string must not end the object early.
    text = 'prefix {"reason": "use a } brace", "score": 1} suffix'
    assert extract_json(text) == {"reason": "use a } brace", "score": 1}


def test_escaped_quote_inside_string() -> None:
    text = r'{"reason": "she said \"hi\"", "score": 0.7}'
    assert extract_json(text) == {"reason": 'she said "hi"', "score": 0.7}


def test_trailing_comma_is_tolerated() -> None:
    assert extract_json('{"score": 0.5, "evidence": [1, 2,],}') == {
        "score": 0.5,
        "evidence": [1, 2],
    }


def test_trailing_comma_cleanup_preserves_string_values() -> None:
    # The ",}" inside the string value must survive; only the structural
    # trailing comma before the final "}" is removed.
    assert extract_json('{"a": "x,}y", "b": 1,}') == {"a": "x,}y", "b": 1}


def test_trailing_comma_before_bracket_inside_string_preserved() -> None:
    assert extract_json('{"a": "y,] z", "b": [1,],}') == {"a": "y,] z", "b": [1]}


def test_first_object_wins_when_multiple() -> None:
    text = '{"score": 0.1} and then {"score": 0.9}'
    assert extract_json(text) == {"score": 0.1}


def test_object_inside_top_level_array() -> None:
    # Whole-text parse yields a list (rejected); brace scan recovers the object.
    assert extract_json('[{"score": 0.5}]') == {"score": 0.5}


def test_empty_fence_is_skipped() -> None:
    # An empty fenced block yields an empty candidate; the real object is found
    # by the brace scan afterwards.
    assert extract_json('```\n```\nblah {"score": 0.5}') == {"score": 0.5}


def test_irreparable_trailing_comma_still_raises() -> None:
    # Trailing-comma cleanup changes the text but it is still invalid JSON.
    with pytest.raises(ParseError):
        extract_json('{"a": ,}')


def test_brace_scan_handles_nested_objects_and_escapes() -> None:
    # Forces the brace scanner (prose prefix) through nested braces, an escaped
    # quote, and a brace inside a string.
    text = 'note: {"reason": "a \\"q\\" and } brace", "meta": {"k": 1}} end'
    assert extract_json(text) == {"reason": 'a "q" and } brace', "meta": {"k": 1}}


def test_raises_on_no_json() -> None:
    with pytest.raises(ParseError):
        extract_json("there is no json here at all")


def test_raises_on_empty() -> None:
    with pytest.raises(ParseError):
        extract_json("")


def test_raises_on_unbalanced_braces() -> None:
    with pytest.raises(ParseError):
        extract_json('{"score": 0.5')


def test_parse_error_preserves_raw_and_truncates_message() -> None:
    raw = "x" * 500
    with pytest.raises(ParseError) as info:
        extract_json(raw)
    assert info.value.raw == raw
    assert "…" in str(info.value)

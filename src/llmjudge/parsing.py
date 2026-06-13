"""Robust extraction of a JSON object from messy model output.

Judge models are asked to return a bare JSON object, but in practice they wrap
it in markdown fences, prepend prose ("Sure! Here is the JSON:"), or append a
trailing comma. :func:`extract_json` recovers the object from all of these and
raises a clear :class:`ParseError` (preserving the raw text) when it genuinely
cannot.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

from llmjudge.errors import ParseError

# ```json ... ``` or plain ``` ... ``` fenced blocks.
_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)
# A trailing comma right before a closing brace/bracket (a common model slip).
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def extract_json(text: str) -> dict[str, Any]:
    """Return the first JSON object found in ``text``.

    Tries, in order: the whole string, any fenced code block, then every
    balanced ``{...}`` span. A final trailing-comma cleanup is attempted per
    candidate.

    Raises:
        ParseError: If no candidate parses to a JSON object.
    """
    for candidate in _candidates(text):
        obj = _try_load(candidate)
        if isinstance(obj, dict):
            return obj
    snippet = text if len(text) <= 200 else text[:200] + "…"
    raise ParseError(
        f"Could not extract a JSON object from model output: {snippet!r}",
        raw=text,
    )


def _candidates(text: str) -> Iterator[str]:
    stripped = text.strip()
    if stripped:
        yield stripped
    for match in _FENCE_RE.finditer(text):
        yield match.group(1)
    yield from _brace_objects(text)


def _try_load(candidate: str) -> Any:
    candidate = candidate.strip()
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    cleaned = _TRAILING_COMMA_RE.sub(r"\1", candidate)
    if cleaned != candidate:
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None
    return None


def _brace_objects(text: str) -> Iterator[str]:
    """Yield each top-level ``{...}`` span, ignoring braces inside JSON strings."""
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for i, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}" and depth > 0:
            depth -= 1
            if depth == 0:
                yield text[start : i + 1]

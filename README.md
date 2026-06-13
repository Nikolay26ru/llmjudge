# LLMJudge

> Provider-agnostic, reproducible, typed **LLM-as-a-judge** — a small primitive you can depend on.

[![CI](https://github.com/Nikolay26ru/llmjudge/actions/workflows/ci.yml/badge.svg)](https://github.com/Nikolay26ru/llmjudge/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Typed](https://img.shields.io/badge/typed-mypy%20strict-blue)](https://mypy-lang.org/)

LLMJudge is one tiny, well-tested module for scoring model outputs with an LLM
judge — the part most projects re-implement badly. The core has **zero required
runtime dependencies**, a **stable typed API**, and runs **fully offline in
tests** via a deterministic mock.

## Install

```bash
pip install llmjudge                 # core only, zero deps
pip install "llmjudge[openai]"       # + OpenAI-compatible provider
pip install "llmjudge[anthropic]"    # + Anthropic provider
pip install "llmjudge[all]"          # all providers
```

## Quickstart

This runs as-is — no API key, deterministic ([`examples/quickstart.py`](examples/quickstart.py)):

```python
from llmjudge import Judge, MockProvider

# MockProvider(fixed_score=...) keeps this example deterministic and offline.
judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="factuality")

result = judge.score(
    prompt="What is the capital of France?",
    response="The capital of France is Paris.",
)

assert result > 0.8  # a JudgeResult compares like its float score
print(f"score={result.score}  confidence={result.confidence}")
print(f"passed={result.passed()}  reason={result.reason!r}")
```

With a **real model**, swap the provider for a spec string — nothing else changes:

```python
judge = Judge(provider="openai:gpt-5", rubric="factuality")
result = judge.score(prompt, response)
if not result.passed(0.7):
    print("Failed:", result.reason, result.violations)
```

## Core concepts

| Piece | What it is |
| --- | --- |
| `Judge(provider, rubric)` | Pairs a model backend with a rubric; `score()` → `JudgeResult`. |
| `JudgeResult` | Frozen, typed verdict: `score`, `confidence`, `reason`, `evidence`, `violations`, `raw`, `metadata`. Compares and casts like its `score`. |
| `Provider` | A `Protocol` with one method, `complete(prompt) -> ProviderResponse`. |
| `Rubric` | Declarative description of *what* to evaluate; renders a strict-JSON judging prompt. |

### `JudgeResult` ergonomics

```python
r = judge.score(prompt, response)
r.score            # float in [0, 1]
float(r)           # same number
r > 0.8            # compares like its score
r.passed(0.7)      # bool against a threshold
r.reason           # short justification
r.evidence         # tuple of supporting quotes/facts
r.violations       # tuple of failed criteria
r.metadata         # provider, model, token usage, latency, cost
```

### Built-in rubrics

`factuality`, `groundedness` (requires `context=`), `relevance`,
`instruction_following`, `safety`. List them with
`llmjudge.available_rubrics()`.

```python
judge = Judge(provider="openai:gpt-5", rubric="groundedness")
result = judge.score(question, answer, context=retrieved_docs)  # RAG check
```

## Extend without touching the core

Add a **rubric** ([`examples/custom_rubric.py`](examples/custom_rubric.py)):

```python
from llmjudge import Rubric, register_rubric

register_rubric(Rubric(
    name="conciseness",
    description="Whether the response is as short as possible while complete.",
    criteria=("No filler or repetition.", "Every sentence earns its place."),
))
judge = Judge(provider="openai:gpt-5", rubric="conciseness")
```

Add a **provider** — implement one method, optionally register a scheme:

```python
from llmjudge import ProviderResponse, register_provider

class MyProvider:
    name = "mine"
    def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        return ProviderResponse(text=call_my_model(prompt))

register_provider("mine", lambda model: MyProvider())
judge = Judge(provider="mine:v1", rubric="relevance")
```

## Why depend on this

- **Easy to depend on** — zero transitive deps in the core; provider SDKs are opt-in extras.
- **Reproducible** — deterministic offline `MockProvider`; all unit tests run without network.
- **Typed** — `mypy --strict` clean; ships `py.typed`.
- **Robust parsing** — recovers JSON from markdown fences, prose, and trailing commas.
- **Extensible** — new provider / rubric / judge without core changes.

## Development

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest --cov=llmjudge --cov-report=term-missing
```

See [CONTRIBUTING.md](CONTRIBUTING.md). The plan of record is in [ROADMAP.md](ROADMAP.md).

## License

MIT — see [LICENSE](LICENSE).

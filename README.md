# LLMJudge Kit

> Provider-agnostic, reproducible, typed **LLM-as-a-judge** — a small primitive you can depend on.

[![PyPI](https://img.shields.io/pypi/v/llm-judge-kit)](https://pypi.org/project/llm-judge-kit/)
[![Python versions](https://img.shields.io/pypi/pyversions/llm-judge-kit)](https://pypi.org/project/llm-judge-kit/)
[![CI](https://github.com/Nikolay26ru/llm-judge-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/Nikolay26ru/llm-judge-kit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Typed: mypy strict](https://img.shields.io/badge/typed-mypy%20strict-blue)](https://mypy-lang.org/)

LLMJudge Kit is one tiny, well-tested module for scoring model outputs with an LLM
judge — the part most projects re-implement badly. The core has **zero required
runtime dependencies**, a **stable typed API**, and runs **fully offline in
tests** via a deterministic mock.

## Install

```bash
pip install llm-judge-kit                 # core only, zero deps
pip install "llm-judge-kit[openai]"       # + OpenAI-compatible provider
pip install "llm-judge-kit[anthropic]"    # + Anthropic provider
pip install "llm-judge-kit[all]"          # all providers
```

## Quickstart

This runs as-is — no API key, deterministic ([`examples/quickstart.py`](examples/quickstart.py)):

```python
from llm_judge_kit import Judge, MockProvider

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
`instruction_following`, `safety`, `coherence`, `completeness`. List them with
`llm_judge_kit.available_rubrics()`.

```python
judge = Judge(provider="openai:gpt-5", rubric="groundedness")
result = judge.score(question, answer, context=retrieved_docs)  # RAG check
```

## Consensus (vote across models)

Run several judge models and aggregate — `confidence` reflects how much they
**agree** ([`examples/consensus.py`](examples/consensus.py)):

```python
judge = Judge.consensus(
    ["openai:gpt-5", "anthropic:claude-opus-4-8", "ollama:llama3"],
    rubric="factuality",
)
result = judge.score(prompt, response)
result.score          # mean (or median) of member scores
result.confidence     # high when members agree, low when they diverge
result.metadata["votes"]   # each member's score
```

## Reliability & caching

Both wrappers are providers, so they compose around any backend
([`examples/reliability_and_cache.py`](examples/reliability_and_cache.py)):

```python
from llm_judge_kit import Judge, OpenAIProvider, RetryProvider, CachingProvider

provider = CachingProvider(                      # memoize identical calls
    RetryProvider(                               # retry w/ backoff + timeout
        OpenAIProvider(model="gpt-5"), retries=3, timeout=30,
    )
)
judge = Judge(provider=provider, rubric="factuality")
```

The cache key is `version + provider + model + prompt + kwargs`, so it is stable
and invalidates correctly across library versions. Logs are emitted on the
`llm_judge_kit` logger (silent by default; call `enable_debug_logging()` to see them).

## Integrations

### pytest — eval as ordinary tests

Installing `llm_judge_kit` registers a pytest plugin (no conftest wiring). The
`llm_judge_kit` fixture turns an eval into a normal test; a failure reads like any
other failing assertion (score, reason, violations):

```python
def test_answer_is_grounded(llm_judge_kit):
    llm_judge_kit.assert_passes(
        prompt="How tall is the Eiffel Tower?",
        response=my_rag_pipeline("How tall is the Eiffel Tower?"),
        rubric="groundedness",
        context=retrieved_docs,
        threshold=0.7,
    )
```

Pick the judge model once for the whole suite — it defaults to `mock` (offline),
so tests are green until you point them at a real model:

```bash
pytest --llm-judge-kit-provider "openai:gpt-5"      # or: export LLM_JUDGE_KIT_PROVIDER=...
```

Runnable example: [`examples/test_with_pytest.py`](examples/test_with_pytest.py).

### Any framework

LLMJudge Kit judges *strings*, so it drops into any stack — LangChain, LlamaIndex,
DSPy, a raw script — with no adapter. Whatever produces the output, pass it in:

```python
output = my_chain.invoke(question)          # LangChain / LlamaIndex / your code
result = Judge(provider="openai:gpt-5", rubric="relevance").score(question, output)
```

## Extend without touching the core

Add a **rubric** ([`examples/custom_rubric.py`](examples/custom_rubric.py)):

```python
from llm_judge_kit import Rubric, register_rubric

register_rubric(Rubric(
    name="conciseness",
    description="Whether the response is as short as possible while complete.",
    criteria=("No filler or repetition.", "Every sentence earns its place."),
))
judge = Judge(provider="openai:gpt-5", rubric="conciseness")
```

Add a **provider** — implement one method, optionally register a scheme:

```python
from llm_judge_kit import ProviderResponse, register_provider

class MyProvider:
    name = "mine"
    def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        return ProviderResponse(text=call_my_model(prompt))

register_provider("mine", lambda model: MyProvider())
judge = Judge(provider="mine:v1", rubric="relevance")
```

## CLI & batch evaluation

Score a whole dataset and get a report — JSON, Markdown, or HTML. A dataset is
JSON Lines (`prompt` + `response`, optional `context`/`reference`/`id`); see
[`examples/sample_dataset.jsonl`](examples/sample_dataset.jsonl).

```bash
llm-judge-kit eval cases.jsonl --provider openai:gpt-5 --rubric factuality --format md
llm-judge-kit eval cases.jsonl --fail-under 0.9            # exit non-zero in CI if pass rate drops
llm-judge-kit compare cases.jsonl --provider openai:gpt-5 --provider anthropic:claude-opus-4-8
llm-judge-kit report report.json --format html -o report.html
```

Try it now — offline, on the shipped sample dataset (deterministic mock scores;
point `--provider` at a real model for real verdicts):

```console
$ llm-judge-kit eval examples/sample_dataset.jsonl --rubric factuality --format md
# LLMJudge Kit report

- **provider:** mock
- **rubric:** factuality
- **threshold:** 0.50
- **cases:** 3
- **passed:** 1 (33.3%)
- **mean score:** 0.596

| # | id | score | result | reason |
| --- | --- | ---: | :---: | --- |
| 1 | fr-capital | 0.997 | PASS | Deterministic mock verdict. |
| 2 | math | 0.349 | FAIL | Deterministic mock verdict. |
| 3 | eiffel | 0.442 | FAIL | Deterministic mock verdict. |
```

Swap `--format html -o report.html` for a shareable, self-contained HTML report.

Same thing in code ([`examples/benchmark_report.py`](examples/benchmark_report.py)):

```python
from llm_judge_kit import Judge, load_dataset, run_benchmark, render_markdown

cases = load_dataset("cases.jsonl")
judge = Judge(provider="openai:gpt-5", rubric="factuality")
report = run_benchmark(judge, cases, provider="openai:gpt-5", rubric="factuality")
print(report.pass_rate, report.mean_score)
print(render_markdown(report))
```

## Use it as a CI gate

Block a merge when answer quality regresses — `--fail-under` exits non-zero, and
the core installs with no heavy dependency tree:

```yaml
# .github/workflows/eval.yml  (steps inside your job)
- run: pip install "llm-judge-kit[openai]"
- run: llm-judge-kit eval cases.jsonl --rubric factuality --provider openai:gpt-5 --fail-under 0.9
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Or keep evals as ordinary `pytest` tests via the bundled plugin (see
[Integrations](#pytest--eval-as-ordinary-tests)) and run them in your existing
test job.

## Why depend on this

- **Easy to depend on** — zero transitive deps in the core; provider SDKs are opt-in extras.
- **Reproducible** — deterministic offline `MockProvider`; all unit tests run without network.
- **Typed** — `mypy --strict` clean; ships `py.typed`.
- **Robust parsing** — recovers JSON from markdown fences, prose, and trailing commas.
- **Extensible** — new provider / rubric / judge without core changes.

## Development

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest --cov=llm_judge_kit --cov-report=term-missing
```

See [CONTRIBUTING.md](CONTRIBUTING.md). The plan of record is in [ROADMAP.md](ROADMAP.md).

## License

MIT — see [LICENSE](LICENSE).

# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-06-14

### Added
- Runnable pytest-integration example (`examples/test_with_pytest.py`),
  exercised in CI under pytest.
- Trusted Publishing release workflow (`.github/workflows/release.yml`) — future
  releases publish to PyPI from GitHub Actions via OIDC (no API token).

### Changed
- Aligned the product brand to **LLMJudge Kit** across the README, docs, and
  generated report titles (the distribution is `llm-judge-kit`; the public
  `LLMJudgeError` API is unchanged).
- Declared the GitHub maintainer (`Nikolay26ru`) as the package
  author/maintainer in metadata and `LICENSE`.
- Lowered the Development Status classifier from `4 - Beta` to `3 - Alpha`.

## [0.1.0] - 2026-06-13

### Added
- Project scaffold: `pyproject.toml`, tooling gate (ruff + mypy strict + pytest
  with ≥95% coverage), CI workflow, MIT license, contributor docs.
- **Wedge core (M1):**
  - `Judge` — pairs a provider with a rubric; `score()` returns a typed
    `JudgeResult`; `__call__` alias and `passed()` convenience.
  - `JudgeResult` / `ProviderResponse` — frozen, typed; `JudgeResult` casts
    (`__float__`) and compares (`<`, `<=`, `>`, `>=`) like its score.
  - `Provider` protocol + `BaseProvider`; deterministic offline `MockProvider`.
  - Provider registry with `"scheme:model"` spec parsing (`register_provider`,
    `make_provider`, `available_providers`).
  - `Rubric` + registry and five built-ins: factuality, groundedness,
    relevance, instruction_following, safety (`register_rubric`, `get_rubric`,
    `available_rubrics`).
  - Robust `extract_json` parser (markdown fences, surrounding prose, trailing
    commas, nested braces) with a clear `ParseError`.
  - Typed exception hierarchy (`LLMJudgeError` and subclasses).
  - Runnable examples and a README quickstart that executes offline.

- **Real providers (M2):**
  - `OpenAIProvider` (Chat Completions; works with any OpenAI-compatible
    `base_url`), `AnthropicProvider` (Messages API), `OllamaProvider` (local,
    via httpx). Registered under the `openai:`/`anthropic:`/`ollama:` schemes.
  - SDKs are imported lazily — the core stays dependency-free; the import only
    happens when a real client is built, with a clear error pointing at the
    extra to install.
  - Offline unit tests drive every provider through injected fake clients;
    live API tests are gated behind `LLM_JUDGE_KIT_LIVE_TESTS=1` (skipped by default).

- **Consensus + reliability (M3):**
  - `ConsensusJudge` and `Judge.consensus([...], rubric=...)` — aggregate
    several judges (mean/median); `confidence` is derived from agreement
    (tight spread → high confidence) and member votes land in `metadata`.
  - `RetryProvider` — composable retry-with-backoff and optional per-call
    timeout wrapper (injectable sleep for deterministic tests).
  - `CachingProvider` — memoizes completions; key = hash of
    `version + provider + model + prompt + kwargs` (pluggable store).
  - Structured logging on the `llm_judge_kit` logger (ships a `NullHandler`;
    `enable_debug_logging()` for local debugging).
  - Version moved to `_version.py` (single source; hatchling dynamic version).

- **Adoption surface (M4):**
  - Bundled pytest plugin (`pytest11` entry point → top-level `pytest_llm_judge_kit`
    module): the `llm_judge_kit` fixture and `JudgeHelper.assert_passes` let you
    write evals as ordinary pytest tests, with score/reason/violations in the
    failure message. Choose the model with `--llm-judge-kit-provider` or
    `$LLM_JUDGE_KIT_PROVIDER` (defaults to `mock`, so suites run offline).
  - README "Integrations" section, including a framework-agnostic note (works
    with LangChain / LlamaIndex / any pipeline — it judges strings).

- **Platform layer (M5):**
  - `llm_judge_kit` CLI (argparse, no new deps): `eval` (run a dataset → report,
    with `--fail-under` for CI gating), `compare` (several providers side by
    side), `report` (re-render a saved JSON report).
  - Dataset loader (`load_dataset`, `Case`) for `.jsonl`/`.ndjson`/`.json`.
  - Benchmark engine (`run_benchmark`, `Report` with count/passed/pass_rate/
    mean_score), kept separate from reporting.
  - Reporting (`render_json`/`render_markdown`/`render_html`, `load_report`) —
    JSON round-trips back into a `Report`.

### Hardened (M1 adversarial review)
- Trailing-comma JSON repair is now string-aware — it no longer corrupts string
  values that contain `,}` or `,]`.
- Non-finite scores/confidence (`NaN`, `Infinity`) are rejected/defaulted
  instead of silently clamping to a perfect `1.0`.
- `JudgeResult` and `ProviderResponse` are now genuinely hashable (the `dict`
  `metadata` field is excluded from the hash).

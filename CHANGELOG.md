# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Hardened (M1 adversarial review)
- Trailing-comma JSON repair is now string-aware — it no longer corrupts string
  values that contain `,}` or `,]`.
- Non-finite scores/confidence (`NaN`, `Infinity`) are rejected/defaulted
  instead of silently clamping to a perfect `1.0`.
- `JudgeResult` and `ProviderResponse` are now genuinely hashable (the `dict`
  `metadata` field is excluded from the hash).

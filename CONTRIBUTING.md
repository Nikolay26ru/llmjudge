# Contributing to LLMJudge Kit

Thanks for your interest! LLMJudge Kit aims to be a small, dependable primitive, so
contributions are judged first on whether they keep the core **easy to depend
on**: stable public API, minimal dependencies, great DX.

## Development setup

We use [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras        # create .venv and install dev + provider deps
uv run pytest               # run the offline test suite
```

## The verification gate

Every change must pass the same gate CI runs:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov=llm_judge_kit --cov-report=term-missing
```

- Coverage must stay **≥ 95%**.
- mypy runs in **strict** mode.
- Unit tests must be **offline** — use `MockProvider`. Never make network calls
  in unit tests. Live provider tests live behind `LLM_JUDGE_KIT_LIVE_TESTS=1`.

## Conventions

- **Conventional Commits**: `feat:`, `fix:`, `test:`, `docs:`, `chore:`,
  `refactor:`. Keep commits small and focused.
- **`main` is always green.** Open a PR; do not merge red.
- Adding a new provider, judge, or rubric should require **no changes to the
  core** — extend via the public extension points.
- New runtime dependencies need an explicit justification. The core stays
  dependency-free; provider SDKs go behind optional extras.

## Extending LLMJudge Kit

- **New provider**: implement the `Provider` protocol (`complete()`), and
  optionally register it under a scheme via `register_provider`.
- **New rubric**: build a `Rubric` and pass it to `Judge`, or register it by
  name with `register_rubric`.
- **New judge strategy**: compose `Judge` / `ConsensusJudge`, or implement the
  same `score()` surface.

By contributing, you agree your contributions are licensed under the MIT License.

# ROADMAP

Durable plan of record. Survives context compaction — re-read this after any
`/clear` or auto-compact to recover where work stopped. Keep checkboxes current.

Strategy: ship the **wedge** first — a small, flawless, easy-to-import
`llmjudge` LLM-as-a-judge primitive — then build the platform around the
adopted core. Narrow and deep beats wide and shallow.

## M0 — Scaffold
- [x] `pyproject.toml` (Python 3.11+, src-layout, hatchling build backend)
- [x] ruff + mypy(strict) + pytest + coverage gate config
- [x] MIT `LICENSE`, `.gitignore` (with `.env`)
- [x] doc stubs: README / ROADMAP / CHANGELOG / CLAUDE.md / CONTRIBUTING.md
- [x] empty package imports
- [x] `.github/workflows/ci.yml` runs the same gate
- [x] gate green locally

## M1 — Wedge core (TOP priority)
- [x] `types.py` — `JudgeResult`, `ProviderResponse` (frozen, `__float__`, ordering, `passed()`)
- [x] `providers/base.py` — `Provider` Protocol + `BaseProvider`
- [x] `providers/mock.py` — deterministic `MockProvider` (offline)
- [x] `parsing.py` — robust JSON extraction from model output
- [x] `rubrics/` — built-in rubrics (factuality, groundedness, relevance, instruction_following, safety)
- [x] `errors.py` — typed exception hierarchy
- [x] provider registry / `Judge(provider="mock:...")` string spec parsing
- [x] `judge.py` — `Judge` class + target public API
- [x] README with a working 10-line example above the fold
- [x] full coverage on mock (100%); README example runs

## M2 — Real providers
- [x] openai-compatible provider (any OpenAI-compatible base_url)
- [x] anthropic provider
- [x] ollama provider (httpx)
- [x] live tests gated behind `LLMJUDGE_LIVE_TESTS=1` (skip by default)
- [x] offline tests via injected fake clients (no network); lazy SDK import

## M3 — Consensus + reliability
- [ ] `ConsensusJudge` (voting across judge models, confidence from agreement)
- [ ] retry + timeout wrapper
- [ ] call cache (key = hash of prompt+rubric+provider+version)
- [ ] structured logging

## M4 — Adoption surface
- [ ] `pytest11` plugin (eval as ordinary pytest tests)
- [ ] thin framework integrations / examples
- [ ] README "Integrations" section

## M5 — Platform layer
- [ ] CLI (`llmjudge eval` / `compare` / `report`)
- [ ] reporting (JSON / Markdown / HTML)
- [ ] minimal benchmark engine + dataset loader

## Done / handoff
- [ ] wheel builds
- [ ] (human) push to GitHub public repo + verify CI
- [ ] (human) publish to PyPI + submit to "Claude for Open Source"

## Decisions log (ambiguity resolutions)
- Repo root at `~/llmjudge` (durable) rather than the session outputs path.
- Dev env pinned to CPython 3.12 (mypy/tooling stability); `requires-python>=3.11`.
- Core has zero runtime deps; providers behind extras `[openai]/[anthropic]/[ollama]`.
- pytest plugin ships inside the `llmjudge` dist via a `pytest11` entry point
  (no second distribution to publish) — easier to depend on.

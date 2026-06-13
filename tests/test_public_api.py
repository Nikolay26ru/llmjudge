"""The public surface must stay importable and the docstring example must run."""

from __future__ import annotations

import subprocess
import sys

import llmjudge


def test_all_names_are_importable() -> None:
    for name in llmjudge.__all__:
        assert hasattr(llmjudge, name), f"{name} missing from llmjudge"


def test_version_is_sane() -> None:
    assert isinstance(llmjudge.__version__, str)
    assert llmjudge.__version__.count(".") >= 2


def test_headline_snippet_runs() -> None:
    # Mirrors the README / package docstring above-the-fold example.
    from llmjudge import Judge, MockProvider

    judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="factuality")
    result = judge.score("What is the capital of France?", "Paris.")
    assert result > 0.8
    assert result.passed()


def test_importing_core_pulls_in_no_provider_sdks() -> None:
    # The wedge promise: `import llmjudge` must not drag in any provider SDK.
    # Checked in a fresh interpreter because other tests import them eagerly.
    probe = (
        "import sys; import llmjudge; "
        "leaked = sorted(m for m in ('openai', 'anthropic', 'httpx') if m in sys.modules); "
        "assert not leaked, leaked"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"core import leaked provider SDKs: {proc.stderr.strip()}"

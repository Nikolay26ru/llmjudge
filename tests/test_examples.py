"""Every example script must actually run end-to-end (offline, exit code 0)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
# Top-level examples plus the integration examples (which degrade to an offline
# stub when their framework isn't installed, so they still run with exit 0).
_EXAMPLES = sorted(_EXAMPLES_DIR.glob("*.py")) + sorted(
    (_EXAMPLES_DIR / "integrations").glob("*.py")
)


def test_examples_directory_is_not_empty() -> None:
    assert _EXAMPLES, "no example scripts found"


@pytest.mark.parametrize("script", _EXAMPLES, ids=lambda p: p.name)
def test_example_runs(script: Path) -> None:
    # `test_*.py` examples demonstrate the pytest plugin, so they must be run
    # *under pytest* (which loads the llm_judge_kit fixture) rather than as a
    # plain script; the rest are standalone scripts. Either way: offline, exit 0.
    if script.name.startswith("test_"):
        cmd = [sys.executable, "-m", "pytest", str(script), "-q", "-p", "no:cacheprovider"]
    else:
        cmd = [sys.executable, str(script)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, f"{script.name} failed:\n{result.stdout}\n{result.stderr}"

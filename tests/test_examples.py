"""Every example script must actually run end-to-end (offline, exit code 0)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
_EXAMPLES = sorted(_EXAMPLES_DIR.glob("*.py"))


def test_examples_directory_is_not_empty() -> None:
    assert _EXAMPLES, "no example scripts found"


@pytest.mark.parametrize("script", _EXAMPLES, ids=lambda p: p.name)
def test_example_runs(script: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, f"{script.name} failed:\n{result.stderr}"

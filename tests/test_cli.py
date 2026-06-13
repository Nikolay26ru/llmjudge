"""Tests for the llm_judge_kit CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_judge_kit.cli import main


def _dataset(tmp_path: Path) -> Path:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        '{"id": "a", "prompt": "p1", "response": "r1"}\n'
        '{"id": "b", "prompt": "p2", "response": "r2"}\n'
    )
    return path


def test_eval_json_to_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["eval", str(_dataset(tmp_path)), "--rubric", "relevance", "--format", "json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["count"] == 2
    assert data["provider"] == "mock"


def test_eval_writes_output_file(tmp_path: Path) -> None:
    out = tmp_path / "report.md"
    assert main(["eval", str(_dataset(tmp_path)), "-o", str(out)]) == 0
    assert "# LLMJudge Kit report" in out.read_text()


def test_eval_html_format(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    assert main(["eval", str(_dataset(tmp_path)), "--format", "html", "-o", str(out)]) == 0
    assert "<table>" in out.read_text()


def test_eval_fail_under_triggers_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["eval", str(_dataset(tmp_path)), "--fail-under", "1.01"])
    assert code == 1
    assert "below --fail-under" in capsys.readouterr().err


def test_eval_fail_under_passes(tmp_path: Path) -> None:
    assert main(["eval", str(_dataset(tmp_path)), "--fail-under", "0.0"]) == 0


def test_compare(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["compare", str(_dataset(tmp_path)), "--provider", "mock", "--provider", "mock"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Comparison on rubric 'factuality'" in out
    assert "pass rate" in out


def test_report_roundtrip(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report_file = tmp_path / "r.json"
    assert main(["eval", str(_dataset(tmp_path)), "-o", str(report_file), "--format", "json"]) == 0
    assert main(["report", str(report_file), "--format", "md"]) == 0
    assert "# LLMJudge Kit report" in capsys.readouterr().out


def test_error_returns_exit_code_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["eval", str(tmp_path / "missing.jsonl")])
    assert code == 2
    assert "error:" in capsys.readouterr().err


def test_no_command_exits() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_output_to_missing_dir_returns_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "nope" / "r.md"  # parent directory does not exist
    code = main(["eval", str(_dataset(tmp_path)), "-o", str(out)])
    assert code == 2
    assert "error:" in capsys.readouterr().err


def test_directory_as_dataset_returns_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    directory = tmp_path / "data.jsonl"  # a directory with a dataset-like suffix
    directory.mkdir()
    code = main(["eval", str(directory)])
    assert code == 2
    assert "error:" in capsys.readouterr().err

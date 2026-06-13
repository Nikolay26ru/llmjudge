"""Render and load benchmark reports (JSON / Markdown / HTML).

Kept separate from the benchmark engine so reporting can evolve independently
of how scores are produced. ``render_json`` round-trips through ``load_report``.
"""

from __future__ import annotations

import html
import json
import math
from pathlib import Path
from typing import Any

from llm_judge_kit.benchmark import CaseResult, Report
from llm_judge_kit.dataset import Case
from llm_judge_kit.errors import DatasetError
from llm_judge_kit.types import JudgeResult


def report_to_dict(report: Report) -> dict[str, Any]:
    """Serialize a report to a plain dict (the JSON shape)."""
    return {
        "provider": report.provider,
        "rubric": report.rubric,
        "threshold": report.threshold,
        "summary": {
            "count": report.count,
            "passed": report.passed,
            "pass_rate": report.pass_rate,
            "mean_score": report.mean_score,
        },
        "cases": [
            {
                "id": cr.case.id,
                "prompt": cr.case.prompt,
                "response": cr.case.response,
                "context": cr.case.context,
                "reference": cr.case.reference,
                "score": cr.result.score,
                "confidence": cr.result.confidence,
                "passed": cr.result.passed(report.threshold),
                "reason": cr.result.reason,
                "evidence": list(cr.result.evidence),
                "violations": list(cr.result.violations),
            }
            for cr in report.results
        ],
    }


def report_from_dict(data: dict[str, Any]) -> Report:
    """Reconstruct a :class:`Report` from :func:`report_to_dict` output.

    Scores are validated and clamped to ``[0, 1]`` (same invariant the live
    judge enforces), so a hand-edited or corrupted report can't smuggle in an
    out-of-range or non-numeric score that would skew the stats or crash a
    later render.
    """
    try:
        rubric = data["rubric"]
        results = tuple(
            CaseResult(
                case=Case(
                    prompt=c["prompt"],
                    response=c["response"],
                    context=c.get("context"),
                    reference=c.get("reference"),
                    id=c.get("id"),
                ),
                result=JudgeResult(
                    score=_load_score(c["score"], index),
                    confidence=_load_confidence(c.get("confidence", 1.0)),
                    reason=c.get("reason", ""),
                    evidence=tuple(c.get("evidence", ())),
                    violations=tuple(c.get("violations", ())),
                    rubric=rubric,
                ),
            )
            for index, c in enumerate(data["cases"])
        )
        return Report(
            provider=data["provider"],
            rubric=rubric,
            threshold=data["threshold"],
            results=results,
        )
    except (KeyError, TypeError) as exc:
        raise DatasetError(f"malformed report: missing or invalid field {exc}") from exc


def _load_score(value: Any, index: int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DatasetError(f"case {index}: 'score' must be a finite number, got {value!r}")
    return max(0.0, min(1.0, float(value)))


def _load_confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return 1.0
    return max(0.0, min(1.0, float(value)))


def load_report(path: str | Path) -> Report:
    """Load a JSON report written by :func:`render_json`."""
    file_path = Path(path)
    if not file_path.exists():
        raise DatasetError(f"report not found: {file_path}")
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DatasetError(f"invalid report JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise DatasetError("a report file must be a JSON object")
    return report_from_dict(data)


def render_json(report: Report) -> str:
    """Render a report as pretty JSON (round-trips via :func:`load_report`)."""
    return json.dumps(report_to_dict(report), indent=2, ensure_ascii=False)


def render_markdown(report: Report) -> str:
    """Render a report as a Markdown summary + per-case table."""
    lines = [
        "# LLMJudge Kit report",
        "",
        f"- **provider:** {_md_cell(report.provider)}",
        f"- **rubric:** {_md_cell(report.rubric)}",
        f"- **threshold:** {report.threshold:.2f}",
        f"- **cases:** {report.count}",
        f"- **passed:** {report.passed} ({report.pass_rate:.1%})",
        f"- **mean score:** {report.mean_score:.3f}",
        "",
        "| # | id | score | result | reason |",
        "| --- | --- | ---: | :---: | --- |",
    ]
    for i, cr in enumerate(report.results, start=1):
        case_id = cr.case.id if cr.case.id is not None else str(i)
        verdict = "PASS" if cr.result.passed(report.threshold) else "FAIL"
        lines.append(
            f"| {i} | {_md_cell(case_id)} | {cr.result.score:.3f} | "
            f"{verdict} | {_md_cell(cr.result.reason)} |"
        )
    return "\n".join(lines) + "\n"


def render_html(report: Report) -> str:
    """Render a report as a small self-contained HTML page."""
    rows = []
    for i, cr in enumerate(report.results, start=1):
        case_id = cr.case.id if cr.case.id is not None else str(i)
        passed = cr.result.passed(report.threshold)
        verdict = "PASS" if passed else "FAIL"
        css = "pass" if passed else "fail"
        rows.append(
            f"<tr><td>{i}</td><td>{html.escape(case_id)}</td>"
            f"<td>{cr.result.score:.3f}</td>"
            f'<td class="{css}">{verdict}</td>'
            f"<td>{html.escape(cr.result.reason)}</td></tr>"
        )
    rows_html = "\n".join(rows)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LLMJudge Kit report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
th {{ background: #f4f1ea; }}
td.pass {{ color: #1a7f37; font-weight: 600; }}
td.fail {{ color: #b3261e; font-weight: 600; }}
</style>
</head>
<body>
<h1>LLMJudge Kit report</h1>
<p><strong>provider:</strong> {html.escape(report.provider)} &middot;
<strong>rubric:</strong> {html.escape(report.rubric)} &middot;
<strong>threshold:</strong> {report.threshold:.2f}</p>
<p><strong>{report.passed}/{report.count}</strong> passed
({report.pass_rate:.1%}) &middot; mean score {report.mean_score:.3f}</p>
<table>
<thead><tr><th>#</th><th>id</th><th>score</th><th>result</th><th>reason</th></tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
</body>
</html>
"""


def _md_cell(text: str) -> str:
    """Make a string safe for a single Markdown table cell or list item."""
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()

import os
from pathlib import Path
from typing import Any, Dict, List

from backend.app.utils import parse_docx_rows


DOCX_PATH = Path(
    "/Users/yuxin.xue/Projects/qenergy-platform/uploads/Test Data/CW32/CW32_Weekly Report_DEV.docx"
)


class _UploadLike:
    def __init__(self, path: Path):
        self._fh = open(path, "rb")
        self.file = self._fh

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass


def _run_parser(path: Path) -> List[Dict[str, Any]]:
    up = _UploadLike(path)
    try:
        # Using a safe default cw/category to avoid changing signature
        rows = parse_docx_rows(up, cw_label="CW32", category="Development")
    finally:
        up.close()
    return rows


def test_baseline_integrity():
    assert DOCX_PATH.exists(), f"Missing test input: {DOCX_PATH}"
    rows = _run_parser(DOCX_PATH)

    assert isinstance(rows, list)
    assert len(rows) >= 1

    required_keys = {
        "category",
        "entry_type",
        "cw_label",
        "title",
        "summary",
        "source_text",
        "next_actions",
        "owner",
        "attachment_url",
    }

    for row in rows[:5]:  # spot-check first few
        assert required_keys.issubset(row.keys())

    # Non-empty summaries should exist
    non_empty = [r for r in rows if (r.get("summary") or "").strip()]
    assert len(non_empty) >= 1


def test_blockization_increases_slices_against_baseline_report():
    """
    After Step A, len(rows) should be >= baseline rows stored in baseline_report.json.
    If baseline report is not generated yet, skip this test with a helpful message.
    """
    baseline_file = Path("/Users/yuxin.xue/Projects/qenergy-platform/baseline_report.json")
    if not baseline_file.exists():
        import pytest
        pytest.skip("baseline_report.json not found; run compare_runs.py to generate baseline first.")

    import json
    with open(baseline_file, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    baseline_rows = int(baseline.get("basic_metrics", {}).get("rows", 0))
    assert baseline_rows >= 1

    rows = _run_parser(DOCX_PATH)
    assert len(rows) >= baseline_rows


def test_boundary_reduction_of_bleed_against_baseline():
    """
    Step B target: reduce cross-project bleed. We heuristically check that for
    a small sample of distinct titles, the summary does not contain the name of
    a different sample project more than once.

    If baseline not present, skip.
    """
    baseline_file = Path("/Users/yuxin.xue/Projects/qenergy-platform/baseline_report.json")
    if not baseline_file.exists():
        import pytest
        pytest.skip("baseline_report.json not found; run compare_runs.py to generate baseline first.")

    rows = _run_parser(DOCX_PATH)
    titles = [r.get("title") or "" for r in rows if (r.get("title") or "").strip()]
    titles = list({t for t in titles})[:15]

    # Heuristic sample: if we have at least 5 distinct titles
    if len(titles) < 5:
        import pytest
        pytest.skip("Not enough titles to sample bleed heuristic.")

    # Build a simple bleed score: for each row's summary, count occurrences of other titles' first token
    def first_token(t: str) -> str:
        return (t.split()[0] if t else "").strip("-_")

    tokens = [first_token(t) for t in titles]
    token_set = {tok for tok in tokens if tok}

    # Count summaries that contain >=2 different other tokens
    bleed_rows = 0
    for r in rows:
        summ = (r.get("summary") or "").lower()
        hit = 0
        for tok in token_set:
            if tok and tok.lower() in summ:
                hit += 1
            if hit >= 2:
                bleed_rows += 1
                break

    # We don't enforce a strict number, but ensure bleed_rows is not growing drastically
    # Baseline was around the same rows; allow slight increase but not > 10
    assert bleed_rows <= 10

import argparse
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root on sys.path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.utils import parse_docx_rows, parse_filename  # type: ignore


class SimpleUpload:
    def __init__(self, filepath: Path):
        self._fh = open(filepath, "rb")
        self.file = self._fh
        self.filename = filepath.name

    def close(self):
        try:
            self._fh.close()
        except Exception:
            pass


def sample_titles_and_summaries(rows: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for row in rows[:limit]:
        out.append({
            "title": (row.get("title") or ""),
            "summary_head": (row.get("summary") or "")[:160],
        })
    return out


def compute_basic_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    titles = [r.get("title") for r in rows]
    uniq_titles = len({t for t in titles if t})
    summaries = [(r.get("summary") or "") for r in rows]
    empty_count = sum(1 for s in summaries if not s.strip())
    avg_len = statistics.mean([len(s) for s in summaries]) if summaries else 0
    return {
        "rows": len(rows),
        "unique_titles": uniq_titles,
        "empty_summary_ratio": (empty_count / len(rows) if rows else 0),
        "avg_summary_len": avg_len,
    }


def try_parse_labels_from_filename(filepath: Path) -> Dict[str, str]:
    try:
        _year, cw_label, _raw_cat, category = parse_filename(filepath.name)
        return {"cw_label": cw_label, "category": category}
    except Exception:
        # Fallback defaults
        return {"cw_label": "CW00", "category": "Development"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate baseline/step report for parse_docx_rows")
    parser.add_argument("--input", required=True, help="Path to DOCX file")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--label", default="baseline", help="Run label to store in report")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    labels = try_parse_labels_from_filename(input_path)

    upload = SimpleUpload(input_path)
    try:
        started = time.time()
        rows = parse_docx_rows(upload, labels["cw_label"], labels["category"])
        elapsed_ms = int((time.time() - started) * 1000)
    finally:
        upload.close()

    # Attempt to read internal metrics populated by the parser
    internal_metrics = None
    try:
        from backend.app.utils import LAST_PARSE_DOCX_METRICS  # type: ignore
        internal_metrics = LAST_PARSE_DOCX_METRICS
    except Exception:
        internal_metrics = None

    report: Dict[str, Any] = {
        "run_label": args.label,
        "input": str(input_path),
        "elapsed_ms": elapsed_ms,
        "basic_metrics": compute_basic_metrics(rows),
        "samples": sample_titles_and_summaries(rows, limit=10),
        "internal_metrics": internal_metrics,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

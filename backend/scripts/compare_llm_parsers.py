import os
import sys
import json
import time
from typing import List, Dict
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
    # Load backend/.env if present for Azure credentials
    BACKEND_ROOT = Path(__file__).resolve().parents[1]
    env_path = BACKEND_ROOT / ".env"
    if env_path.exists():
        load_dotenv(str(env_path), override=False)
except Exception:
    pass

from app.llm_parser import (
    extract_rows_from_docx,
    extract_rows_from_docx_single_pass,
    _load_doc_text,  # type: ignore
    _split_into_sections,  # type: ignore
    _extract_rows_from_text_core,  # type: ignore
)
from app.utils import parse_filename, parse_docx_rows


def summarize(rows: List[Dict]) -> Dict:
    return {
        "count": len(rows),
        "non_empty_source_text": sum(1 for r in rows if (r.get("source_text") or "").strip()),
        "avg_summary_len": (sum(len(r.get("summary") or "") for r in rows) / len(rows)) if rows else 0,
        "categories": sorted({r.get("category") for r in rows}),
    }


def _print_bar(label: str, current: int, total: int, width: int = 30):
    pct = 0 if total == 0 else current / max(total, 1)
    filled = int(width * pct)
    bar = "#" * filled + "-" * (width - filled)
    print(f"\r{label}: [{bar}] {current}/{total}", end="", flush=True)


def _println_done():
    print("", flush=True)


def extract_rows_sectioned_with_progress(file_path: str, cw_label: str, raw_category: str) -> List[Dict]:
    # Build sections to report progress
    text = _load_doc_text(file_path)
    sections = _split_into_sections(text)
    total = len(sections) or 1
    rows: List[Dict] = []
    _print_bar("LLM (sectioned)", 0, total)
    for idx, section in enumerate(sections, 1):
        part = _extract_rows_from_text_core(section, cw_label, raw_category, whitelist_projects=[])
        if part:
            rows.extend(part)
        _print_bar("LLM (sectioned)", idx, total)
    _println_done()
    return rows


def main():
    docx = os.environ.get("DOCX_PATH")
    if not docx:
        raise SystemExit("Set DOCX_PATH to the .docx file to analyze")

    # Derive cw/category from filename, fallback sensible defaults
    try:
        _year, cw_label, raw_cat, display_cat = parse_filename(os.path.basename(docx))
        default_cat = raw_cat
    except Exception:
        cw_label = os.environ.get("CW_LABEL", "CW01")
        default_cat = os.environ.get("DEFAULT_CATEGORY", "DEV")

    # New pipeline (sectioning) with progress
    new_rows = extract_rows_sectioned_with_progress(docx, cw_label, default_cat)
    # Legacy single-pass (simple one-shot progress)
    _print_bar("LLM (single-pass)", 0, 1)
    old_rows = extract_rows_from_docx_single_pass(docx, cw_label, default_cat)
    _print_bar("LLM (single-pass)", 1, 1)
    _println_done()
    # Simple parser
    class _MockFile:
        def __init__(self, path: str):
            self.file = open(path, "rb")
        def close(self):
            try:
                self.file.close()
            except Exception:
                pass
    _print_bar("Simple parser", 0, 1)
    mf = _MockFile(docx)
    try:
        simple_rows = parse_docx_rows(mf, cw_label, default_cat)
    finally:
        mf.close()
    _print_bar("Simple parser", 1, 1)
    _println_done()

    report = {
        "file": docx,
        "cw_label": cw_label,
        "default_category": default_cat,
        "new": summarize(new_rows),
        "old": summarize(old_rows),
        "simple": summarize(simple_rows),
        "delta": {
            "count": len(new_rows) - len(old_rows),
            "non_empty_source_text": summarize(new_rows)["non_empty_source_text"] - summarize(old_rows)["non_empty_source_text"],
        },
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()



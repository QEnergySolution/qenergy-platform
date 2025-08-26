import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient

BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app


client = TestClient(app)


DATA_DIR = Path("/Users/yuxin.xue/Projects/qenergy-platform/Weekly-analyzer/backend/uploads")


def _is_pattern_match(name: str) -> bool:
    name = name.upper()
    return name.endswith(".DOCX") and any(s in name for s in ("_DEV.DOCX", "_EPC.DOCX", "_FINANCE.DOCX", "_INVESTMENT.DOCX"))


def test_bulk_upload_parses_real_docx_rows():
    if not DATA_DIR.exists():
        raise AssertionError(f"Test data directory does not exist: {DATA_DIR}")

    files = []
    picked = []
    for p in sorted(DATA_DIR.glob("*.docx")):
        if _is_pattern_match(p.name):
            picked.append(p)
        if len(picked) >= 4:
            break

    assert picked, "No matching .docx files found for test"

    for p in picked:
        files.append(("files", (p.name, p.open("rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")))

    resp = client.post("/api/reports/upload/bulk", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    oks = [r for r in body["results"] if r.get("status") == "ok"]
    assert len(oks) == len(picked)
    for r in oks:
        assert isinstance(r.get("rows"), list)
        # Expect at least one parsed row per file
        assert len(r["rows"]) >= 1



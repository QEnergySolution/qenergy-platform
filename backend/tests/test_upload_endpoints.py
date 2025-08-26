import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app


client = TestClient(app)


def _mk_file(filename: str, content: bytes = b"dummy"):
    return (filename, io.BytesIO(content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


def test_single_upload_rejects_non_docx():
    files = {"file": ("2025_CW01_DEV.pdf", io.BytesIO(b"%PDF"), "application/pdf")}
    resp = client.post("/api/reports/upload", files=files)
    assert resp.status_code == 400
    body = resp.json()
    assert body["errors"][0]["code"] == "UNSUPPORTED_TYPE"


def test_single_upload_rejects_invalid_name():
    files = {"file": _mk_file("Bi-Weekly Report_CW07.docx")}
    resp = client.post("/api/reports/upload", files=files)
    assert resp.status_code == 400
    body = resp.json()
    assert body["errors"][0]["code"] == "INVALID_NAME"


def test_bulk_upload_mixed_files_returns_per_file_results():
    files = [
        ("files", _mk_file("2025_CW01_DEV.docx")),
        ("files", ("2025_CW01_FINANCE.pdf", io.BytesIO(b"%PDF"), "application/pdf")),
        ("files", _mk_file("Bi-Weekly Report_CW07.docx")),
    ]
    resp = client.post("/api/reports/upload/bulk", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body and isinstance(body["results"], list)
    ok = [r for r in body["results"] if r.get("status") == "ok"]
    errors = [r for r in body["results"] if r.get("status") == "error"]
    assert any(r.get("fileName") == "2025_CW01_DEV.docx" for r in ok)
    assert any(r.get("fileName") == "2025_CW01_FINANCE.pdf" for r in errors)
    assert any(r.get("fileName").startswith("Bi-Weekly") for r in errors)



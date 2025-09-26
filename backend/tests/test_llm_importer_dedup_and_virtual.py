from pathlib import Path
from unittest.mock import patch
import re

from sqlalchemy import text


def _sample_docx(tmp_path: Path) -> str:
    # Reuse any path; content won't be read due to mocking
    p = tmp_path / "2025_CW01_DEV.docx"
    p.write_bytes(b"fake")
    return str(p)


def test_dedup_uses_project_code_log_date_category(db_session, tmp_path):
    from app.report_importer import import_single_docx_llm

    # Seed a project
    db_session.execute(text("""
        INSERT INTO projects (project_code, project_name, status, created_by, updated_by)
        VALUES ('P900','Alpha Solar',1,'sys','sys')
    """))

    # Two rows for same project & category -> should deduplicate to one record per (code, date, category)
    rows = [
        {
            "project_name": "Alpha Solar",
            "title": "Alpha - CW01",
            "summary": "S1",
            "next_actions": None,
            "owner": None,
            "category": "Development",
            "source_text": "Evidence 1.",
        },
        {
            "project_name": "Alpha Solar",
            "title": "Alpha - CW01",
            "summary": "S2",
            "next_actions": None,
            "owner": None,
            "category": "Development",
            "source_text": "Evidence 2.",
        },
    ]

    with patch("app.report_importer.extract_rows_from_docx", return_value=rows):
        result = import_single_docx_llm(db_session, _sample_docx(tmp_path), created_by="test")

    # Should only create one history row for the dedup key
    count = db_session.execute(text(
        "SELECT COUNT(*) FROM project_history WHERE source_upload_id=:id"
    ), {"id": result["upload_id"]}).scalar()
    assert count == 1


def test_fuzzy_mapping_and_virtual_code_format(db_session, tmp_path):
    from app.report_importer import import_single_docx_llm

    # Seed a near-match project name
    db_session.execute(text("""
        INSERT INTO projects (project_code, project_name, status, created_by, updated_by)
        VALUES ('P777','Bravo Wind',1,'sys','sys')
    """))

    mocked = [
        {  # Should fuzzy-map to Bravo Wind
            "project_name": "Bravo-Wind",
            "title": None,
            "summary": "Maintenance ongoing.",
            "next_actions": None,
            "owner": None,
            "category": "EPC",
            "source_text": "Original sentence present.",
        },
        {  # Should create virtual with VIRT_YYYYMMDD_HASH format
            "project_name": "Completely New Project",
            "title": None,
            "summary": "Kickoff started.",
            "next_actions": None,
            "owner": None,
            "category": None,
            "source_text": "Original line.",
        },
    ]

    with patch("app.report_importer.extract_rows_from_docx", return_value=mocked):
        result = import_single_docx_llm(db_session, _sample_docx(tmp_path), created_by="test")

    rows = db_session.execute(text(
        "SELECT project_code, project_name, category, source_text, log_date FROM project_history WHERE source_upload_id=:id ORDER BY id"
    ), {"id": result["upload_id"]}).all()
    assert len(rows) == 2

    codes = {r.project_code for r in rows}
    assert "P777" in codes
    virt_code = next(c for c in codes if c != "P777")
    assert virt_code.startswith("VIRT_")
    m = re.match(r"^VIRT_(\d{8})_([A-F0-9]{8})$", virt_code)
    assert m, f"unexpected virtual code format: {virt_code}"

    # Confirm project exists in projects table
    p = db_session.execute(text("SELECT project_name FROM projects WHERE project_code=:c"), {"c": virt_code}).first()
    assert p is not None



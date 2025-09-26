from pathlib import Path
from unittest.mock import patch

import io
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app
from app.database import get_db  # original dependency to override


def _mk_docx_file(name: str = "2025_CW01_DEV.docx", content: bytes = b"docx"):
    return {"file": (name, io.BytesIO(content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}


def test_persist_period_exists_and_overwrite_flow(db_session):
    # Override dependency to ensure API uses the same test DB session
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # Seed a project and an existing project_history row for 2025 CW01 Development
        db_session.execute(text(
            """
            INSERT INTO projects (project_code, project_name, status, created_by, updated_by)
            VALUES ('PX001','Existing Project',1,'seed','seed')
            ON CONFLICT (project_code) DO NOTHING
            """
        ))
        db_session.execute(text(
            """
            INSERT INTO project_history (
              project_code, project_name, category, entry_type, log_date, cw_label, title, summary, source_text, created_by, updated_by
            ) VALUES (
              'PX001','Existing Project','Development','Report','2025-01-01','CW01','Old','Old content','Old content','seed','seed'
            )
            """
        ))
        db_session.flush()

        # 1) First call without force_import should return period_exists
        files = _mk_docx_file()
        resp = client.post(
            "/api/reports/upload/persist?use_llm=false&override_year=2025&override_week=CW01&override_category=DEV",
            files=files
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("status") == "period_exists"
        assert body.get("year") == 2025
        assert body.get("cw_label") == "CW01"
        assert body.get("category") == "Development"
        assert body.get("existingCount", 0) >= 1

        # 2) Confirm overwrite by forcing import; patch parse_docx_rows to produce one new row
        mocked_rows = [
            {"title": "New Project - CW01", "summary": "New content", "category": "Development"}
        ]
        with patch("app.report_importer.parse_docx_rows", return_value=mocked_rows):
            forced = client.post(
                "/api/reports/upload/persist?use_llm=false&force_import=true&override_year=2025&override_week=CW01&override_category=DEV",
                files=_mk_docx_file()
            )
        assert forced.status_code == 200
        forced_body = forced.json()
        assert forced_body.get("status") == "persisted"
        assert forced_body.get("rowsCreated", 0) == 1

        # Verify DB: old row deleted and replaced with the single new row for the same period
        cnt = db_session.execute(text(
            """
            SELECT COUNT(*) FROM project_history
            WHERE cw_label='CW01' AND category='Development' AND EXTRACT(YEAR FROM log_date)=2025
            """
        )).scalar()
        assert cnt == 1

    finally:
        # Clean up override
        app.dependency_overrides.pop(get_db, None)

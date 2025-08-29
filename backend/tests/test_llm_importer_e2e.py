import os
from pathlib import Path

import pytest
from sqlalchemy import text


@pytest.mark.timeout(180)
def test_llm_e2e_single_file_import(db_session):
    if os.getenv("AZURE_OPENAI_E2E") != "1":
        pytest.skip("AZURE_OPENAI_E2E != 1; skipping live LLM test")

    # require Azure envs
    for k in ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"):
        if not os.getenv(k):
            pytest.skip(f"missing {k}")

    data_file = "/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx"
    assert Path(data_file).exists(), f"missing test file: {data_file}"

    from app.report_importer import import_single_docx_llm

    # seed a catch-all project code used by the mapper
    db_session.execute(text("INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES ('P_E2E','Any Project',1,'sys','sys')"))

    def mapper(_name: str) -> str | None:
        return "P_E2E"

    result = import_single_docx_llm(db_session, data_file, project_code_mapper=mapper, created_by="e2e")
    print(result)

    # verify upload row
    up = db_session.execute(text("SELECT id, status, cw_label, parsed_at FROM report_uploads WHERE id=:id"), {"id": result["upload_id"]}).first()
    assert up is not None and up.status == "parsed" and up.cw_label == "CW01" and up.parsed_at is not None

    # at least one history row
    cnt = db_session.execute(text("SELECT COUNT(*) FROM project_history WHERE source_upload_id=:id"), {"id": result["upload_id"]}).scalar_one()
    assert cnt >= 1

    row = db_session.execute(text("SELECT project_code, entry_type, cw_label, category, summary FROM project_history WHERE source_upload_id=:id LIMIT 1"), {"id": result["upload_id"]}).first()
    assert row.project_code == "P_E2E"
    assert row.entry_type == "Report"
    assert row.cw_label == "CW01"
    assert row.category in ("Development", "EPC", "Finance", "Investment")
    assert isinstance(row.summary, str) and len(row.summary.strip()) > 0



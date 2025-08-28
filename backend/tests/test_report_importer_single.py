from pathlib import Path
from sqlalchemy import text


def test_import_single_docx_creates_upload_and_history(db_session):
    from app.report_importer import import_single_docx

    # pick a real sample file in uploads/
    data_file = Path("/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx")
    assert data_file.exists(), f"Test file missing: {data_file}"

    # seed a project to satisfy FK
    db_session.execute(text("INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES ('PTEST','Test Project',1,'sys','sys')"))

    # run importer (use default project code for all parsed rows for 2B- stage)
    result = import_single_docx(db_session, str(data_file), default_project_code="PTEST", created_by="test")

    # verify upload row
    r = db_session.execute(text("SELECT id, status, sha256, cw_label FROM report_uploads WHERE id=:id"), {"id": result["upload_id"]}).first()
    assert r is not None
    assert r.status in ("parsed",)  # after successful import
    assert isinstance(r.sha256, str) and len(r.sha256) == 64
    assert r.cw_label == "CW01"

    # verify at least one project_history linked
    num_hist = db_session.execute(text("SELECT COUNT(*) FROM project_history WHERE source_upload_id=:id"), {"id": result["upload_id"]}).scalar_one()
    assert num_hist >= 1

    # verify linkage fields
    row = db_session.execute(text("SELECT project_code, entry_type, cw_label, category, source_upload_id FROM project_history WHERE source_upload_id=:id LIMIT 1"), {"id": result["upload_id"]}).first()
    assert row.project_code == "PTEST"
    assert row.entry_type == "Report"
    assert row.cw_label == "CW01"
    assert row.category == "Development"
    assert row.source_upload_id == result["upload_id"]



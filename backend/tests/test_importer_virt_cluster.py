from pathlib import Path
from unittest.mock import patch
from sqlalchemy import text


def _sample_docx(tmp_path: Path) -> str:
    p = tmp_path / "2025_CW10_EPC.docx"
    p.write_bytes(b"fake docx")
    return str(p)


def test_importer_creates_virt_cluster_when_cluster_only(db_session, tmp_path):
    from app.report_importer import import_single_docx_llm

    # Seed two projects in same cluster
    db_session.execute(text("""
        INSERT INTO projects (project_code, project_name, portfolio_cluster, status, created_by, updated_by)
        VALUES
          ('P201','Divor PV1','Cluster Madrid',1,'sys','sys'),
          ('P202','Divor PV2','Cluster Madrid',1,'sys','sys')
    """))

    # Mock LLM to return a single cluster-only row that cannot map to a project
    mocked_rows = [
        {
            "project_name": "Cluster Madrid",  # not a project name
            "title": None,
            "summary": "General cluster activities.",
            "next_actions": None,
            "owner": None,
            "category": "EPC",
            "source_text": "Work continues across Cluster Madrid."
        }
    ]

    with patch("app.report_importer.extract_rows_from_docx", return_value=mocked_rows):
        result = import_single_docx_llm(db_session, _sample_docx(tmp_path), created_by="test")

    # A new VIRT_CLUSTER_* project should be created and used in project_history
    rows = db_session.execute(text(
        "SELECT project_code, project_name FROM project_history WHERE source_upload_id=:id"
    ), {"id": result["upload_id"]}).all()

    assert len(rows) == 1
    virt_code = rows[0].project_code
    assert virt_code.startswith("VIRT_CLUSTER_")
    # Also present in projects table
    p = db_session.execute(text("SELECT project_name, portfolio_cluster FROM projects WHERE project_code=:c"), {"c": virt_code}).first()
    assert p is not None and p.portfolio_cluster == "Cluster Madrid"



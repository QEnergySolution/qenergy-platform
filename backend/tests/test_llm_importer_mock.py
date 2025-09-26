from pathlib import Path
from unittest.mock import patch

from sqlalchemy import text


def test_llm_importer_persists_multiple_rows_with_mapping(db_session):
    from app.report_importer import import_single_docx_llm

    # seed projects for mapping
    db_session.execute(text("INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES ('P001','Solar One',1,'sys','sys')"))
    db_session.execute(text("INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES ('P002','Wind Two',1,'sys','sys')"))

    data_file = "/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx"
    if not Path(data_file).exists():
        # fall back to a tiny temp file when the real sample is absent
        tmp = Path("/tmp/2025_CW01_DEV.docx")
        tmp.write_bytes(b"docx")
        data_file = str(tmp)

    # mock LLM parser to return two rows extracted from the docx
    mocked_rows = [
        {
            "project_name": "Solar One",
            "title": "Solar One update",
            "summary": "Panel cleaning and commissioning checks completed.",
            "next_actions": "Start hot commissioning next week.",
            "owner": "Alice",
            "category": "EPC",
            "source_text": "...evidence A...",
        },
        {
            "project_name": "Wind Two",
            "title": "Wind Two status",
            "summary": "Turbine 3 minor repairs scheduled.",
            "next_actions": None,
            "owner": "Bob",
            "category": None,  # will fallback to category from filename
            "source_text": "...evidence B...",
        },
    ]

    def mapping_func(name: str) -> str | None:
        if name.lower() == "solar one":
            return "P001"
        if name.lower() == "wind two":
            return "P002"
        return None

    # Patch where the symbol is used (imported into report_importer module)
    with patch("app.report_importer.extract_rows_from_docx", return_value=mocked_rows):
        result = import_single_docx_llm(
            db_session,
            data_file,
            project_code_mapper=mapping_func,
            created_by="test",
        )

    # verify upload created
    up = db_session.execute(text("SELECT id, status, cw_label FROM report_uploads WHERE id=:id"), {"id": result["upload_id"]}).first()
    assert up is not None and up.status == "parsed" and up.cw_label == "CW01"

    # verify two history rows created with mapping applied
    rows = db_session.execute(text("SELECT project_code, cw_label, category, title, summary, owner, source_text, log_date FROM project_history WHERE source_upload_id=:id ORDER BY project_code"), {"id": result["upload_id"]}).all()
    assert len(rows) == 2
    # Accept either ISO week Monday (2024-12-30) or Wednesday anchoring (2025-01-01)
    acceptable_dates = {"2024-12-30", "2025-01-01"}
    assert rows[0].project_code == "P001" and rows[0].cw_label == "CW01" and str(rows[0].log_date) in acceptable_dates
    assert rows[0].category == "EPC" and rows[0].source_text is not None
    assert rows[1].project_code == "P002" and rows[1].cw_label == "CW01" and str(rows[1].log_date) in acceptable_dates
    # category fallback from filename (DEV -> Development)
    assert rows[1].category == "Development" and rows[1].source_text is not None



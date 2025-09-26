from pathlib import Path
from unittest.mock import patch

from sqlalchemy import text


def _tmp_doc(path: str = "/tmp/2025_CW01_DEV.docx") -> str:
    p = Path(path)
    p.write_bytes(b"docx")
    return str(p)


def test_reupload_overrides_previous_llm(db_session):
    from app.report_importer import import_single_docx_llm

    # Seed projects for mapping
    db_session.execute(text("""
        INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES
        ('P001','Alpha Solar',1,'sys','sys'),
        ('P002','Beta Wind',1,'sys','sys'),
        ('P003','Gamma Hydro',1,'sys','sys')
    """))

    file_path = _tmp_doc()

    # First upload: Alpha + Beta
    rows_first = [
        {"project_name": "Alpha Solar", "summary": "Alpha summary v1", "category": "Development", "source_text": "alpha v1"},
        {"project_name": "Beta Wind", "summary": "Beta summary v1", "category": "Development", "source_text": "beta v1"},
    ]

    with patch("app.report_importer.extract_rows_from_docx", return_value=rows_first):
        import_single_docx_llm(db_session, file_path, created_by="test")

    # Verify two rows exist initially
    initial = db_session.execute(text(
        """
        SELECT project_code, summary FROM project_history
        WHERE cw_label='CW01' AND category='Development' AND created_by='test'
        ORDER BY project_code
        """
    )).all()
    assert len(initial) == 2

    # Second upload: Alpha (updated) + Gamma (new), should REPLACE previous week/category rows
    rows_second = [
        {"project_name": "Alpha Solar", "summary": "Alpha summary v2", "category": "Development", "source_text": "alpha v2"},
        {"project_name": "Gamma Hydro", "summary": "Gamma summary v1", "category": "Development", "source_text": "gamma v1"},
    ]

    with patch("app.report_importer.extract_rows_from_docx", return_value=rows_second):
        import_single_docx_llm(db_session, file_path, created_by="test")

    final_rows = db_session.execute(text(
        """
        SELECT project_code, summary FROM project_history
        WHERE cw_label='CW01' AND category='Development' AND created_by='test'
        ORDER BY project_code
        """
    )).all()

    # Expect exactly two rows: Alpha (updated) and Gamma; Beta removed
    assert len(final_rows) == 2
    codes = {r.project_code for r in final_rows}
    assert codes == {"P001", "P003"}
    alpha = next(r for r in final_rows if r.project_code == "P001")
    assert "v2" in alpha.summary


def test_reupload_overrides_previous_simple(db_session):
    from app.report_importer import import_single_docx_simple_with_metadata

    # Seed projects so simple importer can map by title-derived name
    db_session.execute(text("""
        INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES
        ('S001','Delta Solar',1,'sys','sys'),
        ('S002','Echo Wind',1,'sys','sys'),
        ('S003','Foxtrot Hydro',1,'sys','sys')
    """))

    file_path = _tmp_doc()

    # Simple importer uses parse_docx_rows; title is used as project name seed
    rows_first = [
        {"title": "Delta Solar - CW01", "summary": "Delta v1", "category": "Development"},
        {"title": "Echo Wind - CW01", "summary": "Echo v1", "category": "Development"},
    ]

    rows_second = [
        {"title": "Delta Solar - CW01", "summary": "Delta v2", "category": "Development"},
        {"title": "Foxtrot Hydro - CW01", "summary": "Foxtrot v1", "category": "Development"},
    ]

    with patch.object(db_session, 'commit', side_effect=lambda: db_session.flush()):
        with patch("app.report_importer.parse_docx_rows", return_value=rows_first):
            import_single_docx_simple_with_metadata(db_session, file_path, "2025_CW01_DEV.docx", created_by="test")

        initial = db_session.execute(text(
            """
            SELECT project_code, summary FROM project_history
            WHERE cw_label='CW01' AND category='Development' AND created_by='test'
            ORDER BY project_code
            """
        )).all()
        assert len(initial) == 2

        # Re-upload with updated/new rows; expect REPLACEMENT
        with patch("app.report_importer.parse_docx_rows", return_value=rows_second):
            import_single_docx_simple_with_metadata(db_session, file_path, "2025_CW01_DEV.docx", created_by="test")

        final_rows = db_session.execute(text(
            """
            SELECT project_code, summary FROM project_history
            WHERE cw_label='CW01' AND category='Development' AND created_by='test'
            ORDER BY project_code
            """
        )).all()

    assert len(final_rows) == 2
    codes = {r.project_code for r in final_rows}
    assert codes == {"S001", "S003"}
    delta = next(r for r in final_rows if r.project_code == "S001")
    assert "v2" in delta.summary


def test_year_scoped_delete_does_not_cross_year(db_session):
    from app.report_importer import import_single_docx_llm

    # Seed project codes
    db_session.execute(text("""
        INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES
        ('Y001','Yearly Solar',1,'sys','sys'),
        ('P001','Alpha Solar',1,'sys','sys')
    """))

    # Seed an older year's CW01 Development row (2024)
    db_session.execute(text("""
        INSERT INTO project_history (
            project_code, project_name, category, entry_type, log_date, cw_label, title, summary, source_text, created_by, updated_by
        ) VALUES (
            'Y001','Yearly Solar','Development','Report','2024-01-03','CW01','Y-24','Old 2024 content','Old 2024 content','seed2024','seed2024'
        )
    """))

    # Now import a 2025 CW01 DEV file that should override only 2025 rows
    file_path = _tmp_doc("/tmp/2025_CW01_DEV.docx")
    rows_now = [
        {"project_name": "Alpha Solar", "summary": "New 2025 content", "category": "Development", "source_text": "new 2025"}
    ]
    with patch("app.report_importer.extract_rows_from_docx", return_value=rows_now):
        import_single_docx_llm(db_session, file_path, created_by="test")

    # The 2024 row must remain
    cnt_2024 = db_session.execute(text(
        """
        SELECT COUNT(*) FROM project_history
        WHERE cw_label='CW01' AND category='Development' AND EXTRACT(YEAR FROM log_date)=2024
        """
    )).scalar()
    assert cnt_2024 == 1

    # And the 2025 row must exist for P001
    exists_2025 = db_session.execute(text(
        """
        SELECT COUNT(*) FROM project_history
        WHERE cw_label='CW01' AND category='Development' AND EXTRACT(YEAR FROM log_date)=2025 AND project_code='P001'
        """
    )).scalar()
    assert exists_2025 == 1



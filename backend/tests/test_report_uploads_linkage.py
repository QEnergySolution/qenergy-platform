from sqlalchemy import text


def test_project_history_can_reference_source_upload_id(db_session):
    # seed project
    db_session.execute(text("INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES ('PX01','Proj X',1,'sys','sys')"))

    # create upload
    upload_id = db_session.execute(
        text(
            """
            INSERT INTO report_uploads (
              original_filename, storage_path, mime_type, file_size_bytes,
              sha256, status, created_by, updated_by
            ) VALUES (
              '2025_CW03_FINANCE.docx', '/tmp/qenergy_uploads/2025_CW03_FINANCE.docx',
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 34567,
              :sha256, 'received', 'sys', 'sys'
            ) RETURNING id
            """
        ),
        {"sha256": "c" * 64},
    ).scalar_one()

    # insert project_history linked to upload
    db_session.execute(
        text(
            """
            INSERT INTO project_history (
              project_code, entry_type, log_date, summary, created_by, updated_by, source_upload_id
            ) VALUES ('PX01','Report','2025-01-20','ok','sys','sys', :upload_id)
            """
        ),
        {"upload_id": upload_id},
    )

    # verify linkage
    row = db_session.execute(text("SELECT source_upload_id FROM project_history WHERE project_code='PX01' AND log_date='2025-01-20'"))
    got = row.scalar_one()
    assert got == upload_id

    # on delete set null
    db_session.execute(text("DELETE FROM report_uploads WHERE id=:id"), {"id": upload_id})
    row2 = db_session.execute(text("SELECT source_upload_id FROM project_history WHERE project_code='PX01' AND log_date='2025-01-20'"))
    assert row2.scalar_one() is None



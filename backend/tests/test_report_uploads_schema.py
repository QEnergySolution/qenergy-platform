from sqlalchemy import text


def test_report_uploads_insert_and_unique_sha256(db_session):
    # insert one upload
    db_session.execute(
        text(
            """
            INSERT INTO report_uploads (
              original_filename, storage_path, mime_type, file_size_bytes,
              sha256, status, created_by, updated_by
            ) VALUES (
              :original_filename, :storage_path, :mime_type, :file_size_bytes,
              :sha256, 'received', 'sys', 'sys'
            )
            """
        ),
        {
            "original_filename": "2025_CW01_DEV.docx",
            "storage_path": "/tmp/qenergy_uploads/2025_CW01_DEV.docx",
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "file_size_bytes": 12345,
            "sha256": "a" * 64,
        },
    )
    # duplicate sha256 should violate UNIQUE (use nested transaction/savepoint)
    import pytest
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(
                text(
                    """
                    INSERT INTO report_uploads (
                      original_filename, storage_path, mime_type, file_size_bytes,
                      sha256, status, created_by, updated_by
                    ) VALUES (
                      :original_filename, :storage_path, :mime_type, :file_size_bytes,
                      :sha256, 'received', 'sys', 'sys'
                    )
                    """
                ),
                {
                    "original_filename": "dup.docx",
                    "storage_path": "/tmp/qenergy_uploads/dup.docx",
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "file_size_bytes": 1,
                    "sha256": "a" * 64,
                },
            )


def test_report_uploads_status_check_and_parsed_at(db_session):
    # create upload
    upload_id = db_session.execute(
        text(
            """
            INSERT INTO report_uploads (
              original_filename, storage_path, mime_type, file_size_bytes,
              sha256, status, created_by, updated_by
            ) VALUES (
              :original_filename, :storage_path, :mime_type, :file_size_bytes,
              :sha256, 'received', 'sys', 'sys'
            ) RETURNING id
            """
        ),
        {
            "original_filename": "2025_CW02_EPC.docx",
            "storage_path": "/tmp/qenergy_uploads/2025_CW02_EPC.docx",
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "file_size_bytes": 23456,
            "sha256": "b" * 64,
        },
    ).scalar_one()
    # valid transition to parsed
    db_session.execute(text("UPDATE report_uploads SET status='parsed', parsed_at=NOW(), notes='ok' WHERE id=:id"), {"id": upload_id})

    # invalid status should fail CHECK
    import pytest
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text("UPDATE report_uploads SET status='invalid' WHERE id=:id"), {"id": upload_id})



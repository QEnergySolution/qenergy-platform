from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_by_sha256(db: Session, sha256: str):
    return db.execute(text("SELECT id, status FROM report_uploads WHERE sha256=:sha"), {"sha": sha256}).first()


def create_received(
    db: Session,
    *,
    original_filename: str,
    storage_path: str,
    mime_type: str,
    file_size_bytes: int,
    sha256: str,
    cw_label: str | None,
    created_by: str,
):
    res = db.execute(
        text(
            """
            INSERT INTO report_uploads (
              original_filename, storage_path, mime_type, file_size_bytes,
              sha256, status, cw_label, created_by, updated_by
            ) VALUES (
              :original_filename, :storage_path, :mime_type, :file_size_bytes,
              :sha256, 'received', :cw_label, :created_by, :created_by
            ) RETURNING id
            """
        ),
        {
            "original_filename": original_filename,
            "storage_path": storage_path,
            "mime_type": mime_type,
            "file_size_bytes": file_size_bytes,
            "sha256": sha256,
            "cw_label": cw_label,
            "created_by": created_by,
        },
    )
    return res.scalar_one()


def mark_parsed(db: Session, upload_id: str, *, updated_by: str, notes: str | None = None):
    db.execute(
        text("UPDATE report_uploads SET status='parsed', parsed_at=NOW(), notes=COALESCE(:notes, notes), updated_by=:u WHERE id=:id"),
        {"notes": notes, "u": updated_by, "id": upload_id},
    )


def mark_failed(db: Session, upload_id: str, *, updated_by: str, notes: str):
    db.execute(
        text("UPDATE report_uploads SET status='failed', parsed_at=NULL, notes=:notes, updated_by=:u WHERE id=:id"),
        {"notes": notes, "u": updated_by, "id": upload_id},
    )



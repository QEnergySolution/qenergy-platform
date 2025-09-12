import os
import time
from pathlib import Path
from typing import Optional
import datetime

from fastapi import UploadFile


def get_tmp_dir() -> Path:
    base = os.getenv("REPORT_UPLOAD_TMP_DIR", "/tmp/qenergy_uploads")
    d = Path(base)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_to_tmp(upload: UploadFile, filename: str) -> Path:
    tmp_dir = get_tmp_dir()
    target = tmp_dir / filename
    # Avoid overwriting by appending suffix if exists
    i = 1
    base = target.stem
    ext = target.suffix
    while target.exists():
        target = tmp_dir / f"{base}_{i}{ext}"
        i += 1
    # stream to disk
    upload.file.seek(0)
    with target.open("wb") as f:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    return target


def cleanup_tmp(older_than_seconds: int) -> int:
    """Delete files older than given seconds. Returns count removed."""
    now = time.time()
    removed = 0
    tmp_dir = get_tmp_dir()
    for p in tmp_dir.glob("*"):
        try:
            if p.is_file():
                mtime = p.stat().st_mtime
                if (now - mtime) > older_than_seconds:
                    p.unlink(missing_ok=True)
                    removed += 1
        except Exception:
            # ignore errors
            continue
    return removed


# Persistent storage helpers

def _sanitize_filename(name: str) -> str:
    # Basic sanitization to avoid path traversal and unsafe chars
    name = name or "upload.bin"
    name = os.path.basename(name)
    name = name.replace("..", "_")
    # Replace spaces with underscores for readability
    return name.replace(" ", "_")


def get_storage_dir() -> Path:
    base = os.getenv("REPORT_UPLOAD_STORAGE_DIR")
    if not base:
        # Default to repo-level uploads/inbox (relative to CWD of the server process)
        base = os.path.join(os.getcwd(), "uploads", "inbox")
    d = Path(base)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_bytes_to_storage(content: bytes, filename: str) -> Path:
    storage_dir = get_storage_dir()
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = _sanitize_filename(filename)
    target = storage_dir / f"{ts}_{safe_name}"
    # Ensure uniqueness if called multiple times in the same second
    i = 1
    while target.exists():
        target = storage_dir / f"{ts}_{i}_{safe_name}"
        i += 1
    with target.open("wb") as f:
        f.write(content)
    return target


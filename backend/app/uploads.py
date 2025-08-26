import os
import time
from pathlib import Path
from typing import Optional

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



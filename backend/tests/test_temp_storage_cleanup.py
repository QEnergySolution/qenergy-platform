from pathlib import Path
import time

from app.uploads import get_tmp_dir, cleanup_tmp


def test_cleanup_tmp_removes_old_files(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("REPORT_UPLOAD_TMP_DIR", str(tmp_path))
    d = get_tmp_dir()
    f_old = d / "old.docx"
    f_new = d / "new.docx"
    f_old.write_text("x")
    f_new.write_text("y")
    # make old really old
    old_time = time.time() - 3600
    os_utime = getattr(__import__("os"), "utime")
    os_utime(f_old, (old_time, old_time))

    removed = cleanup_tmp(older_than_seconds=1800)
    assert removed >= 1
    assert not f_old.exists()
    assert f_new.exists()



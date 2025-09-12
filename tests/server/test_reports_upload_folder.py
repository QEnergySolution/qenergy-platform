import os
import io
import requests
from typing import List, Tuple


def _collect_docx_files(base_dir: str) -> List[Tuple[str, bytes]]:
    """
    Return list of (relative_path, content_bytes) for all .docx files under base_dir.
    relative_path simulates webkitdirectory's relative file path.
    """
    files: List[Tuple[str, bytes]] = []
    base_dir = os.path.abspath(base_dir)
    for root, _dirs, filenames in os.walk(base_dir):
        for name in filenames:
            if not name.lower().endswith(".docx"):
                continue
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, base_dir)
            with open(full_path, "rb") as f:
                files.append((rel_path, f.read()))
    return files


def test_bulk_upload_folder(remote_base_url):
    base_dir = "/Users/yuxin.xue/Projects/qenergy-platform/tests-uploads"
    docx_files = _collect_docx_files(base_dir)
    assert len(docx_files) >= 1, f"No .docx files found under {base_dir}"

    url = f"{remote_base_url}/reports/upload/bulk"

    # Build multipart form with multiple 'files' fields
    files = []
    for rel_path, content in docx_files:
        # Simulate browser's filename carrying relative path within the chosen folder
        files.append((
            "files",
            (
                rel_path,
                io.BytesIO(content),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ))

    r = requests.post(url, files=files, timeout=180)
    assert r.status_code == 200, r.text

    data = r.json()
    assert isinstance(data.get("results"), list)
    assert data.get("summary", {}).get("filesAccepted", 0) >= 1

    # Optionally ensure we got as many result entries as submitted files (allowing rejections)
    submitted_count = len(docx_files)
    assert len(data.get("results", [])) <= submitted_count

import io
import time
import requests
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile


def build_docx_bytes(text: str = "Task poll") -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
        with ZipFile(tmp, "w", ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
              <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
              <Default Extension="xml" ContentType="application/xml"/>
              <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
            </Types>
            """.strip())
            z.writestr("_rels/.rels", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
              <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/word/document.xml"/>
            </Relationships>
            """.strip())
            z.writestr("word/_rels/document.xml.rels", """
            <?xml version="1.0" encoding="UTF-8"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
            """.strip())
            z.writestr("word/document.xml", f"""
            <?xml version=\"1.0\" encoding=\"UTF-8\"?>
            <w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">
              <w:body>
                <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
              </w:body>
            </w:document>
            """.strip())
        tmp.seek(0)
        return tmp.read()


def test_task_status_polling(remote_base_url):
    # Kick off an upload to create a task
    upload_url = f"{remote_base_url}/reports/upload"
    docx_bytes = build_docx_bytes("Task status")
    files = {
        "file": ("CW03_FINANCE_task_poll.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    r = requests.post(upload_url, files=files, timeout=120)
    assert r.status_code == 200, r.text
    data = r.json()
    task_id = data.get("taskId")
    assert task_id

    # Poll task status until completed/failed or timeout
    status_url = f"{remote_base_url}/tasks/{task_id}"
    deadline = time.time() + 60
    last_status = None
    while time.time() < deadline:
        rs = requests.get(status_url, timeout=15)
        if rs.status_code == 404:
            time.sleep(1)
            continue
        rs.raise_for_status()
        status = rs.json()
        last_status = status
        if status.get("status") in {"completed", "failed"}:
            break
        time.sleep(1)

    assert last_status is not None
    assert last_status.get("status") in {"completed", "failed"}



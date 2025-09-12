import io
import requests
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile


def build_minimal_docx_bytes(text: str = "Persist me") -> bytes:
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


def test_persist_upload_creates_upload_and_history(remote_base_url, http_headers):
    url = f"{remote_base_url}/reports/upload/persist"
    # Use a simple pattern the backend's fallback parser recognizes: "Name: content"
    docx_bytes = build_minimal_docx_bytes("Project Alpha: Construction progressing this week with procurement initiated.")
    files = {
        "file": ("CW02_EPC_remote_persist.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    # Keep default use_llm=false for stability
    r = requests.post(url, files=files, timeout=180)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "persisted"
    assert data.get("uploadId")
    assert isinstance(data.get("rowsCreated"), int)

    # Optionally fetch upload history to verify endpoint responds
    upload_id = str(data.get("uploadId"))
    hist_url = f"{remote_base_url}/reports/uploads/{upload_id}/history"
    r2 = requests.get(hist_url, timeout=60)
    assert r2.status_code == 200, r2.text
    hist = r2.json()
    assert str(hist.get("upload", {}).get("id")) == upload_id



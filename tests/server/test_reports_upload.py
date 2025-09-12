import io
import requests
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile


def build_minimal_docx_bytes(text: str = "Hello") -> bytes:
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


def test_upload_single_simple_parser(remote_base_url, http_headers):
    url = f"{remote_base_url}/reports/upload"
    docx_bytes = build_minimal_docx_bytes("Weekly summary")
    # Filename must include CW and category to pass backend validation
    files = {
        "file": ("CW01_DEV_remote_test.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    r = requests.post(url, files=files, timeout=120)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("taskId")
    assert data.get("category")
    assert isinstance(data.get("rows"), list)



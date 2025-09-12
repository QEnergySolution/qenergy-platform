import io
import requests
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile


def build_docx_bytes(text: str) -> bytes:
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


def test_bulk_upload_three_files(remote_base_url):
    url = f"{remote_base_url}/reports/upload/bulk"
    f1 = ("CW04_DEV_bulk1.docx", io.BytesIO(build_docx_bytes("A")), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    f2 = ("CW04_EPC_bulk2.docx", io.BytesIO(build_docx_bytes("B")), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    f3 = ("CW04_FINANCE_bulk3.docx", io.BytesIO(build_docx_bytes("C")), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    files = [("files", f1), ("files", f2), ("files", f3)]
    r = requests.post(url, files=files, timeout=180)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data.get("results"), list)
    assert data.get("summary", {}).get("filesAccepted") >= 1



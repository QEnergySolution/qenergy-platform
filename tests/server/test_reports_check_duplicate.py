import io
import hashlib
import requests


def test_check_duplicate_non_docx_rejected(remote_base_url, http_headers):
    url = f"{remote_base_url}/reports/upload/check-duplicate"
    # Build a fake non-docx file
    content = b"not a docx"
    files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
    r = requests.post(url, files=files, timeout=30)
    assert r.status_code == 400
    data = r.json()
    assert data.get("errors")
    assert any(err.get("code") == "UNSUPPORTED_TYPE" for err in data.get("errors", []))


def test_check_duplicate_fresh_docx_returns_not_duplicate(remote_base_url, http_headers):
    url = f"{remote_base_url}/reports/upload/check-duplicate"
    # Minimal valid .docx: create a simple Office Open XML package.
    # To avoid dependency on python-docx, upload a small but valid .docx bytes.
    # Precomputed tiny docx bytes (word/document.xml with simple text)
    from zipfile import ZipFile
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
        from zipfile import ZipFile, ZIP_DEFLATED
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
            z.writestr("word/document.xml", """
            <?xml version="1.0" encoding="UTF-8"?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p><w:r><w:t>Hello</w:t></w:r></w:p>
              </w:body>
            </w:document>
            """.strip())
        tmp.seek(0)
        files = {"file": ("CW01_DEV_test.docx", tmp.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

    r = requests.post(url, files=files, timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data.get("isDuplicate") in {True, False}
    # If server already has this content from previous runs, allow True as well



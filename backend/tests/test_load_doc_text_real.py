import os
import pytest

from app.llm_parser import _load_doc_text


def test__load_doc_text_with_real_upload_and_prints_output():
    docx_path = "/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx"
    if not os.path.exists(docx_path):
        pytest.skip(f"Missing test file: {docx_path}")

    text = _load_doc_text(docx_path)

    # Print for visibility when running with -s
    print(text)

    assert isinstance(text, str)
    assert text.strip() != ""


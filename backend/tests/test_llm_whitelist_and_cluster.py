from unittest.mock import patch
from unittest import mock
import json


def _mock_choice(rows):
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({"rows": rows})
                }
            }
        ]
    }


@patch("app.llm_parser._load_db_kb", return_value=(
    ["Divor PV1", "Divor PV2", "Tordesillas A2"],
    {"Cluster Madrid": ["Divor PV1", "Divor PV2"]},
))
@patch("app.llm_parser._load_doc_text", return_value="Some section text mentioning Divor PV1 and unrelated names.")
@patch("app.llm_parser._detect_whitelist_candidates", return_value=(["Divor PV1"], []))
@patch("app.llm_parser._azure_chat_completion")
def test_whitelist_filters_llm_rows(mock_chat, _mock_detect, _mock_load_text, _mock_kb):
    from app.llm_parser import extract_rows_from_docx

    mock_chat.return_value = _mock_choice([
        {"project_name": "Divor PV1", "summary": "ok", "category": "Development"},
        {"project_name": "Fake Project", "summary": "should be filtered", "category": "Development"},
    ])

    with mock.patch.dict("os.environ", {"LLM_DB_WHITELIST": "1"}, clear=False):
        rows = extract_rows_from_docx("/tmp/x.docx", "CW01", "Development")

    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["project_name"] == "Divor PV1"


@patch("app.llm_parser._load_db_kb", return_value=(
    ["Divor PV1", "Divor PV2", "Tordesillas A2"],
    {"Cluster Madrid": ["Divor PV1", "Divor PV2"]},
))
@patch("app.llm_parser._load_doc_text", return_value="General update for Cluster Madrid: activities continue across sites.")
@patch("app.llm_parser._detect_whitelist_candidates", return_value=([], ["Cluster Madrid"]))
@patch("app.llm_parser._azure_chat_completion", return_value=_mock_choice([]))
def test_cluster_only_expands_to_all_members(mock_chat, _mock_detect, _mock_load_text, _mock_kb):
    from app.llm_parser import extract_rows_from_docx

    rows = extract_rows_from_docx("/tmp/x.docx", "CW02", "EPC")

    names = {r["project_name"] for r in rows}
    assert names == {"Divor PV1", "Divor PV2"}
    # Ensure source_text is populated from section
    for r in rows:
        assert r["source_text"] and "Cluster Madrid" in r["source_text"]



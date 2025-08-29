"""
Unit tests for llm_parser.extract_rows_from_docx function
Uses mocked Azure OpenAI responses to test parsing logic independently
"""
import pytest
from unittest.mock import patch, mock_open, Mock
import json
import tempfile
import os
from pathlib import Path

from app.llm_parser import extract_rows_from_docx, _load_doc_text, _azure_chat_completion


class TestExtractRowsFromDocx:
    """Test extract_rows_from_docx with various mocked Azure OpenAI responses"""

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_valid_json_array(self, mock_load_text, mock_azure):
        """Test successful extraction with direct JSON array response"""
        # Arrange
        mock_load_text.return_value = "Sample project text content"
        mock_azure.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "project_name": "Project Alpha",
                            "title": "Weekly Update",
                            "summary": "Made progress on task A",
                            "next_actions": "Complete task B",
                            "owner": "John Doe",
                            "category": "Development",
                            "source_text": "Original text about Project Alpha"
                        },
                        {
                            "project_name": "Project Beta",
                            "title": None,
                            "summary": "Reviewed requirements",
                            "next_actions": None,
                            "owner": "Jane Smith",
                            "category": "EPC",
                            "source_text": "Original text about Project Beta"
                        }
                    ])
                }
            }]
        }

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW01", "Development")

        # Assert
        assert len(result) == 2
        assert result[0]["project_name"] == "Project Alpha"
        assert result[0]["title"] == "Weekly Update"
        assert result[0]["summary"] == "Made progress on task A"
        assert result[0]["category"] == "Development"
        assert result[1]["project_name"] == "Project Beta"
        assert result[1]["title"] is None
        assert result[1]["category"] == "EPC"

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_wrapped_json_object(self, mock_load_text, mock_azure):
        """Test extraction when LLM returns {"rows": [...]} format"""
        # Arrange
        mock_load_text.return_value = "Sample text"
        mock_azure.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "rows": [
                            {
                                "project_name": "Test Project",
                                "summary": "Test summary",
                                "category": "Finance"
                            }
                        ]
                    })
                }
            }]
        }

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW02", "Finance")

        # Assert
        assert len(result) == 1
        assert result[0]["project_name"] == "Test Project"
        assert result[0]["summary"] == "Test summary"
        assert result[0]["category"] == "Finance"

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_malformed_json_with_fallback(self, mock_load_text, mock_azure):
        """Test extraction with malformed JSON that can be extracted via regex"""
        # Arrange
        mock_load_text.return_value = "Sample text"
        mock_azure.return_value = {
            "choices": [{
                "message": {
                    "content": 'Some text before [{"project_name": "Extracted", "summary": "Found it"}] and after'
                }
            }]
        }

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW03", "EPC")

        # Assert
        assert len(result) == 1
        assert result[0]["project_name"] == "Extracted"
        assert result[0]["summary"] == "Found it"

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_retry_on_bad_response(self, mock_load_text, mock_azure):
        """Test retry logic when first response is invalid, second succeeds"""
        # Arrange
        mock_load_text.return_value = "Sample text"
        mock_azure.side_effect = [
            {"choices": [{"message": {"content": "Invalid JSON response"}}]},  # First call fails
            {"choices": [{"message": {"content": '[{"project_name": "Retry Success", "summary": "Worked on retry"}]'}}]}  # Second succeeds
        ]

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW04", "Investment")

        # Assert
        assert len(result) == 1
        assert result[0]["project_name"] == "Retry Success"
        assert result[0]["summary"] == "Worked on retry"
        assert mock_azure.call_count == 2

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_empty_response_fallback(self, mock_load_text, mock_azure):
        """Test fallback to empty list when all retry attempts fail"""
        # Arrange
        mock_load_text.return_value = "Sample text"
        mock_azure.return_value = {
            "choices": [{"message": {"content": "No valid JSON here"}}]
        }

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW05", "Development")

        # Assert
        assert result == []
        assert mock_azure.call_count == 3  # Should try all 3 strategies

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_field_normalization(self, mock_load_text, mock_azure):
        """Test that fields are properly normalized and cleaned"""
        # Arrange
        mock_load_text.return_value = "Sample text"
        mock_azure.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "project_name": "  Whitespace Project  ",  # Should be stripped
                            "summary": "  Summary with spaces  ",    # Should be stripped
                            "category": "",                          # Should become None
                            "title": "",                            # Should stay as empty string
                            "owner": None,                          # Should stay None
                            "next_actions": "Valid action"
                        }
                    ])
                }
            }]
        }

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW06", "Development")

        # Assert
        assert len(result) == 1
        row = result[0]
        assert row["project_name"] == "Whitespace Project"  # Stripped
        assert row["summary"] == "Summary with spaces"      # Stripped
        assert row["category"] is None                      # Empty string converted to None
        assert row["title"] == ""                          # Empty string preserved
        assert row["owner"] is None                        # None preserved
        assert row["next_actions"] == "Valid action"

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_filters_invalid_entries(self, mock_load_text, mock_azure):
        """Test that non-dict entries in the array are filtered out"""
        # Arrange
        mock_load_text.return_value = "Sample text"
        mock_azure.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {"project_name": "Valid Project", "summary": "Valid summary"},
                        "invalid string entry",  # Should be filtered out
                        123,                     # Should be filtered out
                        {"project_name": "Another Valid", "summary": "Another summary"}
                    ])
                }
            }]
        }

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW07", "EPC")

        # Assert
        assert len(result) == 2
        assert result[0]["project_name"] == "Valid Project"
        assert result[1]["project_name"] == "Another Valid"

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_handles_missing_fields(self, mock_load_text, mock_azure):
        """Test extraction with minimal/missing fields"""
        # Arrange
        mock_load_text.return_value = "Sample text"
        mock_azure.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "project_name": "Minimal Project"
                            # Missing all other fields
                        }
                    ])
                }
            }]
        }

        # Act
        result = extract_rows_from_docx("/fake/path.docx", "CW08", "Finance")

        # Assert
        assert len(result) == 1
        row = result[0]
        assert row["project_name"] == "Minimal Project"
        assert row["title"] is None
        assert row["summary"] == ""  # Missing summary becomes empty string
        assert row["next_actions"] is None
        assert row["owner"] is None
        assert row["category"] is None
        assert row["source_text"] is None


class TestLoadDocText:
    """Test the _load_doc_text helper function"""

    def test_load_doc_text_with_real_docx(self):
        """Test loading text from a real DOCX file"""
        # This test requires a real DOCX file - we'll use one from uploads
        docx_path = "/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx"
        if not os.path.exists(docx_path):
            pytest.skip("Test DOCX file not available")

        # Act
        text = _load_doc_text(docx_path)

        # Assert
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Development" in text or "Project" in text  # Should contain project-related content


class TestAzureChatCompletion:
    """Test the _azure_chat_completion helper function"""

    def test_azure_chat_completion_missing_env_vars(self):
        """Test that missing environment variables raise RuntimeError"""
        # Arrange
        with patch.dict(os.environ, {}, clear=True):
            messages = [{"role": "user", "content": "test"}]

            # Act & Assert
            with pytest.raises(RuntimeError, match="Azure OpenAI env vars missing"):
                _azure_chat_completion(messages)

    @patch('httpx.Client')
    def test_azure_chat_completion_success(self, mock_client):
        """Test successful Azure OpenAI API call"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "test response"}}]}
        mock_response.raise_for_status.return_value = None
        
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.post.return_value = mock_response
        mock_client.return_value = mock_context

        messages = [{"role": "user", "content": "test"}]

        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment"
        }):
            # Act
            result = _azure_chat_completion(messages)

            # Assert
            assert result == {"choices": [{"message": {"content": "test response"}}]}
            mock_context.post.assert_called_once()

    @patch('httpx.Client')
    def test_azure_chat_completion_http_error(self, mock_client):
        """Test that HTTP errors are properly raised"""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.post.return_value = mock_response
        mock_client.return_value = mock_context

        messages = [{"role": "user", "content": "test"}]

        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment"
        }):
            # Act & Assert
            with pytest.raises(Exception, match="HTTP Error"):
                _azure_chat_completion(messages)

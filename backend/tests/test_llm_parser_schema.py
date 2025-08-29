"""
Tests for LLM parser with strict JSON schema validation
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.schemas import ExtractionResponse, ProjectEntry, CategoryEnum
from app.llm_parser import extract_rows_from_docx, _azure_chat_completion


class TestSchemaValidation:
    """Test Pydantic schema validation"""
    
    def test_valid_project_entry(self):
        """Test valid project entry creation"""
        entry_data = {
            "project_name": "Test Project",
            "title": "Test Title",
            "summary": "Test summary with content",
            "next_actions": "Next steps",
            "owner": "John Doe",
            "category": "Development",
            "source_text": "Original text"
        }
        
        entry = ProjectEntry(**entry_data)
        assert entry.project_name == "Test Project"
        assert entry.category == CategoryEnum.DEVELOPMENT
        assert entry.summary == "Test summary with content"
    
    def test_project_entry_with_minimal_fields(self):
        """Test project entry with only required fields"""
        entry_data = {
            "project_name": "Minimal Project",
            "summary": "Basic summary"
        }
        
        entry = ProjectEntry(**entry_data)
        assert entry.project_name == "Minimal Project"
        assert entry.summary == "Basic summary"
        assert entry.title is None
        assert entry.category is None
    
    def test_project_entry_validation_errors(self):
        """Test validation errors for invalid data"""
        # Empty project name
        with pytest.raises(ValidationError) as exc_info:
            ProjectEntry(project_name="", summary="Test")
        assert "project_name cannot be empty" in str(exc_info.value)
        
        # Missing project name entirely
        with pytest.raises(ValidationError):
            ProjectEntry(summary="Test summary")
        
        # Invalid category
        with pytest.raises(ValidationError):
            ProjectEntry(project_name="Test", summary="Test", category="InvalidCategory")
    
    def test_extraction_response_validation(self):
        """Test full response validation"""
        response_data = {
            "rows": [
                {
                    "project_name": "Project A",
                    "summary": "Summary A",
                    "category": "EPC"
                },
                {
                    "project_name": "Project B", 
                    "summary": "Summary B",
                    "category": "Finance"
                }
            ]
        }
        
        response = ExtractionResponse(**response_data)
        assert len(response.rows) == 2
        assert response.rows[0].category == CategoryEnum.EPC
        assert response.rows[1].category == CategoryEnum.FINANCE


class TestAzureChatCompletion:
    """Test Azure OpenAI chat completion with JSON mode"""
    
    @patch('app.llm_parser.httpx.Client')
    @patch('app.llm_parser.os.getenv')
    def test_json_mode_request(self, mock_getenv, mock_client):
        """Test request with JSON mode enabled"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
            "AZURE_OPENAI_MAX_CONTEXT": "8000",
            "AZURE_OPENAI_MAX_INPUT": "3500",
            "AZURE_OPENAI_MAX_OUTPUT": "4000",
            "AZURE_OPENAI_SAFETY_BUFFER": "500"
        }.get(key, default)
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"rows": [{"project_name": "Test", "summary": "Test summary"}]}'
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        messages = [{"role": "user", "content": "test"}]
        
        # Test with JSON mode
        result = _azure_chat_completion(messages, use_json_mode=True)
        
        # Verify the request payload includes response_format
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]['json']
        assert payload['response_format'] == {"type": "json_object"}
        assert result == mock_response.json.return_value
    
    @patch('app.llm_parser.httpx.Client')
    @patch('app.llm_parser.os.getenv')
    def test_function_calling_request(self, mock_getenv, mock_client):
        """Test request with function calling enabled"""
        # Mock environment variables
        mock_getenv.side_effect = lambda key, default=None: {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
            "AZURE_OPENAI_MAX_CONTEXT": "8000",
            "AZURE_OPENAI_MAX_INPUT": "3500",
            "AZURE_OPENAI_MAX_OUTPUT": "4000",
            "AZURE_OPENAI_SAFETY_BUFFER": "500"
        }.get(key, default)
        
        # Mock HTTP response with function call
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "function_call": {
                        "name": "extract_project_entries",
                        "arguments": '{"rows": [{"project_name": "Test", "summary": "Test summary"}]}'
                    }
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        messages = [{"role": "user", "content": "test"}]
        
        # Test with function calling
        result = _azure_chat_completion(messages, use_function_calling=True)
        
        # Verify the request payload includes functions
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]['json']
        assert 'functions' in payload
        assert payload['function_call'] == {"name": "extract_project_entries"}


class TestExtractRowsFromDocx:
    """Test the main extraction function with mocked Azure calls"""
    
    @patch('app.llm_parser._load_doc_text')
    @patch('app.llm_parser._azure_chat_completion')
    def test_successful_extraction_with_json_mode(self, mock_azure_call, mock_load_text):
        """Test successful extraction using JSON mode"""
        # Mock document text
        mock_load_text.return_value = "Test document content with project information"
        
        # Mock Azure response with valid JSON
        mock_azure_call.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "rows": [
                            {
                                "project_name": "Test Project 1",
                                "title": "Project Update",
                                "summary": "Project is progressing well",
                                "next_actions": "Continue development",
                                "owner": "John Doe",
                                "category": "Development",
                                "source_text": "Original text from document"
                            },
                            {
                                "project_name": "Test Project 2",
                                "summary": "Another project update",
                                "category": "EPC"
                            }
                        ]
                    })
                }
            }]
        }
        
        result = extract_rows_from_docx("test.docx", "CW01", "Development")
        
        assert len(result) == 2
        assert result[0]["project_name"] == "Test Project 1"
        assert result[0]["category"] == "Development"
        assert result[1]["project_name"] == "Test Project 2"
        assert result[1]["category"] == "EPC"
    
    @patch('app.llm_parser._load_doc_text')
    @patch('app.llm_parser._azure_chat_completion')
    def test_extraction_with_validation_error(self, mock_azure_call, mock_load_text):
        """Test handling of validation errors - invalid entries are filtered out"""
        mock_load_text.return_value = "Test document content"
        
        # Mock Azure response with mixed valid and invalid data
        mock_azure_call.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "rows": [
                            {
                                "project_name": "",  # Invalid: empty name - will be filtered
                                "summary": "Test summary"
                            },
                            {
                                "project_name": "Valid Project",  # Valid entry
                                "summary": "Valid summary",
                                "category": "Finance"
                            }
                        ]
                    })
                }
            }]
        }
        
        result = extract_rows_from_docx("test.docx", "CW01", "Development")
        
        # Should filter out invalid entry and keep valid one
        assert len(result) == 1
        assert result[0]["project_name"] == "Valid Project"
        assert result[0]["category"] == "Finance"
    
    @patch('app.llm_parser._load_doc_text')
    @patch('app.llm_parser._azure_chat_completion')
    def test_extraction_all_attempts_fail(self, mock_azure_call, mock_load_text):
        """Test when all extraction attempts fail"""
        mock_load_text.return_value = "Test document content"
        
        # Mock all attempts returning invalid JSON
        mock_azure_call.return_value = {
            "choices": [{
                "message": {
                    "content": "Invalid JSON response"
                }
            }]
        }
        
        result = extract_rows_from_docx("test.docx", "CW01", "Development")
        
        assert result == []
        # Verify all three strategies were attempted
        assert mock_azure_call.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])

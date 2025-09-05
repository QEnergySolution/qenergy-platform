"""
Tests for token limit management in llm_parser
"""
import pytest
import os
from unittest.mock import patch

from app.llm_parser import (
    _estimate_tokens, 
    _get_token_limits, 
    _safe_truncate_text,
    extract_rows_from_docx
)


class TestTokenEstimation:
    """Test token estimation functions"""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation"""
        # Simple cases
        assert _estimate_tokens("") == 0
        assert _estimate_tokens("word") == 1  # 4 chars = 1 token
        assert _estimate_tokens("four") == 1  # exactly 4 chars
        assert _estimate_tokens("hello") == 1  # 5 chars = 1 token (rounded down)
        assert _estimate_tokens("hello world") == 2  # 11 chars = 2 tokens
        
    def test_estimate_tokens_longer_text(self):
        """Test token estimation with longer text"""
        # 100 characters should be ~25 tokens
        text_100 = "a" * 100
        assert _estimate_tokens(text_100) == 25
        
        # 1000 characters should be ~250 tokens
        text_1000 = "test " * 200  # 1000 chars
        assert _estimate_tokens(text_1000) == 250


class TestTokenLimits:
    """Test token limit configuration"""

    def test_get_token_limits_defaults(self):
        """Test default token limits"""
        with patch.dict(os.environ, {}, clear=True):
            limits = _get_token_limits()
            
            assert limits["max_context"] == 8000
            assert limits["max_input"] == 3500
            assert limits["max_output"] == 4000
            assert limits["safety_buffer"] == 500

    def test_get_token_limits_custom(self):
        """Test custom token limits from environment"""
        custom_env = {
            "AZURE_OPENAI_MAX_CONTEXT": "16000",
            "AZURE_OPENAI_MAX_INPUT": "7000", 
            "AZURE_OPENAI_MAX_OUTPUT": "8000",
            "AZURE_OPENAI_SAFETY_BUFFER": "1000"
        }
        
        with patch.dict(os.environ, custom_env):
            limits = _get_token_limits()
            
            assert limits["max_context"] == 16000
            assert limits["max_input"] == 7000
            assert limits["max_output"] == 8000
            assert limits["safety_buffer"] == 1000


class TestSafeTruncation:
    """Test safe text truncation"""

    def test_safe_truncate_short_text(self):
        """Test that short text is not truncated"""
        short_text = "This is a short text."
        result = _safe_truncate_text(short_text, max_tokens=100)
        assert result == short_text

    def test_safe_truncate_long_text(self):
        """Test truncation of long text"""
        # Create text that's definitely longer than limit
        long_text = "This is a sentence. " * 1000  # ~20,000 chars
        result = _safe_truncate_text(long_text, max_tokens=100)  # ~400 char limit
        
        assert len(result) < len(long_text)
        assert len(result) <= 400 * 1.1  # Allow some tolerance
        assert _estimate_tokens(result) <= 100

    def test_safe_truncate_preserves_sentences(self):
        """Test that truncation preserves sentence boundaries"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = _safe_truncate_text(text, max_tokens=10)  # Force truncation
        
        # Should end with a period if truncated at sentence boundary
        if len(result) < len(text):
            assert result.endswith('.') or result.endswith('!') or result.endswith('?')

    def test_safe_truncate_preserves_paragraphs(self):
        """Test that truncation prefers paragraph boundaries"""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = _safe_truncate_text(text, max_tokens=5)  # Force truncation
        
        # Should prefer to end at paragraph breaks
        if len(result) < len(text) and '\n\n' in result:
            # If we have paragraph breaks, should end at one
            lines = result.split('\n\n')
            # Last part should be complete (not cut off mid-sentence)
            assert len(lines[-1].strip()) == 0 or lines[-1].endswith('.')

    def test_safe_truncate_word_boundaries(self):
        """Test that truncation preserves word boundaries as fallback"""
        text = "word1 word2 word3 word4 word5"
        result = _safe_truncate_text(text, max_tokens=3)  # ~12 chars
        
        if len(result) < len(text):
            # Should end at word boundary (space) or be complete
            words_in_result = result.split()
            words_in_original = text.split()
            
            # All words in result should be complete words from original
            for word in words_in_result:
                assert word in words_in_original
            
            # Should not cut off in middle of a word
            if not result.endswith(' '):
                assert result.split()[-1] in words_in_original

    def test_safe_truncate_uses_env_defaults(self):
        """Test that truncation uses environment defaults when max_tokens not specified"""
        with patch.dict(os.environ, {"AZURE_OPENAI_MAX_INPUT": "50"}):
            long_text = "word " * 100  # 500 chars
            result = _safe_truncate_text(long_text)  # No max_tokens specified
            
            # Should use the env var (50 tokens = ~200 chars)
            assert len(result) <= 220  # Some tolerance for word boundaries


class TestIntegrationWithRealFile:
    """Test token limits with real file processing"""

    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_respects_token_limits(self, mock_load_text, mock_azure):
        """Test that extract_rows_from_docx respects token limits"""
        # Create a very long document
        very_long_text = "This is a long project report. " * 1000  # ~32,000 chars
        mock_load_text.return_value = very_long_text
        
        # Mock Azure response
        mock_azure.return_value = {
            "choices": [{"message": {"content": '[{"project_name": "Test", "summary": "Test"}]'}}]
        }
        
        # Call with default token limits
        result = extract_rows_from_docx("/fake/path.docx", "CW01", "Development")
        
        # Verify Azure was called with truncated text
        mock_azure.assert_called_once()
        call_args = mock_azure.call_args[0][0]  # messages argument
        user_message = call_args[1]["content"]
        
        # The text should have been truncated (not the full 32,000 chars)
        assert len(user_message) < len(very_long_text)
        
        # Should still extract results
        assert len(result) == 1
        assert result[0]["project_name"] == "Test"

    @patch.dict(os.environ, {"AZURE_OPENAI_MAX_INPUT": "100"})  # Very small limit
    @patch('app.llm_parser._azure_chat_completion')
    @patch('app.llm_parser._load_doc_text')
    def test_extract_rows_with_custom_limits(self, mock_load_text, mock_azure):
        """Test that custom environment limits are respected"""
        long_text = "Project information here. " * 200  # ~5000 chars
        mock_load_text.return_value = long_text
        
        mock_azure.return_value = {
            "choices": [{"message": {"content": '[{"project_name": "Limited", "summary": "Test"}]'}}]
        }
        
        result = extract_rows_from_docx("/fake/path.docx", "CW01", "Development")
        
        # Verify text was heavily truncated due to small limit
        call_args = mock_azure.call_args[0][0]
        user_message = call_args[1]["content"]
        
        # With 100 token limit, should be ~400 chars max
        # Note: user_message includes prompt + truncated text, so be more lenient
        assert len(user_message) <= 700  # Includes prompt overhead, be more tolerant
        
        assert len(result) == 1
        assert result[0]["project_name"] == "Limited"

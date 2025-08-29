"""
Integration tests for llm_parser.extract_rows_from_docx with real Azure OpenAI
Guarded by AZURE_OPENAI_INTEGRATION_TEST environment variable
"""
import pytest
import os
from typing import List, Dict

from app.llm_parser import extract_rows_from_docx


class TestExtractRowsIntegration:
    """Integration tests using real Azure OpenAI API"""

    @pytest.mark.skipif(
        os.getenv("AZURE_OPENAI_INTEGRATION_TEST") != "1",
        reason="Set AZURE_OPENAI_INTEGRATION_TEST=1 to run integration tests"
    )
    def test_extract_rows_real_azure_openai(self):
        """Test extract_rows_from_docx with real Azure OpenAI API call"""
        # Arrange
        docx_path = "/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx"
        if not os.path.exists(docx_path):
            pytest.skip("Test DOCX file not available")

        # Check required environment variables
        required_env_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT", 
            "AZURE_OPENAI_DEPLOYMENT"
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            pytest.skip(f"Missing environment variables: {missing_vars}")

        # Act
        result = extract_rows_from_docx(docx_path, "CW01", "Development")

        # Assert
        assert isinstance(result, list)
        print(f"Azure OpenAI returned {len(result)} rows")
        
        # If we got results, validate their structure
        if result:
            for i, row in enumerate(result):
                print(f"Row {i}: {row}")
                assert isinstance(row, dict)
                assert "project_name" in row
                assert "summary" in row
                # project_name should not be empty if present
                if row.get("project_name"):
                    assert isinstance(row["project_name"], str)
                    assert len(row["project_name"].strip()) > 0
                # summary should be a string (may be empty)
                assert isinstance(row["summary"], str)
                # category should be None or valid value
                if row.get("category"):
                    assert row["category"] in ["Development", "EPC", "Finance", "Investment"]

    @pytest.mark.skipif(
        os.getenv("AZURE_OPENAI_INTEGRATION_TEST") != "1",
        reason="Set AZURE_OPENAI_INTEGRATION_TEST=1 to run integration tests"
    )
    def test_extract_rows_different_categories(self):
        """Test extraction with different category hints from filename"""
        # Arrange
        test_files = [
            ("uploads/2025_CW01_DEV.docx", "Development"),
            ("uploads/2025_CW01_EPC.docx", "EPC"),
            ("uploads/2025_CW01_FINANCE.docx", "Finance"),
            ("uploads/2025_CW01_INVESTMENT.docx", "Investment")
        ]
        
        base_path = "/Users/yuxin.xue/Projects/qenergy-platform"
        
        for relative_path, expected_category in test_files:
            full_path = os.path.join(base_path, relative_path)
            if not os.path.exists(full_path):
                print(f"Skipping {relative_path} - file not found")
                continue

            # Act
            result = extract_rows_from_docx(full_path, "CW01", expected_category)

            # Assert
            assert isinstance(result, list)
            print(f"File {relative_path} ({expected_category}): {len(result)} rows extracted")
            
            # Log first row for inspection
            if result:
                print(f"  First row: {result[0]}")

    @pytest.mark.skipif(
        os.getenv("AZURE_OPENAI_INTEGRATION_TEST") != "1",
        reason="Set AZURE_OPENAI_INTEGRATION_TEST=1 to run integration tests"
    )
    def test_extract_rows_empty_or_minimal_docx(self):
        """Test behavior with minimal content DOCX (should not crash)"""
        # This test would require a minimal/empty DOCX file
        # For now, we'll test that the function handles non-existent files gracefully
        
        # Test with non-existent file should raise an exception
        with pytest.raises(Exception):  # Could be FileNotFoundError or docx-related error
            extract_rows_from_docx("/nonexistent/path.docx", "CW01", "Development")

    @pytest.mark.skipif(
        os.getenv("AZURE_OPENAI_INTEGRATION_TEST") != "1", 
        reason="Set AZURE_OPENAI_INTEGRATION_TEST=1 to run integration tests"
    )
    def test_extract_rows_consistency(self):
        """Test that multiple calls to the same file return consistent results"""
        # Arrange
        docx_path = "/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx"
        if not os.path.exists(docx_path):
            pytest.skip("Test DOCX file not available")

        # Act - call twice
        result1 = extract_rows_from_docx(docx_path, "CW01", "Development")
        result2 = extract_rows_from_docx(docx_path, "CW01", "Development")

        # Assert
        assert isinstance(result1, list)
        assert isinstance(result2, list)
        
        # Results should have same number of entries (may vary slightly due to LLM randomness)
        # Allow for some variation but they should be in same ballpark
        if result1 and result2:
            ratio = len(result2) / len(result1)
            assert 0.5 <= ratio <= 2.0, f"Results too different: {len(result1)} vs {len(result2)} rows"
            
        print(f"Consistency check: {len(result1)} vs {len(result2)} rows")


class TestLLMParserErrorHandling:
    """Test error handling in LLM parser functions"""

    def test_extract_rows_missing_env_vars(self):
        """Test that missing Azure OpenAI env vars are handled gracefully"""
        # Arrange - temporarily clear environment variables and use valid file path
        original_env = {}
        env_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
        
        for var in env_vars:
            original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        # Use a real file path so docx loading doesn't fail first
        valid_docx_path = "/Users/yuxin.xue/Projects/qenergy-platform/uploads/2025_CW01_DEV.docx"
        if not os.path.exists(valid_docx_path):
            pytest.skip("Valid DOCX file needed for this test")

        try:
            # Act & Assert
            with pytest.raises(RuntimeError, match="Azure OpenAI env vars missing"):
                extract_rows_from_docx(valid_docx_path, "CW01", "Development")
        finally:
            # Restore environment variables
            for var, value in original_env.items():
                if value is not None:
                    os.environ[var] = value

    def test_extract_rows_invalid_file_path(self):
        """Test behavior with invalid file path"""
        # This should raise an exception before reaching Azure API
        with pytest.raises(Exception):  # FileNotFoundError or similar
            extract_rows_from_docx("/definitely/nonexistent/path.docx", "CW01", "Development")

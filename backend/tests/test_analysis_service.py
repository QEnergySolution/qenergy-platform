import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.analysis_service import AnalysisService
from app.models.project_history import ProjectHistory
from app.models.project import Project
from app.models.weekly_report_analysis import WeeklyReportAnalysis


class TestAnalysisService:
    @pytest.fixture
    def analysis_service(self):
        return AnalysisService()

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_get_projects_by_cw_pair(self, analysis_service, mock_db):
        """Test getting candidate projects by CW pair"""
        # Mock database query results
        mock_history_records = [
            Mock(
                project_code="TEST001",
                category="EPC",
                cw_label="CW31"
            ),
            Mock(
                project_code="TEST001",
                category="EPC", 
                cw_label="CW32"
            ),
            Mock(
                project_code="TEST002",
                category="Finance",
                cw_label="CW31"
            )
        ]
        
        mock_projects = [
            Mock(project_code="TEST001", project_name="Test Project 1"),
            Mock(project_code="TEST002", project_name="Test Project 2")
        ]
        
        # Configure mock queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_history_records
        mock_db.query.return_value = mock_query
        
        # Mock project query
        mock_project_query = Mock()
        mock_project_query.filter.return_value = mock_project_query
        mock_project_query.all.return_value = mock_projects
        
        # Configure db.query to return different mocks based on the model
        def query_side_effect(model):
            if model == ProjectHistory:
                return mock_query
            elif model == Project:
                return mock_project_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # Test the method
        result = analysis_service.get_projects_by_cw_pair(mock_db, "CW31", "CW32")
        
        # Verify results
        assert len(result) == 2
        assert result[0]["project_code"] == "TEST001"
        assert result[0]["project_name"] == "Test Project 1"
        assert "EPC" in result[0]["categories"]
        assert "CW31" in result[0]["cw_labels"]
        assert "CW32" in result[0]["cw_labels"]

    def test_get_project_content_for_cw(self, analysis_service, mock_db):
        """Test getting project content for a specific CW"""
        mock_records = [
            Mock(
                title="Weekly Update",
                summary="Project is on track",
                next_actions="Continue development"
            ),
            Mock(
                title="Risk Assessment",
                summary="Low risk identified",
                next_actions=None
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_records
        mock_db.query.return_value = mock_query
        
        result = analysis_service.get_project_content_for_cw(
            mock_db, "TEST001", "CW32", "EPC"
        )
        
        assert "Weekly Update" in result
        assert "Project is on track" in result
        assert "Continue development" in result
        assert "Risk Assessment" in result
        assert "Low risk identified" in result

    def test_detect_language(self, analysis_service):
        """Test language detection"""
        # English text
        english_text = "This is a project status report with updates"
        assert analysis_service.detect_language(english_text) == "EN"
        
        # Korean text (mock with Korean characters)
        korean_text = "프로젝트 상태 보고서입니다"
        assert analysis_service.detect_language(korean_text) == "KO"
        
        # Empty text
        assert analysis_service.detect_language("") == "EN"

    def test_extract_negative_words(self, analysis_service):
        """Test negative word extraction"""
        text = "The project has significant delays and critical issues causing concerns"
        
        negative_words = analysis_service.extract_negative_words(text, "EN")
        
        assert "delays" in negative_words
        assert "critical" in negative_words
        assert "issues" in negative_words
        assert "concerns" in negative_words

    def test_calculate_similarity(self, analysis_service):
        """Test content similarity calculation"""
        past_content = "Project is progressing well with minor issues"
        latest_content = "Project is progressing well with some delays"
        
        similarity = analysis_service.calculate_similarity(past_content, latest_content)
        
        assert 0 <= similarity <= 100
        assert similarity > 50  # Should have reasonable similarity
        
        # Test identical content
        identical_similarity = analysis_service.calculate_similarity(past_content, past_content)
        assert identical_similarity == 100
        
        # Test completely different content
        different_similarity = analysis_service.calculate_similarity(
            "Project A status", "Completely different topic"
        )
        assert different_similarity < 50

    @pytest.mark.asyncio
    async def test_get_llm_analysis_fallback(self, analysis_service):
        """Test LLM analysis fallback when Azure is not configured"""
        # Clear Azure configuration to trigger fallback
        analysis_service.azure_api_key = None
        analysis_service.azure_endpoint = None
        
        past_content = "Project is going well"
        latest_content = "Project has some delays and issues"
        
        result = await analysis_service.get_llm_analysis(
            past_content, latest_content, "EN", "TEST001"
        )
        
        assert "risk_lvl" in result
        assert "risk_desc" in result
        assert "similarity_lvl" in result
        assert "similarity_desc" in result
        assert 0 <= result["risk_lvl"] <= 100
        assert 0 <= result["similarity_lvl"] <= 100

    @pytest.mark.asyncio 
    async def test_analyze_project_pair_new_analysis(self, analysis_service, mock_db):
        """Test analyzing a new project pair"""
        # Mock no existing analysis
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Mock project content
        with patch.object(analysis_service, 'get_project_content_for_cw') as mock_get_content:
            mock_get_content.side_effect = [
                "Past project content",
                "Latest project content with issues"
            ]
            
            # Mock LLM analysis
            with patch.object(analysis_service, 'get_llm_analysis') as mock_llm:
                mock_llm.return_value = {
                    "risk_lvl": 60.0,
                    "risk_desc": "Medium risk detected",
                    "similarity_lvl": 40.0,
                    "similarity_desc": "Content has changed significantly"
                }
                
                # Mock database operations
                mock_new_analysis = Mock()
                mock_new_analysis.id = "test-id"
                mock_new_analysis.project_code = "TEST001"
                mock_new_analysis.cw_label = "CW32"
                mock_new_analysis.language = "EN"
                mock_new_analysis.category = "EPC"
                mock_new_analysis.risk_lvl = 60.0
                mock_new_analysis.risk_desc = "Medium risk detected"
                mock_new_analysis.similarity_lvl = 40.0
                mock_new_analysis.similarity_desc = "Content has changed significantly"
                mock_new_analysis.negative_words = {"words": ["issues"], "count": 1}
                mock_new_analysis.created_at = "2024-01-01T00:00:00Z"
                mock_new_analysis.created_by = "test-user"
                
                mock_db.add.return_value = None
                mock_db.commit.return_value = None
                mock_db.refresh.return_value = None
                mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 'test-id')
                
                # Execute test
                result, was_created = await analysis_service.analyze_project_pair(
                    db=mock_db,
                    project_code="TEST001",
                    past_cw="CW31",
                    latest_cw="CW32",
                    language="EN",
                    category="EPC",
                    created_by="test-user"
                )
                
                # Verify result
                assert was_created is True
                assert result.project_code == "TEST001"
                assert result.risk_lvl == 60.0
                assert result.similarity_lvl == 40.0

    def test_get_analysis_results(self, analysis_service, mock_db):
        """Test getting existing analysis results"""
        mock_analysis = Mock()
        mock_analysis.id = "test-id"
        mock_analysis.project_code = "TEST001"
        mock_analysis.cw_label = "CW32"
        mock_analysis.language = "EN"
        mock_analysis.category = "EPC"
        mock_analysis.risk_lvl = 50.0
        mock_analysis.risk_desc = "Medium risk"
        mock_analysis.similarity_lvl = 75.0
        mock_analysis.similarity_desc = "Similar content"
        mock_analysis.negative_words = {"words": ["delay"], "count": 1}
        mock_analysis.created_at = "2024-01-01T00:00:00Z"
        mock_analysis.created_by = "test-user"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_analysis]
        mock_db.query.return_value = mock_query
        
        results = analysis_service.get_analysis_results(
            mock_db, "CW31", "CW32", "EN", "EPC"
        )
        
        assert len(results) == 1
        assert results[0].project_code == "TEST001"
        assert results[0].risk_lvl == 50.0
        assert results[0].similarity_lvl == 75.0

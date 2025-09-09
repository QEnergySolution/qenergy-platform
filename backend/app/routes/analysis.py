from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    WeeklyReportAnalysisRead,
    Language,
    Category
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisResponse)
async def analyze_reports(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze reports between two calendar weeks.
    """
    # This is a mock implementation - in a real system, you would:
    # 1. Fetch the reports for the specified calendar weeks
    # 2. Analyze them using LLM or other methods
    # 3. Store the results in the database
    # 4. Return the analysis results
    
    # For now, we'll return a mock response
    mock_results = []
    for i in range(1, 6):  # Mock 5 results
        mock_results.append(
            WeeklyReportAnalysisRead(
                id=f"mock-id-{i}",
                project_code=f"2ES0000{i}",
                project_name=f"Mock Project {i}",
                cw_label=request.latest_cw,
                language=request.language,
                category=request.category,
                risk_lvl=50.0 + i * 5,
                risk_desc=f"This is a mock risk description for project {i}",
                similarity_lvl=70.0 - i * 5,
                similarity_desc=f"This is a mock similarity description for project {i}",
                negative_words={"words": ["delay", "issue", "problem"], "count": 3},
                past_content=f"Mock past content for project {i}",
                latest_content=f"Mock latest content for project {i}",
                created_at="2025-09-09T12:00:00Z",
                created_by=request.created_by
            )
        )
    
    return AnalysisResponse(
        message="Analysis completed successfully",
        analyzed_count=len(mock_results),
        skipped_count=0,
        results=mock_results
    )


@router.get("/weekly", response_model=List[WeeklyReportAnalysisRead])
async def get_analysis_results(
    past_cw: str = Query(..., description="Past calendar week (e.g., CW31)"),
    latest_cw: str = Query(..., description="Latest calendar week (e.g., CW32)"),
    language: Optional[Language] = Query(None, description="Language code"),
    category: Optional[Category] = Query(None, description="Report category"),
    db: Session = Depends(get_db)
):
    """
    Get existing analysis results for the specified calendar weeks.
    """
    # This is a mock implementation - in a real system, you would:
    # 1. Query the database for existing analysis results
    # 2. Filter by the specified parameters
    # 3. Return the results
    
    # For now, we'll return a mock response
    mock_results = []
    for i in range(1, 6):  # Mock 5 results
        mock_results.append(
            WeeklyReportAnalysisRead(
                id=f"mock-id-{i}",
                project_code=f"2ES0000{i}",
                project_name=f"Mock Project {i}",
                cw_label=latest_cw,
                language=language or "EN",
                category=category,
                risk_lvl=50.0 + i * 5,
                risk_desc=f"This is a mock risk description for project {i}",
                similarity_lvl=70.0 - i * 5,
                similarity_desc=f"This is a mock similarity description for project {i}",
                negative_words={"words": ["delay", "issue", "problem"], "count": 3},
                past_content=f"Mock past content for project {i}",
                latest_content=f"Mock latest content for project {i}",
                created_at="2025-09-09T12:00:00Z",
                created_by="system"
            )
        )
    
    return mock_results

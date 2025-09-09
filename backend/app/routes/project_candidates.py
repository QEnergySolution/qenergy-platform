from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.analysis import (
    ProjectCandidateResponse,
    Category
)

router = APIRouter(prefix="/project-candidates", tags=["projects"])


@router.get("", response_model=List[ProjectCandidateResponse])
async def get_project_candidates(
    past_cw: str = Query(..., description="Past calendar week (e.g., CW31)"),
    latest_cw: str = Query(..., description="Latest calendar week (e.g., CW32)"),
    category: Optional[Category] = Query(None, description="Report category"),
    db: Session = Depends(get_db)
):
    """
    Get project candidates that have reports in either of the specified calendar weeks.
    """
    # This is a mock implementation - in a real system, you would:
    # 1. Query the database for projects with reports in either calendar week
    # 2. Filter by the specified category if provided
    # 3. Return the project candidates
    
    # For now, we'll return a mock response
    mock_candidates = []
    for i in range(1, 11):  # Mock 10 candidates
        mock_candidates.append(
            ProjectCandidateResponse(
                project_code=f"2ES0000{i}",
                project_name=f"Mock Project {i}",
                categories=["Development", "EPC"] if i % 2 == 0 else ["Finance", "Investment"],
                cw_labels=[past_cw, latest_cw] if i % 3 == 0 else [latest_cw]
            )
        )
    
    # Filter by category if provided
    if category:
        mock_candidates = [c for c in mock_candidates if category in c.categories]
    
    return mock_candidates

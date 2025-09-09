from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.analysis import (
    ProjectCandidateResponse,
    Category,
)
from ..services.analysis_service import AnalysisService

router = APIRouter(prefix="/project-candidates", tags=["projects"])


@router.get("", response_model=List[ProjectCandidateResponse])
def get_project_candidates(
    past_cw: str = Query(..., description="Past calendar week (e.g., CW31)"),
    latest_cw: str = Query(..., description="Latest calendar week (e.g., CW32)"),
    category: Optional[Category] = Query(None, description="Report category"),
    db: Session = Depends(get_db)
):
    """Return real candidates from project history via AnalysisService."""
    service = AnalysisService()
    raw = service.get_projects_by_cw_pair(db, past_cw, latest_cw, category)
    return [
        ProjectCandidateResponse(
            project_code=item["project_code"],
            project_name=item.get("project_name"),
            categories=item.get("categories", []),
            cw_labels=item.get("cw_labels", []),
        )
        for item in raw
    ]

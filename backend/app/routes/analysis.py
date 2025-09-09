from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    WeeklyReportAnalysisRead,
    Language,
    Category,
)
from ..services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisResponse)
async def analyze_reports(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze all candidate projects between two CWs using real AnalysisService."""
    service = AnalysisService()

    candidates = service.get_projects_by_cw_pair(
        db=db,
        past_cw=request.past_cw,
        latest_cw=request.latest_cw,
        category=request.category,
    )

    analyzed: List[WeeklyReportAnalysisRead] = []
    analyzed_count = 0
    skipped_count = 0

    language: Language = request.language or "EN"  # type: ignore

    for c in candidates:
        project_code = c.get("project_code")
        if not project_code:
            skipped_count += 1
            continue
        result, was_created = await service.analyze_project_pair(
            db=db,
            project_code=project_code,
            past_cw=request.past_cw,
            latest_cw=request.latest_cw,
            language=language,
            category=request.category,
            created_by=request.created_by or "system",
        )
        analyzed.append(result)
        analyzed_count += 1 if was_created else 0

    return AnalysisResponse(
        message="Analysis completed",
        analyzed_count=analyzed_count,
        skipped_count=skipped_count,
        results=analyzed,
    )


@router.get("/weekly", response_model=List[WeeklyReportAnalysisRead])
def get_analysis_results(
    past_cw: str = Query(..., description="Past calendar week (e.g., CW31)"),
    latest_cw: str = Query(..., description="Latest calendar week (e.g., CW32)"),
    language: Optional[Language] = Query(None, description="Language code"),
    category: Optional[Category] = Query(None, description="Report category"),
    db: Session = Depends(get_db)
):
    """Fetch existing analysis results from DB using real AnalysisService."""
    service = AnalysisService()
    return service.get_analysis_results(
        db=db,
        past_cw=past_cw,
        latest_cw=latest_cw,
        language=language,
        category=category,
    )

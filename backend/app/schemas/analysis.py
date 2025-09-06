from typing import Literal, List, Dict, Any
from pydantic import BaseModel, Field


Language = Literal["EN", "KO"]
Category = Literal["Development", "EPC", "Finance", "Investment"]


class WeeklyReportAnalysisBase(BaseModel):
    project_code: str = Field(min_length=1, max_length=32)
    cw_label: str = Field(min_length=1, max_length=8)
    language: Language = "EN"
    category: Category | None = None


class WeeklyReportAnalysisCreate(WeeklyReportAnalysisBase):
    risk_lvl: float | None = None
    risk_desc: str | None = None
    similarity_lvl: float | None = None
    similarity_desc: str | None = None
    negative_words: Dict[str, Any] | None = None
    created_by: str


class WeeklyReportAnalysisRead(WeeklyReportAnalysisBase):
    id: str
    risk_lvl: float | None = None
    risk_desc: str | None = None
    similarity_lvl: float | None = None
    similarity_desc: str | None = None
    negative_words: Dict[str, Any] | None = None
    created_at: str
    created_by: str


class AnalysisRequest(BaseModel):
    past_cw: str = Field(min_length=1, max_length=8, description="Past calendar week (e.g., CW31)")
    latest_cw: str = Field(min_length=1, max_length=8, description="Latest calendar week (e.g., CW32)")
    language: Language = "EN"
    category: Category | None = None
    created_by: str = "system"


class AnalysisResponse(BaseModel):
    message: str
    analyzed_count: int
    skipped_count: int
    results: List[WeeklyReportAnalysisRead]


class ProjectCandidateResponse(BaseModel):
    project_code: str
    project_name: str | None = None
    categories: List[str]
    cw_labels: List[str]



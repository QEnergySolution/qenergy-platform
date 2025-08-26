from typing import Literal
from pydantic import BaseModel, Field


Language = Literal["EN", "KO"]


class WeeklyReportAnalysisBase(BaseModel):
    project_code: str = Field(min_length=1, max_length=32)
    cw_label: str = Field(min_length=1, max_length=8)
    language: Language = "EN"


class WeeklyReportAnalysisCreate(WeeklyReportAnalysisBase):
    pass



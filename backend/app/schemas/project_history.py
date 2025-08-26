from typing import Literal
from pydantic import BaseModel, Field


EntryType = Literal[
    "Report",
    "Issue",
    "Decision",
    "Maintenance",
    "Meeting minutes",
    "Mid-update",
]


class ProjectHistoryBase(BaseModel):
    project_code: str = Field(min_length=1, max_length=32)
    entry_type: EntryType
    log_date: str
    summary: str
    category: Literal["Development", "EPC", "Finance", "Investment"] | None = None
    cw_label: str | None = Field(default=None, max_length=8)
    title: str | None = Field(default=None, max_length=255)
    next_actions: str | None = None
    owner: str | None = Field(default=None, max_length=255)
    attachment_url: str | None = Field(default=None, max_length=1024)


class ProjectHistoryCreate(ProjectHistoryBase):
    pass



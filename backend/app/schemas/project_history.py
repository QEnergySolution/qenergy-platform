from typing import List, Optional
import uuid
import datetime
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field, constr


class EntryType(str, Enum):
    REPORT = "Report"
    ISSUE = "Issue"
    DECISION = "Decision"
    MAINTENANCE = "Maintenance"
    MEETING_MINUTES = "Meeting minutes"
    MID_UPDATE = "Mid-update"


class Category(str, Enum):
    DEVELOPMENT = "Development"
    EPC = "EPC"
    FINANCE = "Finance"
    INVESTMENT = "Investment"


class ProjectHistoryBase(BaseModel):
    project_code: constr(min_length=1, max_length=32) = Field(..., description="Project code")
    project_name: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Project name")
    category: Optional[str] = Field(None, description="Category (Development, EPC, Finance, Investment)")
    entry_type: EntryType = Field(..., description="Entry type")
    log_date: date = Field(..., description="Log date")
    cw_label: Optional[str] = Field(None, description="Calendar week label (e.g., 'CW01')")
    title: Optional[str] = Field(None, description="Title")
    summary: str = Field(..., description="Summary text")
    next_actions: Optional[str] = Field(None, description="Next actions")
    owner: Optional[str] = Field(None, description="Owner")
    attachment_url: Optional[str] = Field(None, description="Attachment URL")


class ProjectHistoryCreate(ProjectHistoryBase):
    pass


class ProjectHistoryUpdate(BaseModel):
    project_name: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Project name")
    category: Optional[str] = Field(None, description="Category (Development, EPC, Finance, Investment)")
    entry_type: Optional[EntryType] = Field(None, description="Entry type")
    title: Optional[str] = Field(None, description="Title")
    summary: Optional[str] = Field(None, description="Summary text")
    next_actions: Optional[str] = Field(None, description="Next actions")
    owner: Optional[str] = Field(None, description="Owner")
    attachment_url: Optional[str] = Field(None, description="Attachment URL")


class ProjectHistory(ProjectHistoryBase):
    id: uuid.UUID
    source_text: Optional[str] = Field(None, description="Source text")
    created_at: datetime.datetime
    created_by: str
    updated_at: datetime.datetime
    updated_by: str

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime.datetime: lambda v: v.isoformat()
        }


class ProjectHistoryPagination(BaseModel):
    items: List[ProjectHistory]
    total: int
    page: int
    page_size: int


class ProjectHistoryContent(BaseModel):
    project_code: str
    cw_label: str
    category: Optional[str] = None
    content: str
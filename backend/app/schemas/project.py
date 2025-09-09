from typing import List, Optional
import uuid
import datetime
from pydantic import BaseModel, Field, constr


class ProjectBase(BaseModel):
    project_code: constr(min_length=1, max_length=32) = Field(..., description="Unique project code")
    project_name: constr(min_length=1, max_length=255) = Field(..., description="Project name")
    portfolio_cluster: Optional[constr(max_length=128)] = Field(None, description="Portfolio cluster")
    status: int = Field(1, description="Project status: 1=Active, 0=Inactive", ge=0, le=1)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: Optional[constr(min_length=1, max_length=255)] = Field(None, description="Project name")
    portfolio_cluster: Optional[constr(max_length=128)] = Field(None, description="Portfolio cluster")
    status: Optional[int] = Field(None, description="Project status: 1=Active, 0=Inactive", ge=0, le=1)


class Project(ProjectBase):
    id: uuid.UUID
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


class ProjectPagination(BaseModel):
    items: List[Project]
    total: int
    page: int
    page_size: int


class ProjectBulkUpsertRow(ProjectBase):
    pass


class ProjectBulkUpsertRequest(BaseModel):
    projects: List[ProjectBulkUpsertRow]
    mark_missing_as_inactive: Optional[bool] = Field(False, description="If true, projects not in the list will be marked as inactive")


class ProjectBulkUpsertError(BaseModel):
    row_index: int
    project_code: Optional[str] = None
    error_message: str


class ProjectBulkUpsertResponse(BaseModel):
    success: bool
    created_count: int = 0
    updated_count: int = 0
    inactivated_count: int = 0
    errors: List[ProjectBulkUpsertError] = []
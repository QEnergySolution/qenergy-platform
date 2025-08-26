from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    project_code: str = Field(min_length=1, max_length=32)
    project_name: str = Field(min_length=1, max_length=255)
    portfolio_cluster: str | None = Field(default=None, max_length=128)
    status: int


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: str



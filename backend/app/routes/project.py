from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.project_repository import ProjectRepository
from ..schemas.project import (
    Project, 
    ProjectCreate, 
    ProjectUpdate, 
    ProjectPagination,
    ProjectBulkUpsertRequest,
    ProjectBulkUpsertResponse
)


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectPagination)
def get_projects(
    search: Optional[str] = None,
    status: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
) -> dict:
    """
    Get projects with pagination, filtering, and sorting.
    
    - **search**: Search term for project_code, project_name, or portfolio_cluster
    - **status**: Filter by status (1=Active, 0=Inactive)
    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page
    - **sort_by**: Field to sort by (project_code, project_name, portfolio_cluster, status, updated_at)
    - **sort_order**: Sort order (asc, desc)
    """
    repo = ProjectRepository(db)
    projects, total = repo.get_all(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return {
        "items": projects,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{project_code}", response_model=Project)
def get_project(project_code: str, db: Session = Depends(get_db)) -> Project:
    """
    Get a project by its business key (project_code)
    """
    repo = ProjectRepository(db)
    project = repo.get_by_code(project_code)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with code '{project_code}' not found"
        )
    
    return project


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    """
    Create a new project
    """
    repo = ProjectRepository(db)
    
    try:
        # In a real app, get the user from auth context
        created_project = repo.create(project, "web_user")
        db.commit()
        return created_project
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.put("/{project_code}", response_model=Project)
def update_project(project_code: str, project: ProjectUpdate, db: Session = Depends(get_db)) -> Project:
    """
    Update a project by its business key (project_code)
    """
    repo = ProjectRepository(db)
    
    try:
        # In a real app, get the user from auth context
        updated_project = repo.update(project_code, project, "web_user")
        
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with code '{project_code}' not found"
            )
        
        db.commit()
        return updated_project
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/{project_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_code: str, db: Session = Depends(get_db)):
    """
    Soft delete a project (set status=0) by its business key (project_code)
    """
    repo = ProjectRepository(db)
    
    try:
        # In a real app, get the user from auth context
        result = repo.soft_delete(project_code, "web_user")
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with code '{project_code}' not found"
            )
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


@router.post("/bulk-upsert", response_model=ProjectBulkUpsertResponse)
def bulk_upsert_projects(request: ProjectBulkUpsertRequest, db: Session = Depends(get_db)) -> ProjectBulkUpsertResponse:
    """
    Bulk upsert projects by project_code
    
    - Projects with existing project_code will be updated
    - Projects with new project_code will be created
    - If mark_missing_as_inactive=True, projects not in the list will be marked as inactive
    """
    repo = ProjectRepository(db)
    
    try:
        # Validate all projects first
        if not request.projects:
            return ProjectBulkUpsertResponse(
                success=True,
                created_count=0,
                updated_count=0,
                inactivated_count=0
            )
        
        # In a real app, get the user from auth context
        result = repo.bulk_upsert(
            request.projects, 
            "web_user",
            mark_missing_as_inactive=request.mark_missing_as_inactive
        )
        
        # If there are errors, rollback and return the errors
        if result["errors"]:
            db.rollback()
            return ProjectBulkUpsertResponse(
                success=False,
                errors=result["errors"]
            )
        
        db.commit()
        return ProjectBulkUpsertResponse(
            success=True,
            created_count=result["created_count"],
            updated_count=result["updated_count"],
            inactivated_count=result["inactivated_count"]
        )
    except ValueError as e:
        db.rollback()
        if "validation error" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation error: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process bulk upsert: {str(e)}"
        )

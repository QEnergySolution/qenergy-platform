from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.project_history_repository import ProjectHistoryRepository
from ..schemas.project_history import (
    ProjectHistory, 
    ProjectHistoryCreate, 
    ProjectHistoryUpdate, 
    ProjectHistoryPagination,
    ProjectHistoryContent
)


router = APIRouter(prefix="/project-history", tags=["project-history"])


@router.get("", response_model=ProjectHistoryPagination)
def get_project_history(
    project_code: Optional[str] = None,
    category: Optional[str] = None,
    cw_label: Optional[str] = None,
    year: Optional[int] = None,
    start_cw: Optional[str] = None,
    end_cw: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "log_date",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
) -> dict:
    """
    Get project history entries with filtering and pagination
    
    - **project_code**: Filter by project code
    - **category**: Filter by category (Development, EPC, Finance, Investment)
    - **cw_label**: Filter by calendar week label (e.g., 'CW01')
    - **start_cw**: Filter by start calendar week (inclusive)
    - **end_cw**: Filter by end calendar week (inclusive)
    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page
    - **sort_by**: Field to sort by (project_code, category, entry_type, log_date, cw_label, updated_at)
    - **sort_order**: Sort order (asc, desc)
    """
    repo = ProjectHistoryRepository(db)
    
    # Process CW range if provided
    cw_range = None
    if start_cw and end_cw:
        cw_range = (start_cw, end_cw)
    
    entries, total = repo.get_all(
        project_code=project_code,
        category=category,
        cw_label=cw_label,
        cw_range=cw_range,
        year=year,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return {
        "items": entries,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/content", response_model=ProjectHistoryContent)
def get_project_history_content(
    project_code: str,
    cw_label: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
) -> ProjectHistoryContent:
    """
    Get the summary content for a specific project, CW label, and category
    """
    repo = ProjectHistoryRepository(db)
    content = repo.get_content(project_code, cw_label, category)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No content found for project '{project_code}', CW '{cw_label}', category '{category}'"
        )
    
    return {
        "project_code": project_code,
        "cw_label": cw_label,
        "category": category,
        "content": content
    }


@router.get("/{history_id}", response_model=ProjectHistory)
def get_project_history_by_id(history_id: str, db: Session = Depends(get_db)) -> ProjectHistory:
    """
    Get a project history entry by its ID
    """
    repo = ProjectHistoryRepository(db)
    entry = repo.get_by_id(history_id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project history entry with ID '{history_id}' not found"
        )
    
    return entry


@router.post("", response_model=ProjectHistory, status_code=status.HTTP_201_CREATED)
def create_project_history(history: ProjectHistoryCreate, db: Session = Depends(get_db)) -> ProjectHistory:
    """
    Create a new project history entry
    """
    repo = ProjectHistoryRepository(db)
    
    try:
        # In a real app, get the user from auth context
        created_entry = repo.create(history, "web_user")
        db.commit()
        return created_entry
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
            detail=f"Failed to create project history entry: {str(e)}"
        )


@router.put("/{history_id}", response_model=ProjectHistory)
def update_project_history(history_id: str, history: ProjectHistoryUpdate, db: Session = Depends(get_db)) -> ProjectHistory:
    """
    Update a project history entry by its ID
    """
    repo = ProjectHistoryRepository(db)
    
    try:
        # In a real app, get the user from auth context
        updated_entry = repo.update(history_id, history, "web_user")
        
        if not updated_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project history entry with ID '{history_id}' not found"
            )
        
        db.commit()
        return updated_entry
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project history entry: {str(e)}"
        )


@router.post("/upsert", response_model=ProjectHistory)
def upsert_project_history(history: ProjectHistoryCreate, db: Session = Depends(get_db)) -> ProjectHistory:
    """
    Upsert a project history entry by project_code and log_date
    
    - If an entry with the same project_code, log_date, and category exists, it will be updated
    - Otherwise, a new entry will be created
    """
    repo = ProjectHistoryRepository(db)
    
    try:
        # In a real app, get the user from auth context
        entry, is_new = repo.upsert(history, "web_user")
        db.commit()
        
        # Set appropriate status code based on whether a new entry was created
        if is_new:
            return entry
        else:
            return entry
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upsert project history entry: {str(e)}"
        )


@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_history(history_id: str, db: Session = Depends(get_db)):
    """
    Delete a project history entry by its ID
    """
    repo = ProjectHistoryRepository(db)
    
    try:
        result = repo.delete(history_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project history entry with ID '{history_id}' not found"
            )
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project history entry: {str(e)}"
        )

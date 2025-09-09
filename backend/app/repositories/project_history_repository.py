from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime, timedelta
from sqlalchemy import select, update, func, or_, and_, extract
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.project_history import ProjectHistory
from ..schemas.project_history import ProjectHistoryCreate, ProjectHistoryUpdate


class ProjectHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, history_id: str) -> Optional[ProjectHistory]:
        """Get a project history entry by its ID"""
        return self.db.query(ProjectHistory).filter(ProjectHistory.id == history_id).first()

    def get_by_project_code_and_log_date(self, project_code: str, log_date: date, category: Optional[str] = None) -> Optional[ProjectHistory]:
        """Get a project history entry by project_code and log_date"""
        query = self.db.query(ProjectHistory).filter(
            ProjectHistory.project_code == project_code,
            ProjectHistory.log_date == log_date
        )
        
        if category:
            query = query.filter(ProjectHistory.category == category)
            
        return query.first()

    def get_all(
        self,
        project_code: Optional[str] = None,
        category: Optional[str] = None,
        cw_label: Optional[str] = None,
        cw_range: Optional[Tuple[str, str]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "log_date",
        sort_order: str = "desc",
    ) -> Tuple[List[ProjectHistory], int]:
        """
        Get project history entries with filtering and pagination
        Returns: (entries, total_count)
        """
        # Validate sort_by against allowed fields
        allowed_sort_fields = ["project_code", "category", "entry_type", "log_date", "cw_label", "updated_at"]
        if sort_by not in allowed_sort_fields:
            sort_by = "log_date"
        
        # Validate sort_order
        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"
        
        query = select(ProjectHistory)
        
        # Apply filters
        if project_code:
            query = query.where(ProjectHistory.project_code == project_code)
        
        if category:
            query = query.where(ProjectHistory.category == category)
        
        if cw_label:
            query = query.where(ProjectHistory.cw_label == cw_label)
        
        if cw_range:
            start_cw, end_cw = cw_range
            query = query.where(
                and_(
                    ProjectHistory.cw_label >= start_cw,
                    ProjectHistory.cw_label <= end_cw
                )
            )
        
        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0
        
        # Apply sorting
        sort_column = getattr(ProjectHistory, sort_by)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        entries = self.db.execute(query).scalars().all()
        
        return entries, total

    def create(self, history_data: ProjectHistoryCreate, created_by: str) -> ProjectHistory:
        """Create a new project history entry"""
        # Calculate cw_label if not provided
        if not history_data.cw_label:
            log_date = history_data.log_date
            year = log_date.year
            week = log_date.isocalendar()[1]
            cw_label = f"CW{week:02d}"
        else:
            cw_label = history_data.cw_label
        
        # Create the entry
        entry = ProjectHistory(
            **history_data.model_dump(exclude={"cw_label"}),
            cw_label=cw_label,
            created_by=created_by,
            updated_by=created_by
        )
        
        self.db.add(entry)
        try:
            self.db.flush()
            return entry
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"Entry with project_code '{history_data.project_code}' and log_date '{history_data.log_date}' already exists")

    def update(self, history_id: str, history_data: ProjectHistoryUpdate, updated_by: str) -> Optional[ProjectHistory]:
        """Update a project history entry by its ID"""
        entry = self.get_by_id(history_id)
        if not entry:
            return None
        
        update_data = history_data.model_dump(exclude_unset=True)
        if not update_data:
            return entry  # No changes
        
        update_data["updated_by"] = updated_by
        
        stmt = (
            update(ProjectHistory)
            .where(ProjectHistory.id == history_id)
            .values(**update_data)
            .returning(ProjectHistory)
        )
        
        result = self.db.execute(stmt)
        self.db.flush()
        return result.scalar_one_or_none()

    def upsert(self, history_data: ProjectHistoryCreate, updated_by: str) -> Tuple[ProjectHistory, bool]:
        """
        Upsert a project history entry by project_code and log_date
        Returns: (entry, is_new)
        """
        # Check if entry already exists
        existing = self.get_by_project_code_and_log_date(
            project_code=history_data.project_code,
            log_date=history_data.log_date,
            category=history_data.category
        )
        
        if existing:
            # Update existing entry
            update_data = ProjectHistoryUpdate(**history_data.model_dump())
            updated = self.update(existing.id, update_data, updated_by)
            return updated, False
        else:
            # Create new entry
            new_entry = self.create(history_data, updated_by)
            return new_entry, True

    def delete(self, history_id: str) -> bool:
        """Delete a project history entry by its ID"""
        entry = self.get_by_id(history_id)
        if not entry:
            return False
        
        self.db.delete(entry)
        self.db.flush()
        return True

    def get_content(self, project_code: str, cw_label: str, category: Optional[str] = None) -> Optional[str]:
        """Get the summary content for a specific project, CW label, and category"""
        query = self.db.query(ProjectHistory.summary).filter(
            ProjectHistory.project_code == project_code,
            ProjectHistory.cw_label == cw_label
        )
        
        if category:
            query = query.filter(ProjectHistory.category == category)
        
        result = query.first()
        return result[0] if result else None

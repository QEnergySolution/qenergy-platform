from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import select, update, delete, desc, asc, func, or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.project import Project
from ..models.project_history import ProjectHistory
from ..models.weekly_report_analysis import WeeklyReportAnalysis
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectBulkUpsertRow, ProjectBulkUpsertError


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, project_code: str) -> Optional[Project]:
        """Get a project by its business key (project_code)"""
        return self.db.execute(
            select(Project).where(Project.project_code == project_code)
        ).scalar_one_or_none()

    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by its primary key (id)"""
        return self.db.execute(
            select(Project).where(Project.id == project_id)
        ).scalar_one_or_none()

    def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[int] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Project], int]:
        """
        Get all projects with pagination, filtering, and sorting.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search term for project_code, project_name, or portfolio_cluster
            status: Filter by status (1=Active, 0=Inactive)
            sort_by: Field to sort by (project_code, project_name, portfolio_cluster, status, updated_at)
            sort_order: Sort order (asc, desc)
            
        Returns:
            Tuple of (projects, total_count)
        """
        # Base query
        query = select(Project)
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Project.project_code.ilike(search_term),
                    Project.project_name.ilike(search_term),
                    Project.portfolio_cluster.ilike(search_term)
                )
            )
        
        # Apply status filter if provided
        if status is not None:
            query = query.where(Project.status == status)
        
        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar_one()
        
        # Apply sorting
        if sort_by == "project_code":
            sort_field = Project.project_code
        elif sort_by == "project_name":
            sort_field = Project.project_name
        elif sort_by == "portfolio_cluster":
            sort_field = Project.portfolio_cluster
        elif sort_by == "status":
            sort_field = Project.status
        else:  # Default to updated_at
            sort_field = Project.updated_at
        
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_field))
        else:  # Default to desc
            query = query.order_by(desc(sort_field))
        
        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        projects = self.db.execute(query).scalars().all()
        
        return projects, total

    def create(self, project_data: ProjectCreate, created_by: str) -> Project:
        """
        Create a new project.
        
        Args:
            project_data: Project data to create
            created_by: User who created the project
            
        Returns:
            Created project
        """
        # Check if project with same code already exists
        existing = self.get_by_code(project_data.project_code)
        if existing:
            raise ValueError(f"Project with code '{project_data.project_code}' already exists")
        
        # Create new project
        project = Project(
            **project_data.model_dump(),
            created_by=created_by,
            updated_by=created_by
        )
        
        self.db.add(project)
        self.db.flush()  # Flush to get the ID without committing
        
        return project

    def update(self, project_code: str, project_data: ProjectUpdate, updated_by: str) -> Optional[Project]:
        """
        Update an existing project.
        
        Args:
            project_code: Project code to update
            project_data: Project data to update
            updated_by: User who updated the project
            
        Returns:
            Updated project or None if not found
        """
        # Get existing project
        project = self.get_by_code(project_code)
        if not project:
            return None
        
        # Update project with provided data
        update_data = project_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(project, key, value)
        
        # Update audit fields
        project.updated_by = updated_by
        
        self.db.add(project)
        self.db.flush()  # Flush to get the updated project without committing
        
        return project

    def soft_delete(self, project_code: str, updated_by: str) -> bool:
        """
        Soft delete a project (set status=0).
        
        Args:
            project_code: Project code to delete
            updated_by: User who deleted the project
            
        Returns:
            True if deleted, False if not found
        """
        # Update project status to 0 (inactive)
        result = self.db.execute(
            update(Project)
            .where(Project.project_code == project_code)
            .values(status=0, updated_by=updated_by)
        )
        
        # Return True if any rows were affected
        return result.rowcount > 0

    def hard_delete(self, project_code: str) -> bool:
        """
        Permanently delete a project and its dependent records.
        Returns True if a project was deleted, False if not found.
        """
        # Check existence
        project = self.get_by_code(project_code)
        if not project:
            return False

        # Delete dependents first to satisfy FK constraints
        # project_history
        self.db.execute(
            delete(ProjectHistory).where(ProjectHistory.project_code == project_code)
        )

        # weekly_report_analysis (model name may differ)
        try:
            self.db.execute(
                delete(WeeklyReportAnalysis).where(WeeklyReportAnalysis.project_code == project_code)
            )
        except Exception:
            # If model/table not present, ignore
            pass

        # Delete the project itself
        self.db.execute(
            delete(Project).where(Project.project_code == project_code)
        )
        return True

    def bulk_upsert(
        self,
        projects: List[ProjectBulkUpsertRow],
        updated_by: str,
        mark_missing_as_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        Bulk upsert projects (update existing, insert new).
        
        Args:
            projects: List of projects to upsert
            updated_by: User who performed the upsert
            mark_missing_as_inactive: If True, projects not in the list will be marked as inactive
            
        Returns:
            Dict with counts and errors
        """
        created_count = 0
        updated_count = 0
        inactivated_count = 0
        errors = []
        
        # Get all existing project codes
        existing_projects_query = select(Project.project_code)
        existing_project_codes = set(
            code for (code,) in self.db.execute(existing_projects_query).all()
        )
        
        # Track processed project codes
        processed_codes = set()
        
        # Process each project
        for i, project_data in enumerate(projects):
            try:
                project_code = project_data.project_code
                processed_codes.add(project_code)
                
                if project_code in existing_project_codes:
                    # Update existing project
                    update_data = ProjectUpdate(
                        project_name=project_data.project_name,
                        portfolio_cluster=project_data.portfolio_cluster,
                        status=project_data.status
                    )
                    self.update(project_code, update_data, updated_by)
                    updated_count += 1
                else:
                    # Create new project
                    self.create(project_data, updated_by)
                    created_count += 1
            except Exception as e:
                # Add error to list
                errors.append(
                    ProjectBulkUpsertError(
                        row_index=i,
                        project_code=getattr(project_data, "project_code", None),
                        error_message=str(e)
                    )
                )
        
        # Mark missing projects as inactive if requested
        if mark_missing_as_inactive and processed_codes:
            missing_codes = existing_project_codes - processed_codes
            
            if missing_codes:
                # Update status to 0 (inactive) for missing projects
                result = self.db.execute(
                    update(Project)
                    .where(Project.project_code.in_(missing_codes))
                    .values(status=0, updated_by=updated_by)
                )
                
                inactivated_count = result.rowcount
        
        return {
            "created_count": created_count,
            "updated_count": updated_count,
            "inactivated_count": inactivated_count,
            "errors": errors
        }

import pytest
from datetime import date

from app.repositories.project_history_repository import ProjectHistoryRepository
from app.schemas.project_history import ProjectHistoryCreate, ProjectHistoryUpdate, EntryType
from app.models.project_history import ProjectHistory
from app.models.project import Project


def test_create_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST001",
        project_name="History Test Project",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a test project history entry
    history_data = ProjectHistoryCreate(
        project_code="HIST001",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),  # First Monday of 2025
        title="Test History",
        summary="This is a test history entry"
    )
    
    history = repo.create(history_data, "test_user")
    db_session.flush()
    
    # Verify history was created
    assert history.project_code == "HIST001"
    assert history.category == "Development"
    assert history.entry_type == "Report"
    assert history.log_date == date(2025, 1, 6)
    assert history.cw_label == "CW02"  # Auto-calculated - 2025-01-06 is actually CW02
    assert history.title == "Test History"
    assert history.summary == "This is a test history entry"
    assert history.created_by == "test_user"
    assert history.updated_by == "test_user"
    
    # Verify we can retrieve it
    retrieved = repo.get_by_id(history.id)
    assert retrieved is not None
    assert retrieved.project_code == "HIST001"


def test_create_duplicate_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST002",
        project_name="History Test Project 2",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a history entry
    history_data = ProjectHistoryCreate(
        project_code="HIST002",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),
        title="Test History 2",
        summary="This is a test history entry 2"
    )
    
    repo.create(history_data, "test_user")
    db_session.flush()
    
    # Try to create another with same project_code, log_date, and category
    duplicate_data = ProjectHistoryCreate(
        project_code="HIST002",
        category="Development",
        entry_type=EntryType.ISSUE,
        log_date=date(2025, 1, 6),
        title="Duplicate History",
        summary="This should fail"
    )
    
    with pytest.raises(ValueError, match="already exists"):
        repo.create(duplicate_data, "test_user")


def test_get_by_id(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST003",
        project_name="History Test Project 3",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a test history entry
    history_data = ProjectHistoryCreate(
        project_code="HIST003",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),
        title="Test History 3",
        summary="This is a test history entry 3"
    )
    
    history = repo.create(history_data, "test_user")
    db_session.flush()
    
    # Get by ID
    retrieved = repo.get_by_id(history.id)
    assert retrieved is not None
    assert retrieved.project_code == "HIST003"
    
    # Get non-existent history
    non_existent = repo.get_by_id("00000000-0000-0000-0000-000000000000")
    assert non_existent is None


def test_get_by_project_code_and_log_date(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST004",
        project_name="History Test Project 4",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a test history entry
    history_data = ProjectHistoryCreate(
        project_code="HIST004",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),
        title="Test History 4",
        summary="This is a test history entry 4"
    )
    
    history = repo.create(history_data, "test_user")
    db_session.flush()
    
    # Get by project_code and log_date
    retrieved = repo.get_by_project_code_and_log_date("HIST004", date(2025, 1, 6), "Development")
    assert retrieved is not None
    assert retrieved.project_code == "HIST004"
    assert retrieved.log_date == date(2025, 1, 6)
    
    # Get non-existent history
    non_existent = repo.get_by_project_code_and_log_date("NONEXISTENT", date(2025, 1, 6))
    assert non_existent is None


def test_update_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST005",
        project_name="History Test Project 5",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a test history entry
    history_data = ProjectHistoryCreate(
        project_code="HIST005",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),
        title="Test History 5",
        summary="This is a test history entry 5"
    )
    
    history = repo.create(history_data, "test_user")
    db_session.flush()
    
    # Update the history
    update_data = ProjectHistoryUpdate(
        title="Updated History 5",
        summary="This is an updated history entry 5",
        entry_type=EntryType.ISSUE
    )
    
    updated = repo.update(history.id, update_data, "updater_user")
    db_session.flush()
    
    # Verify update
    assert updated is not None
    assert updated.title == "Updated History 5"
    assert updated.summary == "This is an updated history entry 5"
    assert updated.entry_type == "Issue"
    assert updated.updated_by == "updater_user"
    
    # Verify by retrieving again
    retrieved = repo.get_by_id(history.id)
    assert retrieved.title == "Updated History 5"
    assert retrieved.entry_type == "Issue"


def test_update_nonexistent_project_history(db_session):
    repo = ProjectHistoryRepository(db_session)
    
    update_data = ProjectHistoryUpdate(
        title="This won't work",
        summary="This won't work either"
    )
    
    result = repo.update("00000000-0000-0000-0000-000000000000", update_data, "updater_user")
    assert result is None


def test_delete_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST006",
        project_name="History Test Project 6",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a test history entry
    history_data = ProjectHistoryCreate(
        project_code="HIST006",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),
        title="Test History 6",
        summary="This is a test history entry 6"
    )
    
    history = repo.create(history_data, "test_user")
    db_session.flush()
    
    # Delete
    result = repo.delete(history.id)
    db_session.flush()
    
    # Verify delete
    assert result is True
    
    # Verify it's gone
    deleted = repo.get_by_id(history.id)
    assert deleted is None


def test_delete_nonexistent_project_history(db_session):
    repo = ProjectHistoryRepository(db_session)
    
    result = repo.delete("00000000-0000-0000-0000-000000000000")
    assert result is False


def test_get_all_with_filtering(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST007",
        project_name="History Test Project 7",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create multiple test histories
    histories = [
        ("HIST007", "Development", EntryType.REPORT, date(2025, 1, 6), "CW01", "Dev Report"),
        ("HIST007", "Finance", EntryType.REPORT, date(2025, 1, 6), "CW01", "Finance Report"),
        ("HIST007", "Development", EntryType.ISSUE, date(2025, 1, 13), "CW02", "Dev Issue"),
    ]
    
    for code, category, entry_type, log_date, cw_label, title in histories:
        history_data = ProjectHistoryCreate(
            project_code=code,
            category=category,
            entry_type=entry_type,
            log_date=log_date,
            cw_label=cw_label,
            title=title,
            summary=f"Summary for {title}"
        )
        repo.create(history_data, "test_user")
    
    db_session.flush()
    
    # Test filter by project_code
    results, count = repo.get_all(project_code="HIST007")
    assert count == 3
    assert all(h.project_code == "HIST007" for h in results)
    
    # Test filter by category
    results, count = repo.get_all(project_code="HIST007", category="Development")
    assert count == 2
    assert all(h.category == "Development" for h in results)
    
    # Test filter by cw_label
    results, count = repo.get_all(project_code="HIST007", cw_label="CW01")
    assert count == 2
    assert all(h.cw_label == "CW01" for h in results)
    
    # Test filter by cw_range
    results, count = repo.get_all(project_code="HIST007", cw_range=("CW01", "CW02"))
    assert count == 3
    assert all(h.cw_label in ["CW01", "CW02"] for h in results)


def test_get_all_with_sorting(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST008",
        project_name="History Test Project 8",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create multiple test histories
    histories = [
        ("HIST008", "Development", EntryType.REPORT, date(2025, 1, 6), "CW01", "First Report"),
        ("HIST008", "Finance", EntryType.REPORT, date(2025, 1, 13), "CW02", "Second Report"),
        ("HIST008", "Development", EntryType.ISSUE, date(2025, 1, 20), "CW03", "Third Report"),
    ]
    
    for code, category, entry_type, log_date, cw_label, title in histories:
        history_data = ProjectHistoryCreate(
            project_code=code,
            category=category,
            entry_type=entry_type,
            log_date=log_date,
            cw_label=cw_label,
            title=title,
            summary=f"Summary for {title}"
        )
        repo.create(history_data, "test_user")
    
    db_session.flush()
    
    # Test sort by log_date asc
    results, _ = repo.get_all(
        project_code="HIST008",
        sort_by="log_date",
        sort_order="asc"
    )
    log_dates = [h.log_date for h in results]
    assert log_dates == [date(2025, 1, 6), date(2025, 1, 13), date(2025, 1, 20)]
    
    # Test sort by log_date desc
    results, _ = repo.get_all(
        project_code="HIST008",
        sort_by="log_date",
        sort_order="desc"
    )
    log_dates = [h.log_date for h in results]
    assert log_dates == [date(2025, 1, 20), date(2025, 1, 13), date(2025, 1, 6)]
    
    # Test sort by category asc
    results, _ = repo.get_all(
        project_code="HIST008",
        sort_by="category",
        sort_order="asc"
    )
    categories = [h.category for h in results]
    assert categories[0] == "Development"  # Development comes before Finance alphabetically
    
    # Test sort by entry_type asc
    results, _ = repo.get_all(
        project_code="HIST008",
        sort_by="entry_type",
        sort_order="asc"
    )
    entry_types = [h.entry_type for h in results]
    assert "Issue" in entry_types[0]  # Issue comes before Report alphabetically


def test_upsert_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST009",
        project_name="History Test Project 9",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a new history via upsert
    history_data = ProjectHistoryCreate(
        project_code="HIST009",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),
        title="Test History 9",
        summary="This is a test history entry 9"
    )
    
    entry, is_new = repo.upsert(history_data, "test_user")
    db_session.flush()
    
    # Verify it was created
    assert is_new is True
    assert entry.project_code == "HIST009"
    assert entry.title == "Test History 9"
    
    # Update via upsert
    update_data = ProjectHistoryCreate(
        project_code="HIST009",
        category="Development",
        entry_type=EntryType.ISSUE,
        log_date=date(2025, 1, 6),
        title="Updated History 9",
        summary="This is an updated history entry 9"
    )
    
    updated_entry, is_new = repo.upsert(update_data, "updater_user")
    db_session.flush()
    
    # Verify it was updated
    assert is_new is False
    assert updated_entry.project_code == "HIST009"
    assert updated_entry.title == "Updated History 9"
    assert updated_entry.entry_type == "Issue"
    assert updated_entry.updated_by == "updater_user"


def test_get_content(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="HIST010",
        project_name="History Test Project 10",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.flush()
    
    repo = ProjectHistoryRepository(db_session)
    
    # Create a test history entry
    history_data = ProjectHistoryCreate(
        project_code="HIST010",
        category="Development",
        entry_type=EntryType.REPORT,
        log_date=date(2025, 1, 6),
        cw_label="CW01",
        title="Test History 10",
        summary="This is a test history entry 10"
    )
    
    repo.create(history_data, "test_user")
    db_session.flush()
    
    # Get content
    content = repo.get_content("HIST010", "CW01", "Development")
    assert content == "This is a test history entry 10"
    
    # Get non-existent content
    non_existent = repo.get_content("NONEXISTENT", "CW01")
    assert non_existent is None

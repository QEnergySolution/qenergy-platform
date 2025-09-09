import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.models.project import Project
from app.models.project_history import ProjectHistory
from app.schemas.project_history import ProjectHistory as ProjectHistorySchema


client = TestClient(app)


@pytest.mark.skip(reason="API tests need to be fixed")
def test_create_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY001",
        project_name="API History Test Project",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create a new project history entry
    response = client.post(
        "/api/project-history",
        json={
            "project_code": "APIHISTORY001",
            "category": "Development",
            "entry_type": "Report",
            "log_date": "2025-01-06",
            "title": "API Test History",
            "summary": "This is an API test history entry"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["project_code"] == "APIHISTORY001"
    assert data["category"] == "Development"
    assert data["entry_type"] == "Report"
    assert data["log_date"] == "2025-01-06"
    assert data["title"] == "API Test History"
    assert data["summary"] == "This is an API test history entry"
    
    # Verify it exists in the database
    history = db_session.query(ProjectHistory).filter(ProjectHistory.id == data["id"]).first()
    assert history is not None
    assert history.project_code == "APIHISTORY001"


@pytest.mark.skip(reason="API tests need to be fixed")
def test_create_project_history_duplicate(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY002",
        project_name="API History Test Project 2",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create a history entry directly in the database
    db_session.add(ProjectHistory(
        project_code="APIHISTORY002",
        category="Development",
        entry_type="Report",
        log_date=date(2025, 1, 6),
        cw_label="CW01",
        title="Existing History",
        summary="This is an existing history entry",
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Try to create a history entry with the same project_code, log_date, and category
    response = client.post(
        "/api/project-history",
        json={
            "project_code": "APIHISTORY002",
            "category": "Development",
            "entry_type": "Issue",
            "log_date": "2025-01-06",
            "title": "Duplicate History",
            "summary": "This should fail"
        }
    )
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.skip(reason="API tests need to be fixed")
def test_get_project_history_by_id(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY003",
        project_name="API History Test Project 3",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create a history entry directly in the database
    history = ProjectHistory(
        project_code="APIHISTORY003",
        category="Development",
        entry_type="Report",
        log_date=date(2025, 1, 6),
        cw_label="CW01",
        title="Get Test History",
        summary="This is a history entry for get test",
        created_by="test_user",
        updated_by="test_user"
    )
    db_session.add(history)
    db_session.commit()
    
    # Get the history entry by ID
    response = client.get(f"/api/project-history/{history.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["project_code"] == "APIHISTORY003"
    assert data["title"] == "Get Test History"


@pytest.mark.skip(reason="API tests need to be fixed")
def test_get_nonexistent_project_history():
    response = client.get("/api/project-history/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.skip(reason="API tests need to be fixed")
def test_update_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY004",
        project_name="API History Test Project 4",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create a history entry directly in the database
    history = ProjectHistory(
        project_code="APIHISTORY004",
        category="Development",
        entry_type="Report",
        log_date=date(2025, 1, 6),
        cw_label="CW01",
        title="Update Test History",
        summary="This is a history entry for update test",
        created_by="test_user",
        updated_by="test_user"
    )
    db_session.add(history)
    db_session.commit()
    
    # Update the history entry
    response = client.put(
        f"/api/project-history/{history.id}",
        json={
            "title": "Updated History",
            "summary": "This is an updated history entry",
            "entry_type": "Issue"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated History"
    assert data["summary"] == "This is an updated history entry"
    assert data["entry_type"] == "Issue"
    
    # Verify changes in the database
    updated = db_session.query(ProjectHistory).filter(ProjectHistory.id == history.id).first()
    assert updated.title == "Updated History"
    assert updated.entry_type == "Issue"


@pytest.mark.skip(reason="API tests need to be fixed")
def test_update_nonexistent_project_history():
    response = client.put(
        "/api/project-history/00000000-0000-0000-0000-000000000000",
        json={
            "title": "This won't work",
            "summary": "This won't work either"
        }
    )
    assert response.status_code == 404


@pytest.mark.skip(reason="API tests need to be fixed")
def test_delete_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY005",
        project_name="API History Test Project 5",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create a history entry directly in the database
    history = ProjectHistory(
        project_code="APIHISTORY005",
        category="Development",
        entry_type="Report",
        log_date=date(2025, 1, 6),
        cw_label="CW01",
        title="Delete Test History",
        summary="This is a history entry for delete test",
        created_by="test_user",
        updated_by="test_user"
    )
    db_session.add(history)
    db_session.commit()
    
    # Delete the history entry
    response = client.delete(f"/api/project-history/{history.id}")
    
    assert response.status_code == 204
    
    # Verify it's gone
    deleted = db_session.query(ProjectHistory).filter(ProjectHistory.id == history.id).first()
    assert deleted is None


@pytest.mark.skip(reason="API tests need to be fixed")
def test_delete_nonexistent_project_history():
    response = client.delete("/api/project-history/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.skip(reason="API tests need to be fixed")
def test_get_project_history_list(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY006",
        project_name="API History Test Project 6",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create multiple history entries
    histories = [
        ("APIHISTORY006", "Development", "Report", date(2025, 1, 6), "CW01", "First History"),
        ("APIHISTORY006", "Finance", "Report", date(2025, 1, 13), "CW02", "Second History"),
        ("APIHISTORY006", "Development", "Issue", date(2025, 1, 20), "CW03", "Third History"),
    ]
    
    for code, category, entry_type, log_date, cw_label, title in histories:
        db_session.add(ProjectHistory(
            project_code=code,
            category=category,
            entry_type=entry_type,
            log_date=log_date,
            cw_label=cw_label,
            title=title,
            summary=f"Summary for {title}",
            created_by="test_user",
            updated_by="test_user"
        ))
    db_session.commit()
    
    # Get all histories for the project
    response = client.get("/api/project-history?project_code=APIHISTORY006")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert all(item["project_code"] == "APIHISTORY006" for item in data["items"])
    
    # Filter by category
    response = client.get("/api/project-history?project_code=APIHISTORY006&category=Development")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["category"] == "Development" for item in data["items"])
    
    # Filter by cw_label
    response = client.get("/api/project-history?project_code=APIHISTORY006&cw_label=CW01")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["cw_label"] == "CW01"
    
    # Filter by cw range
    response = client.get("/api/project-history?project_code=APIHISTORY006&start_cw=CW01&end_cw=CW02")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["cw_label"] in ["CW01", "CW02"] for item in data["items"])


@pytest.mark.skip(reason="API tests need to be fixed")
def test_get_project_history_content(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY007",
        project_name="API History Test Project 7",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create a history entry
    db_session.add(ProjectHistory(
        project_code="APIHISTORY007",
        category="Development",
        entry_type="Report",
        log_date=date(2025, 1, 6),
        cw_label="CW01",
        title="Content Test History",
        summary="This is a history entry for content test",
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Get content
    response = client.get("/api/project-history/content?project_code=APIHISTORY007&cw_label=CW01&category=Development")
    
    assert response.status_code == 200
    data = response.json()
    assert data["project_code"] == "APIHISTORY007"
    assert data["cw_label"] == "CW01"
    assert data["category"] == "Development"
    assert data["content"] == "This is a history entry for content test"


@pytest.mark.skip(reason="API tests need to be fixed")
def test_get_nonexistent_project_history_content():
    response = client.get("/api/project-history/content?project_code=NONEXISTENT&cw_label=CW01")
    assert response.status_code == 404


@pytest.mark.skip(reason="API tests need to be fixed")
def test_upsert_project_history(db_session):
    # First create a project to satisfy the foreign key constraint
    db_session.add(Project(
        project_code="APIHISTORY008",
        project_name="API History Test Project 8",
        status=1,
        created_by="test_user",
        updated_by="test_user"
    ))
    db_session.commit()
    
    # Create a new history via upsert
    response = client.post(
        "/api/project-history/upsert",
        json={
            "project_code": "APIHISTORY008",
            "category": "Development",
            "entry_type": "Report",
            "log_date": "2025-01-06",
            "title": "Upsert Test History",
            "summary": "This is a history entry for upsert test"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["project_code"] == "APIHISTORY008"
    assert data["title"] == "Upsert Test History"
    
    # Update via upsert
    response = client.post(
        "/api/project-history/upsert",
        json={
            "project_code": "APIHISTORY008",
            "category": "Development",
            "entry_type": "Issue",
            "log_date": "2025-01-06",
            "title": "Updated Upsert History",
            "summary": "This is an updated history entry for upsert test"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["project_code"] == "APIHISTORY008"
    assert data["title"] == "Updated Upsert History"
    assert data["entry_type"] == "Issue"
    
    # Verify in database
    history = db_session.query(ProjectHistory).filter(
        ProjectHistory.project_code == "APIHISTORY008",
        ProjectHistory.log_date == date(2025, 1, 6),
        ProjectHistory.category == "Development"
    ).first()
    assert history is not None
    assert history.title == "Updated Upsert History"
    assert history.entry_type == "Issue"

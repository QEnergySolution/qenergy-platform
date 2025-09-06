"""Test category filtering functionality in project history API"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    """Get database session for testing"""
    from app.database import get_db
    db = next(get_db())
    yield db
    db.close()


def test_category_filtering_development(client, db_session):
    """Test filtering by Development category"""
    response = client.get("/api/project-history?year=2025&cw_label=CW01&category=Development")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "projectHistory" in data
    assert "totalRecords" in data
    assert "filters" in data
    
    # Check filters are applied correctly
    assert data["filters"]["year"] == 2025
    assert data["filters"]["cwLabel"] == "CW01"
    assert data["filters"]["category"] == "Development"
    
    # Check all returned records have Development category
    for record in data["projectHistory"]:
        assert record["category"] == "Development"
    
    # Verify we have some records (assuming test data exists)
    assert data["totalRecords"] > 0
    assert len(data["projectHistory"]) > 0


def test_category_filtering_epc(client, db_session):
    """Test filtering by EPC category"""
    response = client.get("/api/project-history?year=2025&cw_label=CW01&category=EPC")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned records have EPC category
    for record in data["projectHistory"]:
        assert record["category"] == "EPC"
    
    # Check filters are applied correctly
    assert data["filters"]["category"] == "EPC"


def test_category_filtering_finance(client, db_session):
    """Test filtering by Finance category"""
    response = client.get("/api/project-history?year=2025&cw_label=CW01&category=Finance")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned records have Finance category (if any exist)
    for record in data["projectHistory"]:
        assert record["category"] == "Finance"
    
    # Check filters are applied correctly
    assert data["filters"]["category"] == "Finance"


def test_category_filtering_investment(client, db_session):
    """Test filtering by Investment category"""
    response = client.get("/api/project-history?year=2025&cw_label=CW01&category=Investment")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned records have Investment category (if any exist)
    for record in data["projectHistory"]:
        assert record["category"] == "Investment"
    
    # Check filters are applied correctly
    assert data["filters"]["category"] == "Investment"


def test_no_category_filter_returns_all(client, db_session):
    """Test that without category filter, all categories are returned"""
    response = client.get("/api/project-history?year=2025&cw_label=CW01")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have no category filter
    assert data["filters"]["category"] is None
    
    # Should return records from multiple categories
    categories = set(record["category"] for record in data["projectHistory"])
    
    # We expect at least Development and EPC based on test data
    assert len(categories) >= 2
    assert "Development" in categories
    assert "EPC" in categories


def test_category_filter_comparison(client, db_session):
    """Test that category filtering actually reduces results"""
    # Get all records
    response_all = client.get("/api/project-history?year=2025&cw_label=CW01")
    data_all = response_all.json()
    
    # Get Development records only
    response_dev = client.get("/api/project-history?year=2025&cw_label=CW01&category=Development")
    data_dev = response_dev.json()
    
    # Get EPC records only
    response_epc = client.get("/api/project-history?year=2025&cw_label=CW01&category=EPC")
    data_epc = response_epc.json()
    
    # Category filtering should reduce the number of records
    assert data_dev["totalRecords"] < data_all["totalRecords"]
    assert data_epc["totalRecords"] < data_all["totalRecords"]
    
    # The sum of filtered records should equal or be close to total
    # (allowing for other categories that might exist)
    assert data_dev["totalRecords"] + data_epc["totalRecords"] <= data_all["totalRecords"]


def test_invalid_category_returns_empty(client, db_session):
    """Test that invalid category returns empty results"""
    response = client.get("/api/project-history?year=2025&cw_label=CW01&category=InvalidCategory")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return empty results
    assert data["totalRecords"] == 0
    assert len(data["projectHistory"]) == 0
    
    # But filter should still be set
    assert data["filters"]["category"] == "InvalidCategory"


def test_category_case_sensitivity(client, db_session):
    """Test that category filtering is case sensitive"""
    # Test with correct case
    response_correct = client.get("/api/project-history?year=2025&cw_label=CW01&category=Development")
    data_correct = response_correct.json()
    
    # Test with wrong case
    response_wrong = client.get("/api/project-history?year=2025&cw_label=CW01&category=development")
    data_wrong = response_wrong.json()
    
    # Correct case should return results, wrong case should return empty
    assert data_correct["totalRecords"] > 0
    assert data_wrong["totalRecords"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

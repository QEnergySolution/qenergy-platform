import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json().get("ok") is True


def test_db_ping(client):
    res = client.get("/api/db/ping")
    assert res.status_code == 200
    assert res.json().get("db") in {"ok", "fail"}


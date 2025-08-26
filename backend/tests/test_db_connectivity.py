import os
import sys
import importlib
from pathlib import Path
from sqlalchemy import text

# Ensure backend root is on sys.path for importing app.* regardless of runner CWD
BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


def test_database_module_exists():
    try:
        importlib.import_module("app.database")
    except ModuleNotFoundError as exc:
        raise AssertionError("Expected module app.database to exist for DB engine/session setup") from exc


def test_can_create_engine_and_select_1(monkeypatch):
    # Use env DATABASE_URL; test assumes local Postgres reachable as per env.example
    db_url = os.getenv("DATABASE_URL")
    assert db_url, "DATABASE_URL must be set for DB connectivity test"

    database = importlib.import_module("app.database")
    engine = getattr(database, "engine", None)
    if engine is None and hasattr(database, "get_engine"):
        engine = database.get_engine()
    assert engine is not None, "app.database should expose 'engine' or 'get_engine'"

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row is not None and (row[0] == 1 or row[0] == 1.0)



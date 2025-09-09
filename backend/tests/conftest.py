import os
import sys
import uuid
import subprocess
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2 import sql
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Load backend/.env so DATABASE_URL and other keys are available for tests
try:
    from dotenv import load_dotenv
    load_dotenv(str(Path(BACKEND_ROOT) / ".env"), override=True)
except Exception:
    pass


@contextmanager
def _temp_db(base_url: str):
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    dbname = f"qenergy_platform_test_{uuid.uuid4().hex[:8]}"
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(dbname)))
        yield _swap_db_in_url(base_url, dbname)
    finally:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();"
                ),
                [dbname],
            )
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {};").format(sql.Identifier(dbname)))
        conn.close()


def _swap_db_in_url(url: str, new_db: str) -> str:
    prefix, _, _ = url.rpartition("/")
    return f"{prefix}/{new_db}"


def _alembic_upgrade(url: str):
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.check_call(["conda", "run", "-n", "qenergy-backend", "alembic", "upgrade", "head"], cwd=BACKEND_ROOT, env=env)


@pytest.fixture(scope="session")
def test_database_url():
    base_url = os.getenv("DATABASE_URL")
    assert base_url, "DATABASE_URL must be set"
    with _temp_db(base_url) as url:
        _alembic_upgrade(url)
        yield url


@pytest.fixture()
def db_session(test_database_url):
    engine = create_engine(test_database_url, future=True)
    with Session(engine) as session:
        try:
            yield session
            session.rollback()
        except Exception:
            session.rollback()
            raise


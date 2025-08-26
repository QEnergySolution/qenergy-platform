import os
import sys
from pathlib import Path
import subprocess
import uuid
from contextlib import contextmanager

import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session


BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from .factories import ProjectFactory, ProjectHistoryFactory, WeeklyReportAnalysisFactory


@contextmanager
def temp_db(base_url: str):
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


def _run_alembic_upgrade(test_url: str):
    env = os.environ.copy()
    env["DATABASE_URL"] = test_url
    subprocess.check_call(["conda", "run", "-n", "qenergy-backend", "alembic", "upgrade", "head"], cwd=os.path.dirname(__file__) + "/..", env=env)


def test_models_can_insert_and_query(db_session):
    base_url = os.getenv("DATABASE_URL")
    assert base_url, "DATABASE_URL must be set"

    # Import models
    from app.models.project import Project
    from app.models.project_history import ProjectHistory
    from app.models.weekly_report_analysis import WeeklyReportAnalysis

    # Insert project with factory
    pdata = ProjectFactory()
    p = Project(**pdata)
    p.project_code = "PX01"
    p.project_name = "Proj X"
    db_session.add(p)
    db_session.flush()

    # Insert history
    hdata = ProjectHistoryFactory(project_code="PX01")
    ph = ProjectHistory(**hdata)
    db_session.add(ph)
    db_session.flush()

    # Insert analysis
    adata = WeeklyReportAnalysisFactory(project_code="PX01")
    wa = WeeklyReportAnalysis(**adata)
    db_session.add(wa)
    db_session.flush()

    got_p = db_session.execute(select(Project).where(Project.project_code == "PX01")).scalar_one()
    assert got_p.project_name == "Proj X"

    got_hist = db_session.execute(select(ProjectHistory).where(ProjectHistory.project_code == "PX01")).all()
    assert len(got_hist) == 1

    got_wa = db_session.execute(select(WeeklyReportAnalysis).where(WeeklyReportAnalysis.project_code == "PX01")).all()
    assert len(got_wa) == 1



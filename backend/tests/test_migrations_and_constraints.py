import os
import subprocess
import uuid
from contextlib import contextmanager

import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


@contextmanager
def temp_db(base_url: str):
    # base_url like postgresql://user:pass@host:5432/qenergy_platform
    # create database qenergy_platform_test_<uuid>
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    dbname = f"qenergy_platform_test_{uuid.uuid4().hex[:8]}"
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(dbname)))
        test_url = _swap_db_in_url(base_url, dbname)
        yield test_url
    finally:
        with conn.cursor() as cur:
            # terminate active connections then drop
            cur.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();"
                ),
                [dbname],
            )
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {};").format(sql.Identifier(dbname)))
        conn.close()


def _swap_db_in_url(url: str, new_db: str) -> str:
    # naive replace last path segment
    prefix, _, _ = url.rpartition("/")
    return f"{prefix}/{new_db}"


def _run_alembic_upgrade(test_url: str):
    env = os.environ.copy()
    env["DATABASE_URL"] = test_url
    subprocess.check_call(["conda", "run", "-n", "qenergy-backend", "alembic", "upgrade", "head"], cwd=os.path.dirname(__file__) + "/..", env=env)


def test_migrations_apply_and_schema_constraints():
    base_url = os.getenv("DATABASE_URL")
    assert base_url, "DATABASE_URL must be set"

    with temp_db(base_url) as test_url:
        _run_alembic_upgrade(test_url)

        engine = create_engine(test_url, future=True)
        with engine.connect() as conn:
            # projects unique project_code
            conn.execute(text("INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES ('P001','P One',1,'sys','sys')"))
            conn.commit()
            try:
                conn.execute(text("INSERT INTO projects (project_code, project_name, status, created_by, updated_by) VALUES ('P001','P One Again',1,'sys','sys')"))
                conn.commit()
                assert False, "should violate unique(project_code)"
            except Exception:
                conn.rollback()

            # project_history unique (project_code, log_date) and CHECK on entry_type
            conn.execute(text("INSERT INTO project_history (project_code, entry_type, log_date, summary, created_by, updated_by) VALUES ('P001','Report','2025-01-06','ok','sys','sys')"))
            conn.commit()
            try:
                conn.execute(text("INSERT INTO project_history (project_code, entry_type, log_date, summary, created_by, updated_by) VALUES ('P001','Report','2025-01-06','dup','sys','sys')"))
                conn.commit()
                assert False, "should violate unique(project_code, log_date)"
            except Exception:
                conn.rollback()
            try:
                conn.execute(text("INSERT INTO project_history (project_code, entry_type, log_date, summary, created_by, updated_by) VALUES ('P001','NotValid','2025-01-13','bad','sys','sys')"))
                conn.commit()
                assert False, "should violate CHECK(entry_type)"
            except Exception:
                conn.rollback()

            # category CHECK (Development/EPC/Finance/Investment)
            conn.execute(text("INSERT INTO project_history (project_code, entry_type, log_date, summary, category, created_by, updated_by) VALUES ('P001','Report','2025-01-20','ok','Development','sys','sys')"))
            conn.commit()
            try:
                conn.execute(text("INSERT INTO project_history (project_code, entry_type, log_date, summary, category, created_by, updated_by) VALUES ('P001','Report','2025-01-27','ok','InvalidCat','sys','sys')"))
                conn.commit()
                assert False, "should violate CHECK(category)"
            except Exception:
                conn.rollback()

            # weekly_report_analysis unique (project_code, cw_label, language)
            conn.execute(text("INSERT INTO weekly_report_analysis (project_code, cw_label, language, created_by) VALUES ('P001','CW02','EN','sys')"))
            conn.commit()
            try:
                conn.execute(text("INSERT INTO weekly_report_analysis (project_code, cw_label, language, created_by) VALUES ('P001','CW02','EN','sys')"))
                conn.commit()
                assert False, "should violate unique(project_code, cw_label, language)"
            except Exception:
                conn.rollback()

import os
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


load_dotenv()


def _get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Please configure backend/.env or environment variable.")
    return database_url


def get_engine(url: Optional[str] = None) -> Engine:
    effective_url = url or _get_database_url()
    engine = create_engine(effective_url, pool_pre_ping=True, future=True)
    return engine


# Global engine and session factory for application use
engine: Engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



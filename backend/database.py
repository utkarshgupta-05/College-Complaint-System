"""
backend/database.py
-------------------
Database engine, session management, and base declarative class.
Supports PostgreSQL (production approved) with SQLite for development and testing.
Strictly disallows SQLite in production mode.
"""

from __future__ import annotations

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.config import settings

logger = logging.getLogger(__name__)

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if settings.ENV == "production" and is_sqlite:
    raise RuntimeError(
        "PRODUCTION SECURITY ERROR: Prohibited from using SQLite in production mode. "
        "A valid PostgreSQL connection string is required."
    )

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables and log dialect confirmation."""
    dialect_name = engine.dialect.name
    masked_url = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
    logger.info(
        "Database initialized. Engine dialect: '%s' | Environment: '%s' | Endpoint: '%s'",
        dialect_name, settings.ENV, masked_url
    )
    Base.metadata.create_all(bind=engine)

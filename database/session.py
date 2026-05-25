"""
database/session.py

SQLAlchemy engine and session factory.

Supports both SQLite (local dev / tests) and PostgreSQL (production).
Override DATABASE_URL in .env to switch.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings


def make_engine(database_url: str = settings.database_url):
    """Create a sync SQLAlchemy engine for the given URL."""
    connect_args = (
        {"check_same_thread": False}
        if database_url.startswith("sqlite")
        else {}
    )
    return create_engine(database_url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Session:
    """Return a new database session. Caller is responsible for closing it."""
    return SessionLocal()

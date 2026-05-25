"""
api/deps.py

FastAPI dependency providers.
"""

from typing import Generator
from sqlalchemy.orm import Session
from database.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session; close it when the request is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

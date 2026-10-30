"""
Database session management and connection handling using SQLAlchemy 2.0.
Configured for SQLite by default, fully compatible with PostgreSQL.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# Engine setup: handle SQLite multi-threading correctly
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide an isolated database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

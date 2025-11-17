"""
Database Connection Utility

Provides database connection and session management for the Job Pricing Engine.
Uses connection pooling and follows production-ready patterns.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from job_pricing.core.config import get_settings
from job_pricing.models import Base

logger = logging.getLogger(__name__)
settings = get_settings()


# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections when pool is full
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.ENVIRONMENT == "development",  # Log SQL in dev mode
)


# Configure SQLite-like behavior for PostgreSQL (if needed)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Event listener for database connection.
    Can be used to set connection-level parameters.
    """
    pass


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI routes.
    Provides a database session and ensures it's closed after use.

    Usage in FastAPI:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use this for manual session management outside of FastAPI.

    Usage:
        with get_db_context() as db:
            items = db.query(Item).all()
            # Session automatically commits on success
            # Session automatically rollsback on exception

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    WARNING: This creates tables based on SQLAlchemy models.
    For production, use Alembic migrations instead!

    Usage:
        # Only for development/testing
        from job_pricing.utils.database import init_db
        init_db()
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """
    Drop all tables from the database.
    WARNING: This is destructive! Use only for testing!

    Usage:
        # Only for testing
        from job_pricing.utils.database import drop_all_tables
        drop_all_tables()
    """
    Base.metadata.drop_all(bind=engine)


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return False

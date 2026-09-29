"""Database connection, session management, and base model."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


def _get_engine(database_url: str | None = None):
    """Create database engine with appropriate configuration."""
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./data/business.db")

    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.getenv("DEBUG", "false").lower() == "true",
        )
        # Enable WAL mode and foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        engine = create_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=os.getenv("DEBUG", "false").lower() == "true",
        )

    return engine


# Module-level engine and session factory
_engine = None
_SessionLocal = None


def get_engine(database_url: str | None = None):
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = _get_engine(database_url)
    return _engine


def get_session_factory(database_url: str | None = None) -> sessionmaker:
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(database_url),
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI - yields a database session."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions outside FastAPI."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db(database_url: str | None = None):
    """Initialize database tables. Use for development/testing only."""
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)


def reset_engine():
    """Reset the engine and session factory. Useful for testing."""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None

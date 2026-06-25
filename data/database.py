"""Database initialization and session management."""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from config import settings

# Create declarative base for models (independent from open_webui)
Base = declarative_base()


def get_database_url() -> str:
    """Get database URL, creating SQLite directory if needed."""
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    return db_url


# Create engine with appropriate pool settings
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        get_database_url(),
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DATABASE_ECHO,
    )
else:
    engine = create_engine(
        get_database_url(),
        echo=settings.DATABASE_ECHO,
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def close_database():
    """Close database connection."""
    engine.dispose()

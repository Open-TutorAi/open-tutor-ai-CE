"""Dedicated database for engagement metrics.

Engagement data lives in its own SQLite file (``var/engagement.db``),
fully isolated from the main application database.
Override the location with the ``ENGAGEMENT_DATABASE_URL`` env var.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Independent declarative base — NOT shared with data.database.Base, so the
# engagement table is never created in the main application DB.
EngagementBase = declarative_base()

ENGAGEMENT_DATABASE_URL = os.environ.get(
    "ENGAGEMENT_DATABASE_URL", "sqlite:///./var/engagement.db"
)


def _make_engine(url: str):
    if url.startswith("sqlite"):
        # Ensure the parent directory exists for a file-based SQLite DB.
        if url.startswith("sqlite:///") and ":memory:" not in url:
            path = url.replace("sqlite:///", "")
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url)


engagement_engine = _make_engine(ENGAGEMENT_DATABASE_URL)

EngagementSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engagement_engine
)


def init_engagement_db() -> None:
    """Create the engagement table in its dedicated database."""
    from sqlalchemy import inspect, text
    from . import models  # noqa: F401 — register models on EngagementBase

    inspector = inspect(engagement_engine)
    if inspector.has_table("engagement_metrics"):
        columns = {c["name"] for c in inspector.get_columns("engagement_metrics")}
        if not {"user_id", "text_score", "created_at"}.issubset(columns):
            print(
                "[Engagement DB] Dropping incompatible legacy engagement_metrics "
                "table and recreating with the current schema.",
                flush=True,
            )
            with engagement_engine.begin() as conn:
                conn.execute(text("DROP TABLE engagement_metrics"))

    EngagementBase.metadata.create_all(bind=engagement_engine)


def get_engagement_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session bound to the engagement DB."""
    db = EngagementSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def engagement_session() -> Generator[Session, None, None]:
    """Context manager for engagement sessions outside the request lifecycle."""
    db = EngagementSessionLocal()
    try:
        yield db
    finally:
        db.close()

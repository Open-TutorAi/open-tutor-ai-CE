# tests/conftest.py
"""Pytest configuration and fixtures."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("DEBUG", "true")
# Keep engagement metrics in an isolated in-memory DB during tests.
os.environ.setdefault("ENGAGEMENT_DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from data.database import Base, get_db
from ai.engagement.database import (
    EngagementBase,
    engagement_engine,
    EngagementSessionLocal,
    get_engagement_db,
)
from gateway.http.app import create_app


@pytest.fixture
def db():
    """Create test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def engagement_db():
    """Isolated in-memory engagement DB, reset per test."""
    EngagementBase.metadata.create_all(bind=engagement_engine)
    session = EngagementSessionLocal()
    try:
        yield session
    finally:
        session.close()
        EngagementBase.metadata.drop_all(bind=engagement_engine)


@pytest.fixture
def client(db, engagement_db):
    """Create test client."""

    def override_get_db():
        yield db

    def override_get_engagement_db():
        session = EngagementSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_engagement_db] = override_get_engagement_db

    return TestClient(app)

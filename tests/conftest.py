# tests/conftest.py
"""Pytest configuration and fixtures."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("DEBUG", "true")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from data.database import Base, get_db
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
def client(db):
    """Create test client."""

    def override_get_db():
        yield db

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)

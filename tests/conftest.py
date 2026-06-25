# tests/conftest.py
"""Pytest configuration and fixtures."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("DEBUG", "true")

import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext as _CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import accounts.users.service as _identity_service
from data.database import Base, get_db
from gateway.http.app import create_app

# Speed up the suite: bcrypt at its default cost (~12 rounds) dominates the run
# because the tests create hundreds of users (signup + signin both hash/verify).
# Drop to bcrypt's minimum cost for tests only — production keeps the strong
# default configured in accounts/users/service.py.
_identity_service._pwd_context = _CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4
)


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

# tests/test_auth.py
"""Tests for authentication endpoints."""

import pytest


@pytest.mark.integration
def test_signin_is_rate_limited_after_repeated_attempts(client):
    client.post(
        "/auths/signup",
        json={
            "email": "ratelimit@example.com",
            "name": "Rate Limit",
            "password": "secure_password_123",
        },
    )

    payload = {"email": "ratelimit@example.com", "password": "wrong_password"}
    statuses = [
        client.post("/auths/signin", json=payload).status_code for _ in range(11)
    ]

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


def test_signup(client):
    response = client.post(
        "/auths/signup",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "secure_password_123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token_type"] == "Bearer"
    assert data["email"] == "test@example.com"


def test_signup_duplicate_email(client):
    client.post(
        "/auths/signup",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "secure_password_123",
        },
    )
    response = client.post(
        "/auths/signup",
        json={
            "email": "test@example.com",
            "name": "Another User",
            "password": "different_password_123",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_signin(client):
    client.post(
        "/auths/signup",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "secure_password_123",
        },
    )
    response = client.post(
        "/auths/signin",
        json={"email": "test@example.com", "password": "secure_password_123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["email"] == "test@example.com"


def test_login_alias(client):
    """POST /auths/login is kept as alias for /auths/signin."""
    client.post(
        "/auths/signup",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "secure_password_123",
        },
    )
    response = client.post(
        "/auths/login",
        json={"email": "test@example.com", "password": "secure_password_123"},
    )
    assert response.status_code == 200
    assert "token" in response.json()


def test_login_invalid_password(client):
    client.post(
        "/auths/signup",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "secure_password_123",
        },
    )
    response = client.post(
        "/auths/login",
        json={"email": "test@example.com", "password": "wrong_password"},
    )
    assert response.status_code == 401

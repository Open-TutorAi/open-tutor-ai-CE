"""Tests for teacher availability status and office hours."""

import pytest
from fastapi.testclient import TestClient


def _signup_and_token(client: TestClient, name: str, email: str, role: str) -> str:
    r = client.post(
        "/auths/signup",
        json={"name": name, "email": email, "password": "pass1234!", "role": role},
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _get_user_id(client: TestClient, token: str) -> str:
    r = client.get("/api/v1/auths/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_get_default_availability(client):
    teacher_token = _signup_and_token(client, "Teacher T", "t@test.com", "teacher")
    teacher_id = _get_user_id(client, teacher_token)

    r = client.get(
        f"/api/v1/teachers/availability/{teacher_id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "available"
    assert data["teacher_id"] == teacher_id
    assert data["office_hours_start"] is None
    assert data["office_hours_end"] is None


def test_update_availability_status(client):
    teacher_token = _signup_and_token(client, "Teacher B", "tb@test.com", "teacher")

    r = client.put(
        "/api/v1/teachers/availability",
        json={"status": "busy"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "busy"


def test_update_availability_with_office_hours(client):
    teacher_token = _signup_and_token(client, "Teacher OH", "toh@test.com", "teacher")

    r = client.put(
        "/api/v1/teachers/availability",
        json={
            "status": "available",
            "office_hours_start": "08:00",
            "office_hours_end": "16:30",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["office_hours_start"] == "08:00"
    assert data["office_hours_end"] == "16:30"


def test_update_availability_invalid_status(client):
    teacher_token = _signup_and_token(client, "Teacher I", "ti@test.com", "teacher")

    r = client.put(
        "/api/v1/teachers/availability",
        json={"status": "invisible"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 400


def test_non_teacher_cannot_update_availability(client):
    parent_token = _signup_and_token(client, "Parent P", "pp@test.com", "parent")

    r = client.put(
        "/api/v1/teachers/availability",
        json={"status": "available"},
        headers={"Authorization": f"Bearer {parent_token}"},
    )
    assert r.status_code == 403


def test_parent_can_read_teacher_availability(client):
    teacher_token = _signup_and_token(client, "Teacher X", "tx@test.com", "teacher")
    teacher_id = _get_user_id(client, teacher_token)
    parent_token = _signup_and_token(client, "Parent Y", "py@test.com", "parent")

    # Teacher sets offline
    client.put(
        "/api/v1/teachers/availability",
        json={"status": "offline"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    r = client.get(
        f"/api/v1/teachers/availability/{teacher_id}",
        headers={"Authorization": f"Bearer {parent_token}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "offline"


def test_availability_is_upserted_not_duplicated(client):
    teacher_token = _signup_and_token(client, "Teacher U", "tu@test.com", "teacher")

    client.put(
        "/api/v1/teachers/availability",
        json={"status": "available"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    client.put(
        "/api/v1/teachers/availability",
        json={"status": "busy"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    teacher_id = _get_user_id(client, teacher_token)
    r = client.get(
        f"/api/v1/teachers/availability/{teacher_id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.json()["status"] == "busy"

"""Tests for guardian endpoints."""

import pytest


def _signup(client, email, name, role="user"):
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": name, "password": "pass1234", "role": role},
    )
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture
def teacher_token(client):
    # First user becomes admin — sign up a dummy admin first
    _signup(client, "admin@test.com", "Admin", role="admin")
    return _signup(client, "teacher@test.com", "Teacher", role="teacher")


@pytest.fixture
def student_token(client):
    _signup(client, "admin@test.com", "Admin", role="admin")
    _signup(client, "teacher@test.com", "Teacher", role="teacher")
    return _signup(client, "student@test.com", "Student", role="user")


STUDENT_ID = "fake-student-id"


def test_list_guardians_empty(client, teacher_token):
    r = client.get(
        f"/api/v1/guardians/student/{STUDENT_ID}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_invite_guardian(client, teacher_token):
    r = client.post(
        f"/api/v1/guardians/student/{STUDENT_ID}/invite",
        json={"email": "parent@example.com", "relationship": "Mother"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "parent@example.com"
    assert data["relationship"] == "Mother"
    assert data["status"] == "pending"
    assert data["linked_at"] is None


def test_invite_duplicate_returns_existing(client, teacher_token):
    client.post(
        f"/api/v1/guardians/student/{STUDENT_ID}/invite",
        json={"email": "parent@example.com", "relationship": "Mother"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    r = client.post(
        f"/api/v1/guardians/student/{STUDENT_ID}/invite",
        json={"email": "parent@example.com", "relationship": "Mother"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 201

    r2 = client.get(
        f"/api/v1/guardians/student/{STUDENT_ID}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert len(r2.json()) == 1


def test_list_guardians_after_invite(client, teacher_token):
    client.post(
        f"/api/v1/guardians/student/{STUDENT_ID}/invite",
        json={"email": "parent@example.com", "relationship": "Father"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    r = client.get(
        f"/api/v1/guardians/student/{STUDENT_ID}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_resend_invitation(client, teacher_token):
    invite_r = client.post(
        f"/api/v1/guardians/student/{STUDENT_ID}/invite",
        json={"email": "parent@example.com", "relationship": "Guardian"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    gid = invite_r.json()["id"]
    r = client.post(
        f"/api/v1/guardians/{gid}/resend",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 200
    assert "resent" in r.json()["message"]


def test_resend_not_found(client, teacher_token):
    r = client.post(
        "/api/v1/guardians/nonexistent-id/resend",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 404


def test_get_contact(client, teacher_token):
    invite_r = client.post(
        f"/api/v1/guardians/student/{STUDENT_ID}/invite",
        json={"email": "parent@example.com", "relationship": "Other"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    gid = invite_r.json()["id"]
    r = client.get(
        f"/api/v1/guardians/{gid}/contact",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "parent@example.com"
    assert data["relationship"] == "Other"


def test_student_cannot_invite(client, student_token):
    r = client.post(
        f"/api/v1/guardians/student/{STUDENT_ID}/invite",
        json={"email": "parent@example.com", "relationship": "Mother"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert r.status_code == 403


def test_requires_auth(client):
    r = client.get(f"/api/v1/guardians/student/{STUDENT_ID}")
    assert r.status_code == 403

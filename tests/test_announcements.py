"""Tests for classroom announcements (teacher creates, parent reads)."""

import pytest
from fastapi.testclient import TestClient


def _signup_and_token(client: TestClient, name: str, email: str, role: str) -> str:
    r = client.post(
        "/auths/signup",
        json={"name": name, "email": email, "password": "pass1234!", "role": role},
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _create_ann(
    client: TestClient,
    token: str,
    title: str = "Test Ann",
    content: str = "Content here",
    priority: str = "normal",
) -> dict:
    r = client.post(
        "/api/v1/announcements",
        json={"title": title, "content": content, "priority": priority},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def tokens(client):
    teacher_token = _signup_and_token(client, "Teacher T", "teacher@ann.com", "teacher")
    parent_token = _signup_and_token(client, "Parent P", "parent@ann.com", "parent")
    return {"teacher": teacher_token, "parent": parent_token}


def test_teacher_can_create_announcement(client, tokens):
    ann = _create_ann(client, tokens["teacher"])
    assert ann["title"] == "Test Ann"
    assert ann["priority"] == "normal"
    assert ann["is_published"] is False


def test_parent_cannot_create_announcement(client, tokens):
    r = client.post(
        "/api/v1/announcements",
        json={"title": "X", "content": "Y"},
        headers={"Authorization": f"Bearer {tokens['parent']}"},
    )
    assert r.status_code == 403


def test_invalid_priority_rejected(client, tokens):
    r = client.post(
        "/api/v1/announcements",
        json={"title": "X", "content": "Y", "priority": "critical"},
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 400


def test_list_teacher_announcements(client, tokens):
    _create_ann(client, tokens["teacher"], title="Ann 1")
    _create_ann(client, tokens["teacher"], title="Ann 2")

    r = client.get(
        "/api/v1/announcements/mine",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_publish_announcement(client, tokens):
    ann = _create_ann(client, tokens["teacher"])
    r = client.post(
        f"/api/v1/announcements/{ann['id']}/publish",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 200
    assert r.json()["is_published"] is True


def test_unpublish_announcement(client, tokens):
    ann = _create_ann(client, tokens["teacher"])
    client.post(
        f"/api/v1/announcements/{ann['id']}/publish",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    r = client.post(
        f"/api/v1/announcements/{ann['id']}/unpublish",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 200
    assert r.json()["is_published"] is False


def test_edit_unpublished_announcement(client, tokens):
    ann = _create_ann(client, tokens["teacher"], title="Original")
    r = client.patch(
        f"/api/v1/announcements/{ann['id']}",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"


def test_cannot_edit_published_announcement(client, tokens):
    ann = _create_ann(client, tokens["teacher"])
    client.post(
        f"/api/v1/announcements/{ann['id']}/publish",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    r = client.patch(
        f"/api/v1/announcements/{ann['id']}",
        json={"title": "Too Late"},
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 403


def test_delete_announcement(client, tokens):
    ann = _create_ann(client, tokens["teacher"])
    r = client.delete(
        f"/api/v1/announcements/{ann['id']}",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 200
    assert r.json()["deleted"] is True


def test_parent_sees_only_published(client, tokens):
    _create_ann(client, tokens["teacher"], title="Draft — not visible")
    ann = _create_ann(client, tokens["teacher"], title="Published — visible")
    client.post(
        f"/api/v1/announcements/{ann['id']}/publish",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )

    r = client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {tokens['parent']}"},
    )
    assert r.status_code == 200
    titles = [a["title"] for a in r.json()]
    assert "Published — visible" in titles
    assert "Draft — not visible" not in titles


def test_mark_read_and_unread_count(client, tokens):
    ann = _create_ann(client, tokens["teacher"])
    client.post(
        f"/api/v1/announcements/{ann['id']}/publish",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )

    r = client.get(
        "/api/v1/announcements/unread-count",
        headers={"Authorization": f"Bearer {tokens['parent']}"},
    )
    initial_count = r.json()["unread_count"]
    assert initial_count >= 1

    client.post(
        f"/api/v1/announcements/{ann['id']}/read",
        headers={"Authorization": f"Bearer {tokens['parent']}"},
    )

    r = client.get(
        "/api/v1/announcements/unread-count",
        headers={"Authorization": f"Bearer {tokens['parent']}"},
    )
    assert r.json()["unread_count"] == initial_count - 1


def test_teacher_cannot_delete_other_teachers_announcement(client, tokens):
    other_teacher_token = _signup_and_token(
        client, "Other Teacher", "other@ann.com", "teacher"
    )
    ann = _create_ann(client, other_teacher_token)

    r = client.delete(
        f"/api/v1/announcements/{ann['id']}",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )
    assert r.status_code == 403


def test_announcement_is_read_false_initially(client, tokens):
    ann = _create_ann(client, tokens["teacher"])
    client.post(
        f"/api/v1/announcements/{ann['id']}/publish",
        headers={"Authorization": f"Bearer {tokens['teacher']}"},
    )

    r = client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {tokens['parent']}"},
    )
    matching = [a for a in r.json() if a["id"] == ann["id"]]
    assert matching
    assert matching[0]["is_read"] is False

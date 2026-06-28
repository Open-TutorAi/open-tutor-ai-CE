"""Tests for message attachment upload and download."""

import io
import pytest
from fastapi.testclient import TestClient


def _signup_and_token(client: TestClient, name: str, email: str, role: str) -> str:
    r = client.post(
        "/auths/signup",
        json={"name": name, "email": email, "password": "pass1234!", "role": role},
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _link(client: TestClient, admin_token: str, parent_id: str, student_id: str):
    r = client.post(
        "/api/v1/messages/admin/link-parent-student",
        json={"parent_id": parent_id, "student_id": student_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text


def _link_teacher(client: TestClient, admin_token: str, teacher_id: str, student_id: str):
    r = client.post(
        "/api/v1/messages/admin/link-teacher-student",
        json={"teacher_id": teacher_id, "student_id": student_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200, r.text


def _get_user_id(client: TestClient, token: str) -> str:
    r = client.get("/api/v1/auths/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _create_conversation(
    client: TestClient, parent_token: str, teacher_id: str, student_id: str
) -> str:
    r = client.post(
        "/api/v1/messages/send",
        json={
            "receiver_id": teacher_id,
            "student_id": student_id,
            "content": "Hello teacher",
        },
        headers={"Authorization": f"Bearer {parent_token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()["message"]["conversation_id"]


@pytest.fixture
def setup(client):
    admin_token = _signup_and_token(client, "Admin", "admin@test.com", "admin")
    parent_token = _signup_and_token(client, "Parent P", "parent@test.com", "parent")
    teacher_token = _signup_and_token(client, "Teacher T", "teacher@test.com", "teacher")
    student_token = _signup_and_token(client, "Student S", "student@test.com", "user")

    admin_id = _get_user_id(client, admin_token)
    parent_id = _get_user_id(client, parent_token)
    teacher_id = _get_user_id(client, teacher_token)
    student_id = _get_user_id(client, student_token)

    _link(client, admin_token, parent_id, student_id)
    _link_teacher(client, admin_token, teacher_id, student_id)

    conv_id = _create_conversation(client, parent_token, teacher_id, student_id)

    return {
        "parent_token": parent_token,
        "teacher_token": teacher_token,
        "teacher_id": teacher_id,
        "student_id": student_id,
        "conv_id": conv_id,
    }


def test_upload_pdf_attachment(client, setup, tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"%PDF-1.4 test content")

    with open(pdf, "rb") as f:
        r = client.post(
            f"/api/v1/messages/conversations/{setup['conv_id']}/attachments",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers={"Authorization": f"Bearer {setup['parent_token']}"},
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["original_filename"] == "test.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] > 0
    assert "id" in data


def test_upload_image_attachment(client, setup, tmp_path):
    img = tmp_path / "photo.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)  # minimal JPEG header

    with open(img, "rb") as f:
        r = client.post(
            f"/api/v1/messages/conversations/{setup['conv_id']}/attachments",
            files={"file": ("photo.jpg", f, "image/jpeg")},
            headers={"Authorization": f"Bearer {setup['parent_token']}"},
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["mime_type"] == "image/jpeg"


def test_upload_blocked_mime_type(client, setup, tmp_path):
    exe = tmp_path / "evil.exe"
    exe.write_bytes(b"MZ" + b"\x00" * 100)

    with open(exe, "rb") as f:
        r = client.post(
            f"/api/v1/messages/conversations/{setup['conv_id']}/attachments",
            files={"file": ("evil.exe", f, "application/x-msdownload")},
            headers={"Authorization": f"Bearer {setup['parent_token']}"},
        )
    assert r.status_code == 400


def test_upload_outsider_cannot_attach(client, setup, tmp_path):
    outsider_token = _signup_and_token(
        client, "Outsider O", "outsider@test.com", "parent"
    )
    pdf = tmp_path / "snoop.pdf"
    pdf.write_bytes(b"%PDF-1.4 snooping")

    with open(pdf, "rb") as f:
        r = client.post(
            f"/api/v1/messages/conversations/{setup['conv_id']}/attachments",
            files={"file": ("snoop.pdf", f, "application/pdf")},
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
    assert r.status_code == 403


def test_send_message_with_attachment_id(client, setup, tmp_path):
    # Upload an attachment first
    pdf = tmp_path / "attach.pdf"
    pdf.write_bytes(b"%PDF-1.4 attached")

    with open(pdf, "rb") as f:
        r = client.post(
            f"/api/v1/messages/conversations/{setup['conv_id']}/attachments",
            files={"file": ("attach.pdf", f, "application/pdf")},
            headers={"Authorization": f"Bearer {setup['parent_token']}"},
        )
    assert r.status_code == 200
    att_id = r.json()["id"]

    # Send message referencing the attachment
    r = client.post(
        "/api/v1/messages/send",
        json={
            "receiver_id": setup["teacher_id"],
            "student_id": setup["student_id"],
            "content": "See attached PDF",
            "attachment_ids": [att_id],
        },
        headers={"Authorization": f"Bearer {setup['parent_token']}"},
    )
    assert r.status_code == 200
    msg = r.json()["message"]
    assert len(msg["attachments"]) == 1
    assert msg["attachments"][0]["id"] == att_id


def test_messages_include_attachments_on_fetch(client, setup, tmp_path):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 doc")

    with open(pdf, "rb") as f:
        r = client.post(
            f"/api/v1/messages/conversations/{setup['conv_id']}/attachments",
            files={"file": ("doc.pdf", f, "application/pdf")},
            headers={"Authorization": f"Bearer {setup['teacher_token']}"},
        )
    att_id = r.json()["id"]

    client.post(
        "/api/v1/messages/send",
        json={
            "receiver_id": _get_user_id(client, setup["parent_token"]),
            "student_id": setup["student_id"],
            "content": "Here's the doc",
            "attachment_ids": [att_id],
        },
        headers={"Authorization": f"Bearer {setup['teacher_token']}"},
    )

    r = client.get(
        f"/api/v1/messages/conversations/{setup['conv_id']}",
        headers={"Authorization": f"Bearer {setup['parent_token']}"},
    )
    assert r.status_code == 200
    messages = r.json()
    msgs_with_att = [m for m in messages if m["attachments"]]
    assert msgs_with_att, "No messages with attachments found"

from common.exceptions import AuthorizationError
# tests/test_announcements.py
"""Tests for the classroom announcements (stream) feature."""


import uuid

import pytest

from data.models import Classroom, User
from learning.announcements.service import AnnouncementsService
from learning.classrooms.repository import ClassroomRepository
from learning.classrooms.schemas import ClassroomCreate


def _make_user(db, email, name):
    user = User(id=str(uuid.uuid4()), email=email, name=name, password_hash="hashed")
    db.add(user)
    db.commit()
    return user


def _make_classroom(db, owner_id, name="Class"):
    return ClassroomRepository(db, Classroom).create(
        owner_id, ClassroomCreate(name=name)
    )


def _enroll(db, classroom_id, student_id):
    return ClassroomRepository(db, Classroom).add_student(classroom_id, student_id)


def _signup(client, email, name, role=None):
    payload = {"email": email, "name": name, "password": "pass1234!"}
    if role:
        payload["role"] = role
    return client.post("/auths/signup", json=payload).json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit
def test_owner_can_create_announcement(db):
    owner = _make_user(db, "owner-ann1@t.com", "Owner1")
    classroom = _make_classroom(db, owner.id)
    service = AnnouncementsService(db)

    result = service.create_announcement(classroom.id, owner.id, "Hello class")

    assert result.content == "Hello class"
    assert result.author_id == owner.id
    assert result.author_name == "Owner1"


@pytest.mark.unit
def test_non_owner_cannot_create_announcement(db):
    owner = _make_user(db, "owner-ann2@t.com", "Owner2")
    intruder = _make_user(db, "intruder-ann2@t.com", "Intruder2")
    classroom = _make_classroom(db, owner.id)
    service = AnnouncementsService(db)

    with pytest.raises(AuthorizationError):
        service.create_announcement(classroom.id, intruder.id, "spam")


@pytest.mark.unit
def test_owner_and_enrolled_student_can_list_announcements(db):
    owner = _make_user(db, "owner-ann3@t.com", "Owner3")
    student = _make_user(db, "student-ann3@t.com", "Student3")
    classroom = _make_classroom(db, owner.id)
    _enroll(db, classroom.id, student.id)
    service = AnnouncementsService(db)
    service.create_announcement(classroom.id, owner.id, "Welcome!")

    owner_view = service.list_announcements(classroom.id, owner.id)
    student_view = service.list_announcements(classroom.id, student.id)

    assert len(owner_view) == 1
    assert len(student_view) == 1
    assert owner_view[0].content == "Welcome!"


@pytest.mark.unit
def test_non_enrolled_user_cannot_list_announcements(db):
    owner = _make_user(db, "owner-ann4@t.com", "Owner4")
    outsider = _make_user(db, "outsider-ann4@t.com", "Outsider4")
    classroom = _make_classroom(db, owner.id)
    service = AnnouncementsService(db)
    service.create_announcement(classroom.id, owner.id, "Welcome!")

    with pytest.raises(AuthorizationError):
        service.list_announcements(classroom.id, outsider.id)


@pytest.mark.unit
def test_announcements_ordered_most_recent_first(db):
    owner = _make_user(db, "owner-ann5@t.com", "Owner5")
    classroom = _make_classroom(db, owner.id)
    service = AnnouncementsService(db)
    service.create_announcement(classroom.id, owner.id, "First")
    service.create_announcement(classroom.id, owner.id, "Second")

    result = service.list_announcements(classroom.id, owner.id)

    assert [a.content for a in result] == ["Second", "First"]


@pytest.mark.unit
def test_owner_can_delete_announcement(db):
    owner = _make_user(db, "owner-ann6@t.com", "Owner6")
    classroom = _make_classroom(db, owner.id)
    service = AnnouncementsService(db)
    created = service.create_announcement(classroom.id, owner.id, "Temp post")

    service.delete_announcement(created.id, owner.id)

    assert service.list_announcements(classroom.id, owner.id) == []


@pytest.mark.unit
def test_non_owner_cannot_delete_announcement(db):
    owner = _make_user(db, "owner-ann7@t.com", "Owner7")
    intruder = _make_user(db, "intruder-ann7@t.com", "Intruder7")
    classroom = _make_classroom(db, owner.id)
    service = AnnouncementsService(db)
    created = service.create_announcement(classroom.id, owner.id, "Keep me")

    with pytest.raises(AuthorizationError):
        service.delete_announcement(created.id, intruder.id)


@pytest.mark.integration
def test_announcements_endpoints_full_flow(client):
    owner_token = _signup(client, "owner-ann-api@t.com", "OwnerAPI", role="teacher")
    student_token = _signup(client, "student-ann-api@t.com", "StudentAPI")

    classroom = client.post(
        "/api/classrooms", json={"name": "API Class"}, headers=_auth(owner_token)
    ).json()
    code = client.get(
        f"/api/classrooms/{classroom['id']}", headers=_auth(owner_token)
    ).json()["join_code"]
    client.post(f"/api/classrooms/invites/{code}/redeem", headers=_auth(student_token))

    created = client.post(
        f"/api/classrooms/{classroom['id']}/announcements",
        json={"content": "Premier cours lundi"},
        headers=_auth(owner_token),
    )
    assert created.status_code == 201

    student_post = client.post(
        f"/api/classrooms/{classroom['id']}/announcements",
        json={"content": "spam"},
        headers=_auth(student_token),
    )
    assert student_post.status_code == 403

    student_list = client.get(
        f"/api/classrooms/{classroom['id']}/announcements", headers=_auth(student_token)
    )
    assert student_list.status_code == 200
    assert len(student_list.json()) == 1

    deleted = client.delete(
        f"/api/announcements/{created.json()['id']}", headers=_auth(owner_token)
    )
    assert deleted.status_code == 200

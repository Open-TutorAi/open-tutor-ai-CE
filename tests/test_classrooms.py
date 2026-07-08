from common.exceptions import AuthorizationError
# tests/test_classrooms.py
"""Tests for the classroom repository, service, and HTTP layer."""


import uuid
from datetime import date, datetime

import pytest

from data.models import Classroom, Enrollment, User
from learning.classrooms.repository import ClassroomRepository
from learning.classrooms.schemas import ClassroomCreate, ClassroomOut
from learning.classrooms.service import ClassroomsService


def _make_user(db, email="teacher@t.com", name="Teacher"):
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        name=name,
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    return user


def _signup(client, email, name):
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": name, "password": "pass1234!"},
    )
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_enrollment(db, classroom_id, student_id):
    enrollment = Enrollment(
        id=str(uuid.uuid4()),
        classroom_id=classroom_id,
        student_id=student_id,
        enrolled_at=date.today(),
    )
    db.add(enrollment)
    db.commit()
    return enrollment


# --- Repository tests -------------------------------------------------


@pytest.mark.unit
def test_create_classroom(db):
    owner = _make_user(db)
    repo = ClassroomRepository(db, Classroom)

    classroom = repo.create(owner.id, ClassroomCreate(name="Algebra I"))

    assert classroom.id is not None
    assert classroom.owner_id == owner.id


@pytest.mark.unit
def test_get_by_owner_returns_only_own(db):
    owner_a = _make_user(db, email="a@t.com", name="A")
    owner_b = _make_user(db, email="b@t.com", name="B")
    repo = ClassroomRepository(db, Classroom)
    repo.create(owner_a.id, ClassroomCreate(name="A's class"))
    repo.create(owner_b.id, ClassroomCreate(name="B's class"))

    result = repo.get_by_owner(owner_a.id)

    assert len(result) > 0
    assert all(c.owner_id == owner_a.id for c in result)


@pytest.mark.unit
def test_get_by_owner_includes_student_count(db):
    owner = _make_user(db)
    student_1 = _make_user(db, email="s1@t.com", name="S1")
    student_2 = _make_user(db, email="s2@t.com", name="S2")
    repo = ClassroomRepository(db, Classroom)
    classroom = repo.create(owner.id, ClassroomCreate(name="Class"))
    _make_enrollment(db, classroom.id, student_1.id)
    _make_enrollment(db, classroom.id, student_2.id)

    result = repo.get_by_owner(owner.id)

    found = next(c for c in result if c.id == classroom.id)
    assert found.student_count == 2


@pytest.mark.unit
def test_get_enrolled_classrooms_returns_only_classrooms_student_belongs_to(db):
    owner = _make_user(db)
    student = _make_user(db, email="enrolled@t.com", name="Enrolled")
    other_student = _make_user(db, email="other@t.com", name="Other")
    repo = ClassroomRepository(db, Classroom)
    enrolled_classroom = repo.create(owner.id, ClassroomCreate(name="Joined"))
    other_classroom = repo.create(owner.id, ClassroomCreate(name="Not joined"))
    _make_enrollment(db, enrolled_classroom.id, student.id)
    _make_enrollment(db, other_classroom.id, other_student.id)

    result = repo.get_enrolled_classrooms(student.id)

    assert [c.id for c in result] == [enrolled_classroom.id]
    assert result[0].student_count == 1


@pytest.mark.unit
def test_get_by_id_returns_none_for_unknown(db):
    repo = ClassroomRepository(db, Classroom)

    assert repo.get_by_id(str(uuid.uuid4())) is None


@pytest.mark.unit
def test_delete_removes_row(db):
    owner = _make_user(db)
    repo = ClassroomRepository(db, Classroom)
    classroom = repo.create(owner.id, ClassroomCreate(name="To Delete"))

    repo.delete(classroom.id)

    assert repo.get_by_id(classroom.id) is None


@pytest.mark.unit
def test_delete_does_not_cascade_to_users(db):
    owner = _make_user(db)
    student = _make_user(db, email="student@t.com", name="Student")
    repo = ClassroomRepository(db, Classroom)
    classroom = repo.create(owner.id, ClassroomCreate(name="Class"))
    _make_enrollment(db, classroom.id, student.id)

    repo.delete(classroom.id)

    assert db.query(User).filter(User.id == student.id).first() is not None


# --- Service tests ------------------------------------------------------


@pytest.fixture
def service(db):
    return ClassroomsService(db)


@pytest.mark.unit
def test_create_classroom_returns_schema(service, mocker):
    fake_classroom = mocker.Mock(
        id="classroom-1",
        subject=None,
        course=None,
        objectives=None,
        level=None,
        description=None,
        created_at=datetime.utcnow(),
        owner_id="owner-1",
    )
    fake_classroom.name = "Algebra I"  # "name" is a reserved Mock() kwarg
    mocker.patch.object(service.repo, "create", return_value=fake_classroom)

    result = service.create_classroom("owner-1", ClassroomCreate(name="Algebra I"))

    assert isinstance(result, ClassroomOut)
    assert result.student_count == 0


@pytest.mark.unit
def test_get_my_classrooms_enriches_with_count(service, mocker):
    fake_classrooms = [
        mocker.Mock(
            id="classroom-1",
            subject=None,
            course=None,
            objectives=None,
            level=None,
            description=None,
            created_at=datetime.utcnow(),
            owner_id="owner-1",
            student_count=3,
        ),
        mocker.Mock(
            id="classroom-2",
            subject=None,
            course=None,
            objectives=None,
            level=None,
            description=None,
            created_at=datetime.utcnow(),
            owner_id="owner-1",
            student_count=0,
        ),
    ]
    fake_classrooms[0].name = "A"  # "name" is a reserved Mock() kwarg
    fake_classrooms[1].name = "B"
    mocker.patch.object(service.repo, "get_by_owner", return_value=fake_classrooms)

    result = service.get_my_classrooms("owner-1")

    assert all(isinstance(r, ClassroomOut) for r in result)
    assert [r.student_count for r in result] == [3, 0]


@pytest.mark.unit
def test_list_enrolled_classrooms_flags_active_session(service, db):
    from learning.attendance.service import AttendanceService

    owner = _make_user(db)
    student = _make_user(db, email="enrolled2@t.com", name="Enrolled2")
    repo = ClassroomRepository(db, Classroom)
    with_session = repo.create(owner.id, ClassroomCreate(name="With session"))
    without_session = repo.create(owner.id, ClassroomCreate(name="Without session"))
    _make_enrollment(db, with_session.id, student.id)
    _make_enrollment(db, without_session.id, student.id)

    attendance = AttendanceService(db)
    started = attendance.start_session(
        with_session.id, owner.id, scheduled_at=datetime.utcnow()
    )

    result = service.list_enrolled_classrooms(student.id)

    by_id = {c.id: c for c in result}
    assert by_id[with_session.id].active_session_id == started.id
    assert by_id[without_session.id].active_session_id is None


@pytest.mark.unit
def test_get_classroom_detail_raises_403_if_not_owner(service, mocker):
    fake_classroom = mocker.Mock(id="classroom-1", owner_id="real-owner")
    mocker.patch.object(service.repo, "get_by_id", return_value=fake_classroom)

    with pytest.raises(AuthorizationError):
        service.get_classroom_detail("classroom-1", "someone-else")


@pytest.mark.unit
def test_delete_classroom_raises_403_if_not_owner(service, mocker):
    fake_classroom = mocker.Mock(id="classroom-1", owner_id="real-owner")
    mocker.patch.object(service.repo, "get_by_id", return_value=fake_classroom)

    with pytest.raises(AuthorizationError):
        service.delete_classroom("classroom-1", "someone-else")


# --- API tests ------------------------------------------------------------


@pytest.mark.integration
def test_create_classroom_endpoint_returns_201(client):
    token = _signup(client, "owner-api-1@t.com", "Owner1")

    r = client.post("/api/classrooms", json={"name": "Algebra I"}, headers=_auth(token))

    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Algebra I"
    assert data["student_count"] == 0


@pytest.mark.integration
def test_list_my_classrooms_endpoint_returns_list(client):
    token = _signup(client, "owner-api-2@t.com", "Owner2")
    client.post("/api/classrooms", json={"name": "Class A"}, headers=_auth(token))

    r = client.get("/api/classrooms", headers=_auth(token))

    assert r.status_code == 200
    classrooms = r.json()
    assert isinstance(classrooms, list)
    assert any(c["name"] == "Class A" for c in classrooms)


@pytest.mark.integration
def test_get_classroom_detail_endpoint_returns_403_for_wrong_user(client):
    owner_token = _signup(client, "owner-api-3@t.com", "Owner3")
    created = client.post(
        "/api/classrooms", json={"name": "Private Class"}, headers=_auth(owner_token)
    ).json()
    intruder_token = _signup(client, "intruder-api-1@t.com", "Intruder1")

    r = client.get(f"/api/classrooms/{created['id']}", headers=_auth(intruder_token))

    assert r.status_code == 403


@pytest.mark.integration
def test_delete_classroom_endpoint_returns_403_for_wrong_user(client):
    owner_token = _signup(client, "owner-api-4@t.com", "Owner4")
    created = client.post(
        "/api/classrooms", json={"name": "Class"}, headers=_auth(owner_token)
    ).json()
    intruder_token = _signup(client, "intruder-api-2@t.com", "Intruder2")

    r = client.delete(f"/api/classrooms/{created['id']}", headers=_auth(intruder_token))

    assert r.status_code == 403


@pytest.mark.integration
def test_delete_classroom_endpoint_returns_200_and_keeps_student(client, db):
    owner_token = _signup(client, "owner-api-5@t.com", "Owner5")
    created = client.post(
        "/api/classrooms", json={"name": "Class"}, headers=_auth(owner_token)
    ).json()
    _signup(client, "student-api-1@t.com", "Student1")
    student = db.query(User).filter(User.email == "student-api-1@t.com").first()
    _make_enrollment(db, created["id"], student.id)

    r = client.delete(f"/api/classrooms/{created['id']}", headers=_auth(owner_token))

    assert r.status_code == 200
    assert "message" in r.json()
    assert db.query(User).filter(User.id == student.id).first() is not None

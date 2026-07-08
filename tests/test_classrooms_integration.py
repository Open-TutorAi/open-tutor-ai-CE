# tests/test_classrooms_integration.py
"""End-to-end backend integration tests for the teacher classroom feature.

Exercises the full sequence-diagram scenarios over a real SQLite DB + a real
FastAPI TestClient (no mocking), covering classrooms + attendance together.
"""


import uuid
from datetime import date, datetime

import pytest
from sqlalchemy.orm import sessionmaker

from data.models import Classroom, ClassSession, Enrollment, Presence, User
from gateway.http.routers.auth import _create_token
from learning.attendance.repository import AttendanceRepository
from learning.classrooms.repository import ClassroomRepository
from learning.classrooms.schemas import ClassroomCreate


def _signup(client, email, name, role=None):
    payload = {"email": email, "name": name, "password": "pass1234!"}
    if role:
        payload["role"] = role
    r = client.post("/auths/signup", json=payload)
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_user(db, email, name):
    user = User(id=str(uuid.uuid4()), email=email, name=name, password_hash="hashed")
    db.add(user)
    db.commit()
    return user


def _enroll(db, classroom_id, student_id):
    db.add(
        Enrollment(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            student_id=student_id,
            enrolled_at=date.today(),
        )
    )
    db.commit()


@pytest.mark.integration
def test_scenario_a_teacher_creates_lists_and_sees_zero_students(client):
    token = _signup(client, "teacher-a@t.com", "Teacher A", role="teacher")

    created = client.post(
        "/api/classrooms",
        json={"name": "Algebra I", "subject": "Math"},
        headers=_auth(token),
    )
    assert created.status_code == 201
    classroom = created.json()
    assert classroom["student_count"] == 0

    listed = client.get("/api/classrooms", headers=_auth(token))
    assert listed.status_code == 200
    assert any(
        c["id"] == classroom["id"] and c["student_count"] == 0 for c in listed.json()
    )


@pytest.mark.integration
def test_scenario_b_teacher_adds_student_other_teacher_denied(client, db):
    owner_token = _signup(client, "teacher-b@t.com", "Teacher B", role="teacher")
    other_token = _signup(client, "teacher-b2@t.com", "Teacher B2", role="teacher")
    student = _make_user(db, "student-b@t.com", "Student B")

    created = client.post(
        "/api/classrooms", json={"name": "Biology"}, headers=_auth(owner_token)
    ).json()

    # No enrollment HTTP endpoint exists yet — enroll directly via the repository.
    ClassroomRepository(db, Classroom).add_student(created["id"], student.id)

    detail = client.get(f"/api/classrooms/{created['id']}", headers=_auth(owner_token))
    assert detail.status_code == 200
    assert detail.json()["student_count"] == 1

    denied = client.get(f"/api/classrooms/{created['id']}", headers=_auth(other_token))
    assert denied.status_code == 403


@pytest.mark.integration
def test_scenario_d_teacher_deletes_classroom_student_row_intact(client, db):
    owner_token = _signup(client, "teacher-d@t.com", "Teacher D", role="teacher")
    student = _make_user(db, "student-d@t.com", "Student D")

    created = client.post(
        "/api/classrooms", json={"name": "Chemistry"}, headers=_auth(owner_token)
    ).json()
    ClassroomRepository(db, Classroom).add_student(created["id"], student.id)

    deleted = client.delete(
        f"/api/classrooms/{created['id']}", headers=_auth(owner_token)
    )
    assert deleted.status_code == 200

    assert db.query(User).filter(User.id == student.id).first() is not None


@pytest.mark.integration
def test_scenario_e_session_lifecycle_updates_stats_and_history(client, db):
    owner_token = _signup(client, "teacher-e@t.com", "Teacher E", role="teacher")
    student_1 = _make_user(db, "student-e1@t.com", "Student E1")
    student_2 = _make_user(db, "student-e2@t.com", "Student E2")

    created = client.post(
        "/api/classrooms", json={"name": "Physics"}, headers=_auth(owner_token)
    ).json()
    repo = ClassroomRepository(db, Classroom)
    repo.add_student(created["id"], student_1.id)
    repo.add_student(created["id"], student_2.id)

    started = client.post(
        f"/api/classrooms/{created['id']}/sessions",
        json={"scheduled_at": datetime.utcnow().isoformat(), "subject": "Physics"},
        headers=_auth(owner_token),
    )
    assert started.status_code == 201
    session = started.json()

    presences_resp = client.get(
        f"/api/sessions/{session['id']}/presences", headers=_auth(owner_token)
    )
    assert presences_resp.status_code == 200
    presences = presences_resp.json()
    assert len(presences) == 2
    assert all(p["status"] == "ABSENT" for p in presences)

    # Student 2 enters the live session — this is what actually marks them present.
    student_2_token = _create_token(student_2.id)
    joined = client.post(
        f"/api/sessions/{session['id']}/join", headers=_auth(student_2_token)
    )
    assert joined.status_code == 200
    assert joined.json()["status"] == "PRESENT"

    stats = client.get(
        f"/api/classrooms/{created['id']}/attendance-stats", headers=_auth(owner_token)
    ).json()
    assert stats["sessions_count"] == 1
    assert stats["total_absences"] == 1
    assert stats["total_lates"] == 0
    assert stats["avg_rate"] == pytest.approx(50.0)

    history = client.get(
        f"/api/classrooms/{created['id']}/students/{student_1.id}/history",
        headers=_auth(owner_token),
    ).json()
    assert history["presences"] == 0
    assert history["absences"] == 1
    assert history["lates"] == 0

    sessions = client.get(
        f"/api/classrooms/{created['id']}/sessions", headers=_auth(owner_token)
    ).json()
    assert len(sessions) == 1
    assert sessions[0]["present_count"] == 1
    assert sessions[0]["absent_count"] == 1


@pytest.mark.integration
def test_start_session_endpoint_accepts_and_returns_objectives(client):
    owner_token = _signup(
        client, "teacher-objectives@t.com", "Teacher Obj", role="teacher"
    )
    created = client.post(
        "/api/classrooms", json={"name": "Chemistry"}, headers=_auth(owner_token)
    ).json()

    started = client.post(
        f"/api/classrooms/{created['id']}/sessions",
        json={
            "scheduled_at": datetime.utcnow().isoformat(),
            "subject": "Chemistry",
            "objectives": "Balance chemical equations",
        },
        headers=_auth(owner_token),
    )
    assert started.status_code == 201
    session = started.json()
    assert session["subject"] == "Chemistry"
    assert session["objectives"] == "Balance chemical equations"

    sessions = client.get(
        f"/api/classrooms/{created['id']}/sessions", headers=_auth(owner_token)
    ).json()
    assert sessions[0]["objectives"] == "Balance chemical equations"


# --- Regression: writes must survive the request session closing -------
#
# get_db() only closes the session (gateway/.../database.py), it never
# commits. A repository method that only calls session.flush() looks fine
# under the test suite's `db` fixture, because that fixture keeps one
# session open for the whole test — but in real usage each HTTP request
# gets a fresh session that's closed (and therefore rolled back) at the
# end, so the write is silently lost. These tests open a second session on
# the same engine after closing the first, to catch that class of bug.


@pytest.mark.integration
def test_classroom_create_persists_after_session_close(db):
    SessionLocal = sessionmaker(bind=db.bind)

    owner = _make_user(db, "persist-owner@t.com", "Persist Owner")
    classroom = ClassroomRepository(db, Classroom).create(
        owner.id, ClassroomCreate(name="Persisted Classroom")
    )
    classroom_id = classroom.id
    db.close()

    fresh_session = SessionLocal()
    try:
        found = (
            fresh_session.query(Classroom).filter(Classroom.id == classroom_id).first()
        )
        assert found is not None
        assert found.name == "Persisted Classroom"
    finally:
        fresh_session.close()


@pytest.mark.integration
def test_session_and_presence_creation_persist_after_session_close(db):
    SessionLocal = sessionmaker(bind=db.bind)

    owner = _make_user(db, "persist-owner2@t.com", "Persist Owner 2")
    student = _make_user(db, "persist-student@t.com", "Persist Student")
    classroom = ClassroomRepository(db, Classroom).create(
        owner.id, ClassroomCreate(name="Persisted Sessions")
    )
    ClassroomRepository(db, Classroom).add_student(classroom.id, student.id)

    repo = AttendanceRepository(db, ClassSession)
    session_row = repo.create_session(classroom.id, datetime.utcnow())
    presence = repo.create_presence(session_row.id, student.id)
    session_id = session_row.id
    presence_id = presence.id
    db.close()

    fresh_session = SessionLocal()
    try:
        assert (
            fresh_session.query(ClassSession)
            .filter(ClassSession.id == session_id)
            .first()
            is not None
        )
        found_presence = (
            fresh_session.query(Presence).filter(Presence.id == presence_id).first()
        )
        assert found_presence is not None
        assert found_presence.status.value == "PRESENT"
    finally:
        fresh_session.close()


# --- Enrollment endpoints integration tests -------------------------------


@pytest.mark.integration
def test_list_students_empty(client):
    """GET /api/classrooms/{id}/students returns an empty list."""
    token = _signup(client, "teacher-list@t.com", "Teacher List", role="teacher")
    created = client.post(
        "/api/classrooms", json={"name": "Empty Class"}, headers=_auth(token)
    ).json()

    resp = client.get(f"/api/classrooms/{created['id']}/students", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.integration
def test_add_student_by_email(client, db):
    """POST /api/classrooms/{id}/students enrolls an existing student."""
    teacher_token = _signup(client, "teacher-add@t.com", "Teacher Add", role="teacher")
    student = _make_user(db, "student-add@t.com", "Student Add")

    created = client.post(
        "/api/classrooms", json={"name": "Add Class"}, headers=_auth(teacher_token)
    ).json()

    resp = client.post(
        f"/api/classrooms/{created['id']}/students",
        json={"email": student.email},
        headers=_auth(teacher_token),
    )
    assert resp.status_code == 201
    assert resp.json()["student_id"] == student.id
    assert resp.json()["student_name"] == student.name
    assert resp.json()["student_email"] == student.email

    # Verify the student appears in the list
    list_resp = client.get(
        f"/api/classrooms/{created['id']}/students", headers=_auth(teacher_token)
    )
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == student.id


@pytest.mark.integration
def test_add_student_already_enrolled(client, db):
    """POST /api/classrooms/{id}/students with an already enrolled student → 400."""
    teacher_token = _signup(
        client, "teacher-already@t.com", "Teacher Already", role="teacher"
    )
    student = _make_user(db, "student-already@t.com", "Student Already")

    created = client.post(
        "/api/classrooms", json={"name": "Already Class"}, headers=_auth(teacher_token)
    ).json()

    # First enrollment
    client.post(
        f"/api/classrooms/{created['id']}/students",
        json={"email": student.email},
        headers=_auth(teacher_token),
    )

    # Second attempt
    resp = client.post(
        f"/api/classrooms/{created['id']}/students",
        json={"email": student.email},
        headers=_auth(teacher_token),
    )
    assert resp.status_code == 400
    assert "already enrolled" in resp.json()["detail"].lower()


@pytest.mark.integration
def test_add_student_unknown_email(client):
    """POST /api/classrooms/{id}/students with an unknown email → 404."""
    teacher_token = _signup(
        client, "teacher-unknown@t.com", "Teacher Unknown", role="teacher"
    )

    created = client.post(
        "/api/classrooms", json={"name": "Unknown Class"}, headers=_auth(teacher_token)
    ).json()

    resp = client.post(
        f"/api/classrooms/{created['id']}/students",
        json={"email": "unknown@t.com"},
        headers=_auth(teacher_token),
    )
    assert resp.status_code == 404
    assert "user not found" in resp.json()["detail"].lower()


@pytest.mark.integration
def test_remove_student(client, db):
    """DELETE /api/classrooms/{id}/students/{student_id} unenrolls a student."""
    teacher_token = _signup(
        client, "teacher-remove@t.com", "Teacher Remove", role="teacher"
    )
    student = _make_user(db, "student-remove@t.com", "Student Remove")

    created = client.post(
        "/api/classrooms", json={"name": "Remove Class"}, headers=_auth(teacher_token)
    ).json()

    # Enroll
    client.post(
        f"/api/classrooms/{created['id']}/students",
        json={"email": student.email},
        headers=_auth(teacher_token),
    )

    # Unenroll
    resp = client.delete(
        f"/api/classrooms/{created['id']}/students/{student.id}",
        headers=_auth(teacher_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "removed"

    # Verify the list is empty
    list_resp = client.get(
        f"/api/classrooms/{created['id']}/students", headers=_auth(teacher_token)
    )
    assert len(list_resp.json()) == 0


@pytest.mark.integration
def test_remove_student_not_enrolled(client, db):
    """DELETE /api/classrooms/{id}/students/{student_id} with a non-enrolled student → 404."""
    teacher_token = _signup(
        client, "teacher-notenrolled@t.com", "Teacher NotEnrolled", role="teacher"
    )
    student = _make_user(db, "student-notenrolled@t.com", "Student NotEnrolled")

    created = client.post(
        "/api/classrooms",
        json={"name": "NotEnrolled Class"},
        headers=_auth(teacher_token),
    ).json()

    resp = client.delete(
        f"/api/classrooms/{created['id']}/students/{student.id}",
        headers=_auth(teacher_token),
    )
    assert resp.status_code == 404
    assert "not enrolled" in resp.json()["detail"].lower()

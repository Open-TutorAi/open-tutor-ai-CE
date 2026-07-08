from common.exceptions import AuthorizationError
# tests/test_attendance.py
"""Failing tests for the attendance/session feature.

Document the intended contract before AttendanceRepository / AttendanceService
are implemented (both currently raise NotImplementedError).
"""


import uuid
from datetime import datetime, timedelta

import pytest

from common.exceptions import NotFoundError, ValidationError
from data.models import Classroom, ClassSession, Presence, PresenceStatus, User
from learning.attendance.service import AttendanceService
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


def _make_session(db, classroom_id, scheduled_at, subject="Math", auto_recorded=True):
    session_row = ClassSession(
        id=str(uuid.uuid4()),
        classroom_id=classroom_id,
        scheduled_at=scheduled_at,
        subject=subject,
        auto_recorded=auto_recorded,
    )
    db.add(session_row)
    db.commit()
    return session_row


def _make_presence(db, session_id, student_id, status, recorded_at=None):
    presence = Presence(
        id=str(uuid.uuid4()),
        session_id=session_id,
        student_id=student_id,
        status=status,
        recorded_at=recorded_at or datetime.utcnow(),
    )
    db.add(presence)
    db.commit()
    return presence


# --- Session tests ----------------------------------------------------


@pytest.mark.unit
def test_start_session_creates_session_row(db):
    owner = _make_user(db, "owner1@t.com", "Owner1")
    classroom = _make_classroom(db, owner.id)
    service = AttendanceService(db)

    result = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow(), subject="Algebra"
    )

    session_row = db.query(ClassSession).filter(ClassSession.id == result.id).first()
    assert session_row is not None
    assert session_row.auto_recorded is True


@pytest.mark.unit
def test_start_session_stores_subject_and_objectives(db):
    owner = _make_user(db, "owner1b@t.com", "Owner1b")
    classroom = _make_classroom(db, owner.id)
    service = AttendanceService(db)

    result = service.start_session(
        classroom.id,
        owner.id,
        scheduled_at=datetime.utcnow(),
        subject="Algebra",
        objectives="Solve quadratic equations\nReview homework",
    )

    assert result.subject == "Algebra"
    assert result.objectives == "Solve quadratic equations\nReview homework"
    session_row = db.query(ClassSession).filter(ClassSession.id == result.id).first()
    assert session_row.objectives == "Solve quadratic equations\nReview homework"


@pytest.mark.unit
def test_start_session_generates_presence_rows(db):
    owner = _make_user(db, "owner2@t.com", "Owner2")
    classroom = _make_classroom(db, owner.id)
    students = [_make_user(db, f"s{i}@t.com", f"S{i}") for i in range(3)]
    for s in students:
        _enroll(db, classroom.id, s.id)
    service = AttendanceService(db)

    result = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )

    presences = db.query(Presence).filter(Presence.session_id == result.id).all()
    assert len(presences) == 3
    assert all(p.status == PresenceStatus.ABSENT for p in presences)


@pytest.mark.unit
def test_get_session_presences_returns_all_students(db):
    owner = _make_user(db, "owner3@t.com", "Owner3")
    classroom = _make_classroom(db, owner.id)
    students = [_make_user(db, f"gs{i}@t.com", f"GS{i}") for i in range(3)]
    for s in students:
        _enroll(db, classroom.id, s.id)
    session_row = _make_session(db, classroom.id, datetime.utcnow())
    for s in students:
        _make_presence(db, session_row.id, s.id, PresenceStatus.PRESENT)
    service = AttendanceService(db)

    result = service.get_session_presences(session_row.id, owner.id)

    assert len(result) == 3
    assert {p.student_name for p in result} == {s.name for s in students}
    assert all(p.status == "PRESENT" for p in result)


@pytest.mark.unit
def test_update_presence_status(db):
    owner = _make_user(db, "owner4@t.com", "Owner4")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "ups@t.com", "UPS")
    _enroll(db, classroom.id, student.id)
    session_row = _make_session(db, classroom.id, datetime.utcnow())
    _make_presence(db, session_row.id, student.id, PresenceStatus.PRESENT)
    service = AttendanceService(db)

    result = service.update_presence_status(
        session_row.id, student.id, owner.id, PresenceStatus.LATE
    )

    assert result.status == "LATE"
    refreshed = (
        db.query(Presence)
        .filter(
            Presence.session_id == session_row.id, Presence.student_id == student.id
        )
        .first()
    )
    assert refreshed.status == PresenceStatus.LATE


# --- Attendance stats tests --------------------------------------------


@pytest.mark.unit
def test_avg_attendance_rate_calculation(db):
    owner = _make_user(db, "owner5@t.com", "Owner5")
    classroom = _make_classroom(db, owner.id)
    students = [_make_user(db, f"rate{i}@t.com", f"Rate{i}") for i in range(10)]
    for s in students:
        _enroll(db, classroom.id, s.id)
    sessions = [
        _make_session(db, classroom.id, datetime.utcnow() + timedelta(days=i))
        for i in range(3)
    ]

    # PRESENT and LATE both count as "attended"; only ABSENT lowers the rate.
    # 24 present + 3 late + 3 absent = 30 rows -> 27/30 attended = 90%.
    statuses = (
        [PresenceStatus.PRESENT] * 24
        + [PresenceStatus.LATE] * 3
        + [PresenceStatus.ABSENT] * 3
    )
    idx = 0
    for sess in sessions:
        for s in students:
            _make_presence(db, sess.id, s.id, statuses[idx])
            idx += 1

    service = AttendanceService(db)

    stats = service.get_attendance_stats(classroom.id, owner.id)

    assert stats.sessions_count == 3
    assert stats.total_absences == 3
    assert stats.total_lates == 3
    assert stats.avg_rate == pytest.approx(90.0)


@pytest.mark.unit
def test_student_history_returns_last_10(db):
    owner = _make_user(db, "owner6@t.com", "Owner6")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "hist@t.com", "Hist")
    _enroll(db, classroom.id, student.id)

    base = datetime.utcnow()
    sessions = [
        _make_session(db, classroom.id, base + timedelta(days=i)) for i in range(12)
    ]
    statuses = [
        PresenceStatus.PRESENT if i % 2 == 0 else PresenceStatus.ABSENT
        for i in range(12)
    ]
    for sess, status in zip(sessions, statuses):
        _make_presence(db, sess.id, student.id, status, recorded_at=sess.scheduled_at)

    service = AttendanceService(db)

    history = service.get_student_history(classroom.id, student.id, owner.id)

    assert len(history.last_10) == 10
    assert history.last_10 == [s.value for s in statuses[-10:]]


@pytest.mark.unit
def test_student_history_correct_counts(db):
    owner = _make_user(db, "owner7@t.com", "Owner7")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "counts@t.com", "Counts")
    _enroll(db, classroom.id, student.id)

    base = datetime.utcnow()
    statuses = (
        [PresenceStatus.PRESENT] * 5
        + [PresenceStatus.ABSENT] * 2
        + [PresenceStatus.LATE] * 3
    )
    for i, status in enumerate(statuses):
        sess = _make_session(db, classroom.id, base + timedelta(days=i))
        _make_presence(db, sess.id, student.id, status)

    service = AttendanceService(db)

    history = service.get_student_history(classroom.id, student.id, owner.id)

    raw = db.query(Presence).filter(Presence.student_id == student.id).all()
    assert history.presences + history.absences + history.lates == len(raw)
    assert history.presences == 5
    assert history.absences == 2
    assert history.lates == 3


# --- Access control tests -----------------------------------------------


@pytest.mark.unit
def test_only_classroom_owner_can_start_session(db):
    owner = _make_user(db, "owner8@t.com", "Owner8")
    classroom = _make_classroom(db, owner.id)
    intruder = _make_user(db, "intruder8@t.com", "Intruder8")
    service = AttendanceService(db)

    with pytest.raises(AuthorizationError):
        service.start_session(classroom.id, intruder.id, scheduled_at=datetime.utcnow())


@pytest.mark.unit
def test_session_presences_readable_by_enrolled_student(db):
    owner = _make_user(db, "owner9@t.com", "Owner9")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "enrolled9@t.com", "Enrolled9")
    _enroll(db, classroom.id, student.id)
    session_row = _make_session(db, classroom.id, datetime.utcnow())
    _make_presence(db, session_row.id, student.id, PresenceStatus.PRESENT)
    service = AttendanceService(db)

    result = service.get_session_presences(session_row.id, student.id)

    assert any(p.student_id == student.id for p in result)


@pytest.mark.unit
def test_session_presences_not_readable_by_other_student(db):
    owner = _make_user(db, "owner10@t.com", "Owner10")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "member10@t.com", "Member10")
    outsider = _make_user(db, "outsider10@t.com", "Outsider10")
    _enroll(db, classroom.id, student.id)
    session_row = _make_session(db, classroom.id, datetime.utcnow())
    _make_presence(db, session_row.id, student.id, PresenceStatus.PRESENT)
    service = AttendanceService(db)

    with pytest.raises(AuthorizationError):
        service.get_session_presences(session_row.id, outsider.id)


@pytest.mark.unit
def test_join_session_marks_enrolled_student_present(db):
    owner = _make_user(db, "owner11@t.com", "Owner11")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "joiner11@t.com", "Joiner11")
    _enroll(db, classroom.id, student.id)
    service = AttendanceService(db)
    session_out = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )

    presence = service.join_session(session_out.id, student.id)

    assert presence.status == "PRESENT"
    db_presence = (
        db.query(Presence)
        .filter(
            Presence.session_id == session_out.id, Presence.student_id == student.id
        )
        .first()
    )
    assert db_presence.status == PresenceStatus.PRESENT


@pytest.mark.unit
def test_join_session_is_idempotent_and_does_not_downgrade_late(db):
    owner = _make_user(db, "owner12@t.com", "Owner12")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "joiner12@t.com", "Joiner12")
    _enroll(db, classroom.id, student.id)
    service = AttendanceService(db)
    session_out = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )
    service.update_presence_status(
        session_out.id, student.id, owner.id, PresenceStatus.LATE
    )

    presence = service.join_session(session_out.id, student.id)

    assert presence.status == "LATE"


@pytest.mark.unit
def test_join_session_rejects_non_enrolled_student(db):
    owner = _make_user(db, "owner13@t.com", "Owner13")
    classroom = _make_classroom(db, owner.id)
    outsider = _make_user(db, "outsider13@t.com", "Outsider13")
    service = AttendanceService(db)
    session_out = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )

    with pytest.raises(AuthorizationError):
        service.join_session(session_out.id, outsider.id)


@pytest.mark.unit
def test_join_session_rejects_unknown_session(db):
    student = _make_user(db, "joiner14@t.com", "Joiner14")
    service = AttendanceService(db)

    with pytest.raises(NotFoundError):
        service.join_session("does-not-exist", student.id)


@pytest.mark.unit
def test_join_ended_session_is_rejected(db):
    owner = _make_user(db, "owner15@t.com", "Owner15")
    classroom = _make_classroom(db, owner.id)
    student = _make_user(db, "joiner15@t.com", "Joiner15")
    _enroll(db, classroom.id, student.id)
    service = AttendanceService(db)
    session_out = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )
    service.end_session(session_out.id, owner.id)

    with pytest.raises(ValidationError):
        service.join_session(session_out.id, student.id)


@pytest.mark.unit
def test_end_session_sets_ended_at_and_requires_ownership(db):
    owner = _make_user(db, "owner16@t.com", "Owner16")
    classroom = _make_classroom(db, owner.id)
    intruder = _make_user(db, "intruder16@t.com", "Intruder16")
    service = AttendanceService(db)
    session_out = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )
    assert session_out.ended_at is None

    with pytest.raises(AuthorizationError):
        service.end_session(session_out.id, intruder.id)

    ended = service.end_session(session_out.id, owner.id)
    assert ended.ended_at is not None


@pytest.mark.unit
def test_delete_session_requires_owner_and_ended_session(db):
    owner = _make_user(db, "owner17@t.com", "Owner17")
    intruder = _make_user(db, "intruder17@t.com", "Intruder17")
    classroom = _make_classroom(db, owner.id)
    service = AttendanceService(db)
    session_out = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )

    with pytest.raises(AuthorizationError):
        service.delete_session(session_out.id, intruder.id)

    with pytest.raises(ValidationError):
        service.delete_session(session_out.id, owner.id)

    service.end_session(session_out.id, owner.id)
    service.delete_session(session_out.id, owner.id)

    assert (
        db.query(ClassSession).filter(ClassSession.id == session_out.id).first() is None
    )


@pytest.mark.unit
def test_delete_session_also_deletes_its_presences(db):
    owner = _make_user(db, "owner18@t.com", "Owner18")
    student = _make_user(db, "student18@t.com", "Student18")
    classroom = _make_classroom(db, owner.id)
    _enroll(db, classroom.id, student.id)
    service = AttendanceService(db)
    session_out = service.start_session(
        classroom.id, owner.id, scheduled_at=datetime.utcnow()
    )
    service.end_session(session_out.id, owner.id)

    service.delete_session(session_out.id, owner.id)

    remaining = db.query(Presence).filter(Presence.session_id == session_out.id).all()
    assert remaining == []

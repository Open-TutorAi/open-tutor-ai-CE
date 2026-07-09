# tests/test_classrooms.py
"""Classroom domain tests — Increment 0 (require_teacher) + Increment 1 (class CRUD).

The create payload is the full pedagogical profile captured by the guided wizard
(E1-S1); all fields are required (Pydantic for presence, service for non-empty).
"""

from accounts.users.service import AccountService as IdentityService


def _signup(client, email, name="User", password="pass1234!"):
    r = client.post(
        "/auths/signup", json={"email": email, "name": name, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_teacher(client, db, email="teacher@t.com"):
    data = _signup(client, email, "Teacher")
    IdentityService(db).update_role(data["id"], "teacher")
    return data


def _payload(name="Math · G6"):
    return {
        "name": name,
        "short_description": "A grade-6 maths class.",
        "subject": "Mathematics",
        "course": "National programme",
        "learning_objective": "Master fractions and basic geometry.",
        "competencies": "Reasoning, problem solving",
        "learning_type": "course",
        "level": "Grade 6",
        "content_language": "English",
        "estimated_duration": "30h",
        "keywords": ["fractions", "geometry"],
    }


def _create(client, token, name="Math · G6"):
    return client.post("/api/v1/classrooms", json=_payload(name), headers=_auth(token))


# ── Increment 0: require_teacher guard ──────────────────────────────────────


def test_list_requires_auth(client):
    r = client.get("/api/v1/classrooms")
    assert r.status_code in (401, 403)


def test_list_forbidden_for_non_teacher(client, db):
    _signup(client, "admin@t.com", "Admin")  # first → admin
    student = _signup(client, "student@t.com", "Student")
    r = client.get("/api/v1/classrooms", headers=_auth(student["token"]))
    assert r.status_code == 403


def test_list_ok_for_teacher_empty(client, db):
    _signup(client, "admin@t.com", "Admin")
    teacher = _make_teacher(client, db, "teacher@t.com")
    r = client.get("/api/v1/classrooms", headers=_auth(teacher["token"]))
    assert r.status_code == 200
    assert r.json() == []


# ── Increment 1: classroom management (Epic E1) ─────────────────────────────


def test_create_classroom(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    r = _create(client, teacher["token"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Math · G6"
    assert body["teacher_id"] == teacher["id"]
    assert body["competencies"] == "Reasoning, problem solving"
    assert body["keywords"] == ["fractions", "geometry"]
    assert body["student_count"] == 0
    assert "id" in body
    # New optional teacher settings default to empty when not provided.
    assert body["capacity"] is None
    assert body["meeting_days"] is None


def test_create_classroom_with_schedule_and_capacity(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    payload = {
        **_payload(),
        "capacity": 30,
        "term_start": "2026-09-01",
        "term_end": "2027-06-15",
        "meeting_days": ["Mon", "Wed", "Fri"],
    }
    r = client.post("/api/v1/classrooms", json=payload, headers=_auth(teacher["token"]))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["capacity"] == 30
    assert body["term_start"].startswith("2026-09-01")
    assert body["term_end"].startswith("2027-06-15")
    assert body["meeting_days"] == ["Mon", "Wed", "Fri"]


def test_create_classroom_rejects_bad_capacity_and_dates(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    bad_cap = client.post(
        "/api/v1/classrooms",
        json={**_payload(), "capacity": 0},
        headers=_auth(teacher["token"]),
    )
    assert bad_cap.status_code == 422
    bad_range = client.post(
        "/api/v1/classrooms",
        json={**_payload(), "term_start": "2027-01-01", "term_end": "2026-01-01"},
        headers=_auth(teacher["token"]),
    )
    assert bad_range.status_code == 422


def test_create_missing_field_is_422(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    payload = _payload()
    del payload["learning_objective"]  # drop a required field
    r = client.post("/api/v1/classrooms", json=payload, headers=_auth(teacher["token"]))
    assert r.status_code == 422


def test_create_empty_field_is_422(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    payload = _payload()
    payload["competencies"] = "   "  # present but blank
    r = client.post("/api/v1/classrooms", json=payload, headers=_auth(teacher["token"]))
    assert r.status_code == 422


def test_create_forbidden_for_non_teacher(client, db):
    _signup(client, "admin@t.com", "Admin")
    student = _signup(client, "student@t.com", "Student")
    r = _create(client, student["token"])
    assert r.status_code == 403


def test_list_returns_created_classes(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    _create(client, teacher["token"], name="Math")
    _create(client, teacher["token"], name="Physics")
    r = client.get("/api/v1/classrooms", headers=_auth(teacher["token"]))
    assert r.status_code == 200
    assert {c["name"] for c in r.json()} == {"Math", "Physics"}


def test_get_classroom(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    created = _create(client, teacher["token"]).json()
    r = client.get(
        f"/api/v1/classrooms/{created['id']}", headers=_auth(teacher["token"])
    )
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_classroom_not_found(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    r = client.get("/api/v1/classrooms/nope", headers=_auth(teacher["token"]))
    assert r.status_code == 404


def test_get_classroom_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    created = _create(client, owner["token"]).json()
    r = client.get(f"/api/v1/classrooms/{created['id']}", headers=_auth(other["token"]))
    assert r.status_code == 403


def test_delete_classroom(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    created = _create(client, teacher["token"]).json()
    r = client.delete(
        f"/api/v1/classrooms/{created['id']}", headers=_auth(teacher["token"])
    )
    assert r.status_code == 200
    r2 = client.get(
        f"/api/v1/classrooms/{created['id']}", headers=_auth(teacher["token"])
    )
    assert r2.status_code == 404


def test_delete_classroom_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    created = _create(client, owner["token"]).json()
    r = client.delete(
        f"/api/v1/classrooms/{created['id']}", headers=_auth(other["token"])
    )
    assert r.status_code == 403


def test_delete_classroom_cascades_class_data(client, db):
    """Deleting a class purges its class-scoped data (E1-S4) — no orphan rows."""
    from data.models import (
        Assignment,
        ClassResource,
        Enrollment,
        Invitation,
        MonitorAwayEvent,
        MonitorState,
        Submission,
    )

    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cid = _create(client, teacher["token"]).json()["id"]
    tok = teacher["token"]
    _enrol(client, tok, cid, "student@t.com")
    client.post(
        f"/api/v1/classrooms/{cid}/invitations",
        json={"email": "x@y.com", "invitee_role": "student"},
        headers=_auth(tok),
    )
    aid = client.post(
        f"/api/v1/classrooms/{cid}/assignments",
        json={"title": "A1"},
        headers=_auth(tok),
    ).json()["id"]
    client.post(
        f"/api/v1/assignments/{aid}/submit",
        json={"content": "work"},
        headers=_auth(student["token"]),
    )
    client.post(
        f"/api/v1/classrooms/{cid}/resources",
        files={"file": ("n.txt", b"hi", "text/plain")},
        data={"title": "M1"},
        headers=_auth(tok),
    )
    client.post(
        f"/api/v1/classrooms/{cid}/students/{student['id']}/monitor",
        json={"enabled": False},
        headers=_auth(tok),
    )
    # Generate an away-log row too (student is now locked).
    client.post(
        "/api/v1/me/monitor/presence",
        json={"away": True},
        headers=_auth(student["token"]),
    )

    # Sanity: the child rows exist before deletion.
    assert db.query(Assignment).filter(Assignment.classroom_id == cid).count() == 1
    assert db.query(Submission).filter(Submission.assignment_id == aid).count() == 1
    assert (
        db.query(MonitorAwayEvent).filter(MonitorAwayEvent.classroom_id == cid).count()
        == 1
    )

    r = client.delete(f"/api/v1/classrooms/{cid}", headers=_auth(tok))
    assert r.status_code == 200

    db.expire_all()
    assert db.query(Enrollment).filter(Enrollment.classroom_id == cid).count() == 0
    assert db.query(Invitation).filter(Invitation.classroom_id == cid).count() == 0
    assert db.query(Assignment).filter(Assignment.classroom_id == cid).count() == 0
    assert db.query(Submission).filter(Submission.assignment_id == aid).count() == 0
    assert (
        db.query(ClassResource).filter(ClassResource.classroom_id == cid).count() == 0
    )
    assert db.query(MonitorState).filter(MonitorState.classroom_id == cid).count() == 0
    assert (
        db.query(MonitorAwayEvent).filter(MonitorAwayEvent.classroom_id == cid).count()
        == 0
    )


# ── Increment 2: roster — enrol + invite (Epic E2) ──────────────────────────


def _enrol(client, token, cid, email):
    return client.post(
        f"/api/v1/classrooms/{cid}/students",
        json={"email": email},
        headers=_auth(token),
    )


def _roster(client, token, cid):
    return client.get(f"/api/v1/classrooms/{cid}/students", headers=_auth(token))


def _invite(client, token, cid, email, role="student"):
    return client.post(
        f"/api/v1/classrooms/{cid}/invitations",
        json={"email": email, "invitee_role": role},
        headers=_auth(token),
    )


def test_enrol_existing_student(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    r = _enrol(client, teacher["token"], cls["id"], "student@t.com")
    assert r.status_code == 201, r.text
    assert r.json()["student_id"] == student["id"]
    roster = _roster(client, teacher["token"], cls["id"]).json()
    assert {s["student_id"] for s in roster} == {student["id"]}
    assert roster[0]["email"] == "student@t.com"


def test_enrol_nonexistent_email_is_404(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    cls = _create(client, teacher["token"]).json()
    r = _enrol(client, teacher["token"], cls["id"], "ghost@nowhere.com")
    assert r.status_code == 404


def test_enrol_duplicate_is_409(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    r = _enrol(client, teacher["token"], cls["id"], "student@t.com")
    assert r.status_code == 409


def test_enrol_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    _signup(client, "student@t.com", "Student")
    cls = _create(client, owner["token"]).json()
    r = _enrol(client, other["token"], cls["id"], "student@t.com")
    assert r.status_code == 403


def test_remove_student(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    r = client.delete(
        f"/api/v1/classrooms/{cls['id']}/students/{student['id']}",
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200
    assert _roster(client, teacher["token"], cls["id"]).json() == []


def test_invite_creates_pending_with_join_link(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    cls = _create(client, teacher["token"]).json()
    r = _invite(client, teacher["token"], cls["id"], "newbie@mail.com")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["invitation"]["status"] == "pending"
    assert body["email_sent"] is False
    assert body["join_url"]
    inv = client.get(
        f"/api/v1/classrooms/{cls['id']}/invitations", headers=_auth(teacher["token"])
    ).json()
    assert any(i["email"] == "newbie@mail.com" for i in inv)


def test_invite_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create(client, owner["token"]).json()
    r = _invite(client, other["token"], cls["id"], "newbie@mail.com")
    assert r.status_code == 403


def test_accept_invitation_enrols_invitee(client, db):
    from data.models import Invitation

    teacher = _make_teacher(client, db, "teacher@t.com")
    cls = _create(client, teacher["token"]).json()
    _invite(client, teacher["token"], cls["id"], "invitee@mail.com")
    token = (
        db.query(Invitation)
        .filter(Invitation.email == "invitee@mail.com")
        .first()
        .token
    )
    invitee = _signup(client, "invitee@mail.com", "Invitee")
    r = client.post(
        "/api/v1/invitations/accept",
        json={"token": token},
        headers=_auth(invitee["token"]),
    )
    assert r.status_code == 200, r.text
    roster = _roster(client, teacher["token"], cls["id"]).json()
    assert invitee["id"] in {s["student_id"] for s in roster}


def test_accept_invalid_token_is_404(client, db):
    user = _signup(client, "u@mail.com", "U")
    r = client.post(
        "/api/v1/invitations/accept",
        json={"token": "nope"},
        headers=_auth(user["token"]),
    )
    assert r.status_code == 404


def test_accept_expired_token_is_410(client, db):
    from datetime import datetime, timedelta

    from data.models import Invitation

    teacher = _make_teacher(client, db, "teacher@t.com")
    cls = _create(client, teacher["token"]).json()
    _invite(client, teacher["token"], cls["id"], "late@mail.com")
    inv = db.query(Invitation).filter(Invitation.email == "late@mail.com").first()
    inv.expires_at = datetime.utcnow() - timedelta(days=1)
    db.commit()
    invitee = _signup(client, "late@mail.com", "Late")
    r = client.post(
        "/api/v1/invitations/accept",
        json={"token": inv.token},
        headers=_auth(invitee["token"]),
    )
    assert r.status_code == 410


def test_accept_used_token_is_410(client, db):
    from data.models import Invitation

    teacher = _make_teacher(client, db, "teacher@t.com")
    cls = _create(client, teacher["token"]).json()
    _invite(client, teacher["token"], cls["id"], "once@mail.com")
    token = (
        db.query(Invitation).filter(Invitation.email == "once@mail.com").first().token
    )
    invitee = _signup(client, "once@mail.com", "Once")
    client.post(
        "/api/v1/invitations/accept",
        json={"token": token},
        headers=_auth(invitee["token"]),
    )
    r = client.post(
        "/api/v1/invitations/accept",
        json={"token": token},
        headers=_auth(invitee["token"]),
    )
    assert r.status_code == 410


# ── Increment 3: progress monitoring (Epic E3, read-only) ───────────────────


def _create_support(client, token, title="Fractions", subject="Math"):
    return client.post(
        "/api/v1/supports/create",
        json={"title": title, "subject": subject},
        headers=_auth(token),
    )


def _class_progress(client, token, cid):
    return client.get(f"/api/v1/classrooms/{cid}/progress", headers=_auth(token))


def _student_progress(client, token, cid, sid):
    return client.get(
        f"/api/v1/classrooms/{cid}/students/{sid}/progress", headers=_auth(token)
    )


def test_class_progress_overview(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    active = _signup(client, "active@t.com", "Active")
    idle = _signup(client, "idle@t.com", "Idle")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "active@t.com")
    _enrol(client, teacher["token"], cls["id"], "idle@t.com")
    _create_support(client, active["token"])  # active student has activity

    r = _class_progress(client, teacher["token"], cls["id"])
    assert r.status_code == 200, r.text
    rows = {row["student_id"]: row for row in r.json()}
    assert rows[active["id"]]["supports_total"] == 1
    assert rows[active["id"]]["status"] == "active"
    assert rows[idle["id"]]["supports_total"] == 0
    assert rows[idle["id"]]["status"] == "not_started"


def test_class_progress_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create(client, owner["token"]).json()
    r = _class_progress(client, other["token"], cls["id"])
    assert r.status_code == 403


def test_student_progress_detail(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    _create_support(client, student["token"], title="Fractions", subject="Math")

    r = _student_progress(client, teacher["token"], cls["id"], student["id"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["student_id"] == student["id"]
    assert body["supports"]["total"] == 1
    assert body["supports"]["items"][0]["title"] == "Fractions"
    assert body["activity"]["status"] == "active"
    assert "engagement" in body


def test_student_progress_no_data_renders(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    r = _student_progress(client, teacher["token"], cls["id"], student["id"])
    assert r.status_code == 200
    body = r.json()
    assert body["supports"]["total"] == 0
    assert body["activity"]["status"] == "not_started"
    assert body["activity"]["last_active"] is None


def test_student_progress_non_enrolled_is_404(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    outsider = _signup(client, "outsider@t.com", "Out")
    cls = _create(client, teacher["token"]).json()
    r = _student_progress(client, teacher["token"], cls["id"], outsider["id"])
    assert r.status_code == 404


def test_student_progress_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, owner["token"]).json()
    _enrol(client, owner["token"], cls["id"], "student@t.com")
    r = _student_progress(client, other["token"], cls["id"], student["id"])
    assert r.status_code == 403


def test_progress_is_read_only(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    _create_support(client, student["token"])
    before = client.get("/api/v1/supports/list", headers=_auth(student["token"])).json()
    _student_progress(client, teacher["token"], cls["id"], student["id"])
    _class_progress(client, teacher["token"], cls["id"])
    after = client.get("/api/v1/supports/list", headers=_auth(student["token"])).json()
    assert len(before) == len(after)


# ── Increment 4: guardians — parent link & contact (Epic E4) ────────────────


def _make_parent(client, db, email="parent@t.com"):
    data = _signup(client, email, "Parent")
    IdentityService(db).update_role(data["id"], "parent")
    return data


def _guardians(client, token, cid, sid):
    return client.get(
        f"/api/v1/classrooms/{cid}/students/{sid}/guardians", headers=_auth(token)
    )


def _add_guardian(client, token, cid, sid, email):
    return client.post(
        f"/api/v1/classrooms/{cid}/students/{sid}/guardians",
        json={"email": email},
        headers=_auth(token),
    )


def _enrolled(client, db, teacher_email="teacher@t.com"):
    teacher = _make_teacher(client, db, teacher_email)
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    return teacher, student, cls


def test_link_existing_parent_is_active(client, db):
    teacher, student, cls = _enrolled(client, db)
    parent = _make_parent(client, db, "parent@t.com")
    r = _add_guardian(
        client, teacher["token"], cls["id"], student["id"], "parent@t.com"
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "active"
    links = _guardians(client, teacher["token"], cls["id"], student["id"]).json()
    assert links[0]["status"] == "active"
    assert links[0]["parent_user_id"] == parent["id"]


def test_invite_new_parent_is_pending_with_link(client, db):
    teacher, student, cls = _enrolled(client, db)
    r = _add_guardian(
        client, teacher["token"], cls["id"], student["id"], "newdad@mail.com"
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["join_url"]
    links = _guardians(client, teacher["token"], cls["id"], student["id"]).json()
    assert links[0]["status"] == "pending"
    assert links[0]["parent_user_id"] is None


def test_link_duplicate_parent_is_409(client, db):
    teacher, student, cls = _enrolled(client, db)
    _make_parent(client, db, "parent@t.com")
    _add_guardian(client, teacher["token"], cls["id"], student["id"], "parent@t.com")
    r = _add_guardian(
        client, teacher["token"], cls["id"], student["id"], "parent@t.com"
    )
    assert r.status_code == 409


def test_duplicate_pending_invite_is_409(client, db):
    teacher, student, cls = _enrolled(client, db)
    _add_guardian(client, teacher["token"], cls["id"], student["id"], "newdad@mail.com")
    r = _add_guardian(
        client, teacher["token"], cls["id"], student["id"], "newdad@mail.com"
    )
    assert r.status_code == 409


def test_guardians_forbidden_for_other_teacher(client, db):
    teacher, student, cls = _enrolled(client, db)
    other = _make_teacher(client, db, "other@t.com")
    r = _add_guardian(client, other["token"], cls["id"], student["id"], "p@mail.com")
    assert r.status_code == 403


def test_guardians_non_enrolled_student_is_404(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    outsider = _signup(client, "out@t.com", "Out")
    cls = _create(client, teacher["token"]).json()
    r = _add_guardian(client, teacher["token"], cls["id"], outsider["id"], "p@mail.com")
    assert r.status_code == 404


def test_parent_accept_activates_guardian_link(client, db):
    from data.models import Invitation

    teacher, student, cls = _enrolled(client, db)
    _add_guardian(
        client, teacher["token"], cls["id"], student["id"], "futuredad@mail.com"
    )
    token = (
        db.query(Invitation)
        .filter(Invitation.email == "futuredad@mail.com")
        .first()
        .token
    )
    parent = _signup(client, "futuredad@mail.com", "Dad")
    r = client.post(
        "/api/v1/invitations/accept",
        json={"token": token},
        headers=_auth(parent["token"]),
    )
    assert r.status_code == 200, r.text
    links = _guardians(client, teacher["token"], cls["id"], student["id"]).json()
    assert links[0]["status"] == "active"
    assert links[0]["parent_user_id"] == parent["id"]


# ── Students directory (cross-class roster) ─────────────────────────────────


def _directory(client, token):
    return client.get("/api/v1/students", headers=_auth(token))


def test_students_directory_requires_teacher(client, db):
    _signup(client, "admin@t.com", "Admin")  # first → admin
    student = _signup(client, "student@t.com", "Student")
    r = _directory(client, student["token"])
    assert r.status_code == 403


def test_students_directory_empty(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    r = _directory(client, teacher["token"])
    assert r.status_code == 200
    assert r.json() == []


def test_students_directory_dedups_across_classes(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    math = _create(client, teacher["token"], name="Math").json()
    physics = _create(client, teacher["token"], name="Physics").json()
    _enrol(client, teacher["token"], math["id"], "student@t.com")
    _enrol(client, teacher["token"], physics["id"], "student@t.com")

    rows = _directory(client, teacher["token"]).json()
    assert len(rows) == 1  # one student, two classes
    entry = rows[0]
    assert entry["student_id"] == student["id"]
    assert entry["email"] == "student@t.com"
    assert {c["name"] for c in entry["classes"]} == {"Math", "Physics"}


def test_students_directory_excludes_other_teachers(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    _signup(client, "mine@t.com", "Mine")
    _signup(client, "theirs@t.com", "Theirs")
    my_cls = _create(client, teacher["token"], name="Mine").json()
    their_cls = _create(client, other["token"], name="Theirs").json()
    _enrol(client, teacher["token"], my_cls["id"], "mine@t.com")
    _enrol(client, other["token"], their_cls["id"], "theirs@t.com")

    emails = {e["email"] for e in _directory(client, teacher["token"]).json()}
    assert emails == {"mine@t.com"}


def test_students_directory_includes_signals(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    _create_support(client, student["token"])
    _add_guardian(client, teacher["token"], cls["id"], student["id"], "mum@mail.com")

    entry = _directory(client, teacher["token"]).json()[0]
    assert entry["supports_total"] == 1
    assert entry["status"] == "active"
    assert entry["guardians"] == 1


# ── Increment 7: classroom control — student monitors (Epic E6) ─────────────


def _set_monitor(client, token, cid, sid, enabled):
    return client.post(
        f"/api/v1/classrooms/{cid}/students/{sid}/monitor",
        json={"enabled": enabled},
        headers=_auth(token),
    )


def _get_monitor(client, token, cid, sid):
    return client.get(
        f"/api/v1/classrooms/{cid}/students/{sid}/monitor", headers=_auth(token)
    )


def test_monitor_defaults_to_on(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    r = _get_monitor(client, teacher["token"], cls["id"], student["id"])
    assert r.status_code == 200
    assert r.json()["enabled"] is True


def test_set_monitor_off_persists(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")

    r = _set_monitor(client, teacher["token"], cls["id"], student["id"], False)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["enabled"] is False
    assert body["state"] == "off"
    assert body["delivered"] is False

    got = _get_monitor(client, teacher["token"], cls["id"], student["id"]).json()
    assert got["enabled"] is False

    _set_monitor(client, teacher["token"], cls["id"], student["id"], True)
    assert (
        _get_monitor(client, teacher["token"], cls["id"], student["id"]).json()[
            "enabled"
        ]
        is True
    )


def test_set_monitor_forbidden_for_non_teacher(client, db):
    _signup(client, "admin@t.com", "Admin")
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    r = _set_monitor(client, student["token"], cls["id"], student["id"], False)
    assert r.status_code == 403


def test_set_monitor_other_teacher_is_403(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    r = _set_monitor(client, other["token"], cls["id"], student["id"], False)
    assert r.status_code == 403


def test_set_monitor_non_enrolled_is_404(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    outsider = _signup(client, "outsider@t.com", "Out")
    cls = _create(client, teacher["token"]).json()
    r = _set_monitor(client, teacher["token"], cls["id"], outsider["id"], False)
    assert r.status_code == 404


def test_class_monitor_toggles_all(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    a = _signup(client, "a@t.com", "A")
    b = _signup(client, "b@t.com", "B")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "a@t.com")
    _enrol(client, teacher["token"], cls["id"], "b@t.com")

    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/monitor",
        json={"enabled": False},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 2
    assert body["reached"] == 0
    assert body["state"] == "off"
    assert (
        _get_monitor(client, teacher["token"], cls["id"], a["id"]).json()["enabled"]
        is False
    )
    assert (
        _get_monitor(client, teacher["token"], cls["id"], b["id"]).json()["enabled"]
        is False
    )


def test_class_monitor_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create(client, owner["token"]).json()
    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/monitor",
        json={"enabled": False},
        headers=_auth(other["token"]),
    )
    assert r.status_code == 403


def test_class_presence_lists_roster_with_offline_default(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    a = _signup(client, "a@t.com", "Anna")
    b = _signup(client, "b@t.com", "Ben")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "a@t.com")
    _enrol(client, teacher["token"], cls["id"], "b@t.com")

    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/presence", headers=_auth(teacher["token"])
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 2
    # No live sockets in tests → everyone is offline.
    assert body["online"] == 0
    # Ids only (names are resolved client-side from the loaded roster).
    assert {s["student_id"] for s in body["students"]} == {a["id"], b["id"]}
    assert all(s["online"] is False for s in body["students"])


def test_class_presence_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create(client, owner["token"]).json()
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/presence", headers=_auth(other["token"])
    )
    assert r.status_code == 403


# ── Student-facing: my own monitor state (re-applied on reconnect) ──────────


def _my_monitor(client, token):
    return client.get("/api/v1/me/monitor", headers=_auth(token))


def test_my_monitor_defaults_to_on(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    r = _my_monitor(client, student["token"])
    assert r.status_code == 200
    assert r.json()["enabled"] is True


def test_my_monitor_reflects_lock(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")

    _set_monitor(client, teacher["token"], cls["id"], student["id"], False)
    assert _my_monitor(client, student["token"]).json()["enabled"] is False

    # Unlocking restores the student's own view.
    _set_monitor(client, teacher["token"], cls["id"], student["id"], True)
    assert _my_monitor(client, student["token"]).json()["enabled"] is True


def test_my_monitor_locked_if_any_class_locks(client, db):
    # One student in two classes: a lock in either one locks the single screen.
    student = _signup(client, "student@t.com", "Student")
    t1 = _make_teacher(client, db, "t1@t.com")
    t2 = _make_teacher(client, db, "t2@t.com")
    c1 = _create(client, t1["token"]).json()
    c2 = _create(client, t2["token"]).json()
    _enrol(client, t1["token"], c1["id"], "student@t.com")
    _enrol(client, t2["token"], c2["id"], "student@t.com")

    _set_monitor(client, t2["token"], c2["id"], student["id"], False)
    assert _my_monitor(client, student["token"]).json()["enabled"] is False

    # Clearing only that class unlocks again (no other class holds a lock).
    _set_monitor(client, t2["token"], c2["id"], student["id"], True)
    assert _my_monitor(client, student["token"]).json()["enabled"] is True


def test_my_monitor_requires_auth(client, db):
    assert client.get("/api/v1/me/monitor").status_code in (401, 403)


# ── Tab-away telemetry: locked student leaving/returning to the screen ──────


def _presence(client, token, away):
    return client.post(
        "/api/v1/me/monitor/presence", json={"away": away}, headers=_auth(token)
    )


def test_presence_notifies_locking_teacher(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    _set_monitor(client, teacher["token"], cls["id"], student["id"], False)

    r = _presence(client, student["token"], True)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["away"] is True
    assert body["notified"] == 1


def test_presence_silent_when_not_locked(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    # No lock in place → nobody to notify.
    r = _presence(client, student["token"], True)
    assert r.status_code == 200
    assert r.json()["notified"] == 0


def test_presence_notifies_each_locking_class(client, db):
    student = _signup(client, "student@t.com", "Student")
    t1 = _make_teacher(client, db, "t1@t.com")
    t2 = _make_teacher(client, db, "t2@t.com")
    c1 = _create(client, t1["token"]).json()
    c2 = _create(client, t2["token"]).json()
    _enrol(client, t1["token"], c1["id"], "student@t.com")
    _enrol(client, t2["token"], c2["id"], "student@t.com")
    _set_monitor(client, t1["token"], c1["id"], student["id"], False)
    _set_monitor(client, t2["token"], c2["id"], student["id"], False)

    assert _presence(client, student["token"], True).json()["notified"] == 2

    # Returning to the screen reports to the same teachers.
    assert _presence(client, student["token"], False).json()["notified"] == 2


def test_presence_requires_auth(client, db):
    assert client.post(
        "/api/v1/me/monitor/presence", json={"away": True}
    ).status_code in (401, 403)


# ── Away-log persistence (durable tab-away history) ─────────────────────────


def _away_log(client, token, cid):
    return client.get(
        f"/api/v1/classrooms/{cid}/monitor/away-log", headers=_auth(token)
    )


def test_clear_away_log(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    _set_monitor(client, teacher["token"], cls["id"], student["id"], False)
    _presence(client, student["token"], True)
    assert len(_away_log(client, teacher["token"], cls["id"]).json()) == 1

    r = client.delete(
        f"/api/v1/classrooms/{cls['id']}/monitor/away-log",
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["removed"] == 1
    assert _away_log(client, teacher["token"], cls["id"]).json() == []


def test_clear_away_log_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create(client, owner["token"]).json()
    r = client.delete(
        f"/api/v1/classrooms/{cls['id']}/monitor/away-log",
        headers=_auth(other["token"]),
    )
    assert r.status_code == 403


def test_away_log_records_transitions_newest_first(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    _set_monitor(client, teacher["token"], cls["id"], student["id"], False)

    _presence(client, student["token"], True)  # left
    _presence(client, student["token"], False)  # returned

    r = _away_log(client, teacher["token"], cls["id"])
    assert r.status_code == 200, r.text
    log = r.json()
    assert len(log) == 2
    # Newest first: the return (away=False) was logged last.
    assert log[0]["away"] is False
    assert log[1]["away"] is True
    assert log[0]["student_name"] == "Student"
    assert log[0]["student_id"] == student["id"]


def test_away_log_empty_when_no_events(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    cls = _create(client, teacher["token"]).json()
    assert _away_log(client, teacher["token"], cls["id"]).json() == []


def test_presence_while_unlocked_writes_no_log(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    # Not locked → presence reports are silent and unrecorded.
    _presence(client, student["token"], True)
    assert _away_log(client, teacher["token"], cls["id"]).json() == []


def test_away_log_forbidden_for_other_teacher(client, db):
    owner = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create(client, owner["token"]).json()
    assert _away_log(client, other["token"], cls["id"]).status_code == 403


def test_away_log_requires_teacher(client, db):
    _signup(client, "admin@t.com", "Admin")
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"]).json()
    assert _away_log(client, student["token"], cls["id"]).status_code == 403


# ── Student-facing: my teachers (messaging contacts) ────────────────────────


def _my_teachers(client, token):
    return client.get("/api/v1/my-teachers", headers=_auth(token))


def test_my_teachers_lists_class_teachers(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create(client, teacher["token"], name="Math").json()
    _enrol(client, teacher["token"], cls["id"], "student@t.com")

    r = _my_teachers(client, student["token"])
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["teacher_id"] == teacher["id"]
    assert {c["name"] for c in rows[0]["classes"]} == {"Math"}


def test_my_teachers_dedups_same_teacher(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    math = _create(client, teacher["token"], name="Math").json()
    physics = _create(client, teacher["token"], name="Physics").json()
    _enrol(client, teacher["token"], math["id"], "student@t.com")
    _enrol(client, teacher["token"], physics["id"], "student@t.com")

    rows = _my_teachers(client, student["token"]).json()
    assert len(rows) == 1  # same teacher, two classes
    assert {c["name"] for c in rows[0]["classes"]} == {"Math", "Physics"}


def test_my_teachers_empty_when_not_enrolled(client, db):
    _make_teacher(client, db, "teacher@t.com")
    loner = _signup(client, "loner@t.com", "Loner")
    r = _my_teachers(client, loner["token"])
    assert r.status_code == 200
    assert r.json() == []


# ── Dashboard stats aggregation ─────────────────────────────────────────────


def test_dashboard_requires_teacher(client, db):
    student = _signup(client, "s@t.com", "Student")
    # Missing bearer → 403 (HTTPBearer auto_error); a non-teacher → 403 (role guard).
    assert client.get("/api/v1/classrooms/dashboard").status_code == 403
    r = client.get("/api/v1/classrooms/dashboard", headers=_auth(student["token"]))
    assert r.status_code == 403


def test_dashboard_stats_aggregates(client, db):
    teacher = _make_teacher(client, db, "teach@t.com")
    student = _signup(client, "stud@t.com", "Stud")
    tok = teacher["token"]
    cid = _create(client, tok).json()["id"]

    # 1 enrolled student, 1 pending invitation.
    client.post(
        f"/api/v1/classrooms/{cid}/students",
        json={"email": "stud@t.com"},
        headers=_auth(tok),
    )
    client.post(
        f"/api/v1/classrooms/{cid}/invitations",
        json={"email": "invitee@t.com"},
        headers=_auth(tok),
    )

    # An assignment with one ungraded submission → to_grade = 1.
    aid = client.post(
        f"/api/v1/classrooms/{cid}/assignments",
        json={"title": "HW1"},
        headers=_auth(tok),
    ).json()["id"]
    client.post(
        f"/api/v1/assignments/{aid}/submit",
        json={"content": "my answer"},
        headers=_auth(student["token"]),
    )

    r = client.get("/api/v1/classrooms/dashboard", headers=_auth(tok))
    assert r.status_code == 200, r.text
    stats = r.json()
    assert stats == {
        "classes": 1,
        "students": 1,
        "pending_invites": 1,
        "to_grade": 1,
    }

    # Grading the submission clears the to-grade count.
    client.post(
        f"/api/v1/classrooms/{cid}/assignments/{aid}/grade",
        json={"student_id": student["id"], "grade": 8},
        headers=_auth(tok),
    )
    assert (
        client.get("/api/v1/classrooms/dashboard", headers=_auth(tok)).json()[
            "to_grade"
        ]
        == 0
    )


def test_dashboard_only_counts_own_classes(client, db):
    teacher = _make_teacher(client, db, "owner@t.com")
    other = _make_teacher(client, db, "other@t.com")
    _create(client, teacher["token"])
    _create(client, other["token"])
    # Each teacher sees only their own single class.
    assert (
        client.get(
            "/api/v1/classrooms/dashboard", headers=_auth(teacher["token"])
        ).json()["classes"]
        == 1
    )

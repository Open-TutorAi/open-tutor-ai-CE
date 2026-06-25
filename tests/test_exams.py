# tests/test_exams.py
"""Exam (proctoring) domain tests — Epic E10.

An exam is an assignment with an ExamConfig. Students run one ExamSession; leaving the
page records an ExamViolation. Policy `on_violation` = warn | flag | auto_submit.
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


def _class_payload(name="Math · G6"):
    return {
        "name": name,
        "short_description": "desc",
        "subject": "Mathematics",
        "course": "National programme",
        "learning_objective": "Objectives.",
        "competencies": "Reasoning",
        "learning_type": "course",
        "level": "Grade 6",
        "content_language": "English",
        "estimated_duration": "30h",
        "keywords": ["x"],
    }


def _create_class(client, token):
    r = client.post("/api/v1/classrooms", json=_class_payload(), headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def _enrol(client, token, cid, email):
    return client.post(
        f"/api/v1/classrooms/{cid}/students",
        json={"email": email},
        headers=_auth(token),
    )


def _assignment(client, token, cid, title="Exam 1"):
    r = client.post(
        f"/api/v1/classrooms/{cid}/assignments",
        json={"title": title},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _configure(client, token, cid, aid, **over):
    body = {"require_fullscreen": True}  # policy is fixed to auto_submit server-side
    body.update(over)
    return client.post(
        f"/api/v1/classrooms/{cid}/assignments/{aid}/exam",
        json=body,
        headers=_auth(token),
    )


def _get_exam(client, token, aid):
    return client.get(f"/api/v1/assignments/{aid}/exam", headers=_auth(token))


def _start(client, token, aid):
    return client.post(f"/api/v1/assignments/{aid}/exam/start", headers=_auth(token))


def _violation(client, token, aid, vtype="left_page"):
    return client.post(
        f"/api/v1/assignments/{aid}/exam/violation",
        json={"type": vtype},
        headers=_auth(token),
    )


def _proctoring(client, token, cid, aid):
    return client.get(
        f"/api/v1/classrooms/{cid}/assignments/{aid}/proctoring", headers=_auth(token)
    )


# A teacher + class + one enrolled student + one assignment.
def _setup(client, db, student_email="student@t.com"):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, student_email, "Student")
    cls = _create_class(client, teacher["token"])
    _enrol(client, teacher["token"], cls["id"], student_email)
    a = _assignment(client, teacher["token"], cls["id"])
    return teacher, student, cls, a


# ── configuration ───────────────────────────────────────────────────────────


def test_configure_marks_assignment_as_exam(client, db):
    teacher, student, cls, a = _setup(client, db)
    r = _configure(client, teacher["token"], cls["id"], a["id"], time_limit_minutes=45)
    assert r.status_code == 200, r.text
    # Policy is fixed to auto-submit; warnings default to the cap (3).
    assert r.json()["on_violation"] == "auto_submit"
    assert r.json()["max_violations"] == 3
    assert r.json()["time_limit_minutes"] == 45

    # Student sees it's an exam.
    g = _get_exam(client, student["token"], a["id"]).json()
    assert g["is_exam"] is True
    assert g["config"]["require_fullscreen"] is True
    assert g["session"] is None


def test_plain_assignment_is_not_an_exam(client, db):
    teacher, student, cls, a = _setup(client, db)
    g = _get_exam(client, student["token"], a["id"]).json()
    assert g["is_exam"] is False
    assert g["config"] is None


def test_configure_forbidden_for_non_owner(client, db):
    teacher, student, cls, a = _setup(client, db)
    other = _make_teacher(client, db, "other@t.com")
    assert _configure(client, other["token"], cls["id"], a["id"]).status_code == 403


def test_configure_caps_max_warnings_at_3(client, db):
    teacher, student, cls, a = _setup(client, db)
    assert (
        _configure(
            client, teacher["token"], cls["id"], a["id"], max_violations=5
        ).status_code
        == 422
    )


def test_configure_defaults_max_warnings_to_3(client, db):
    teacher, student, cls, a = _setup(client, db)
    r = _configure(client, teacher["token"], cls["id"], a["id"])
    assert r.status_code == 200
    assert r.json()["max_violations"] == 3


# ── student sessions + violations ───────────────────────────────────────────


def test_start_session_and_resume(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"])
    r = _start(client, student["token"], a["id"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["session"]["status"] == "in_progress"
    sid = body["session"]["id"]
    # Re-start resumes the same session.
    assert _start(client, student["token"], a["id"]).json()["session"]["id"] == sid


def test_start_non_exam_is_422(client, db):
    teacher, student, cls, a = _setup(client, db)  # not configured
    assert _start(client, student["token"], a["id"]).status_code == 422


def test_violation_grace_schedule(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=3)
    _start(client, student["token"], a["id"])
    # Each graced warning shrinks the time-to-return: 60 → 30 → 10.
    r1 = _violation(client, student["token"], a["id"], "left_page")
    assert r1.status_code == 200, r1.text
    assert r1.json()["action"] == "warn"
    assert r1.json()["grace_seconds"] == 60
    assert r1.json()["session"]["violation_count"] == 1
    r2 = _violation(client, student["token"], a["id"], "left_page")
    assert r2.json()["grace_seconds"] == 30
    r3 = _violation(client, student["token"], a["id"], "left_page")
    assert r3.json()["grace_seconds"] == 10
    assert r3.json()["session"]["status"] == "in_progress"


def test_terminates_after_warnings_exhausted(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=2)
    _start(client, student["token"], a["id"])
    assert _violation(client, student["token"], a["id"]).json()["action"] == "warn"
    assert _violation(client, student["token"], a["id"]).json()["action"] == "warn"
    # The warning after the allowance ends the exam.
    third = _violation(client, student["token"], a["id"])
    assert third.json()["action"] == "terminated"
    assert third.json()["session"]["status"] == "terminated"


def test_terminate_session_endpoint(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"])
    _start(client, student["token"], a["id"])
    r = client.post(
        f"/api/v1/assignments/{a['id']}/exam/terminate",
        json={"reason": "away_timeout"},
        headers=_auth(student["token"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["session"]["status"] == "terminated"
    # Teacher sees the terminal reason in the proctoring log.
    rows = _proctoring(client, teacher["token"], cls["id"], a["id"]).json()
    assert rows[0]["status"] == "terminated"
    assert any(v["type"] == "away_timeout" for v in rows[0]["violations"])


# ── proctoring (teacher) ────────────────────────────────────────────────────


def test_proctoring_lists_sessions_and_violations(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"])
    _start(client, student["token"], a["id"])
    _violation(client, student["token"], a["id"], "left_page")

    r = _proctoring(client, teacher["token"], cls["id"], a["id"])
    assert r.status_code == 200, r.text
    rows = r.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["student_id"] == student["id"]
    assert row["status"] == "in_progress"
    assert row["violation_count"] == 1
    assert row["violations"][0]["type"] == "left_page"


def test_proctoring_shows_not_started(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"])
    rows = _proctoring(client, teacher["token"], cls["id"], a["id"]).json()
    assert rows[0]["status"] == "not_started"
    assert rows[0]["violation_count"] == 0


def test_proctoring_forbidden_for_non_owner(client, db):
    teacher, student, cls, a = _setup(client, db)
    other = _make_teacher(client, db, "other@t.com")
    assert _proctoring(client, other["token"], cls["id"], a["id"]).status_code == 403


def test_get_exam_denied_to_outsider(client, db):
    teacher, student, cls, a = _setup(client, db)
    outsider = _signup(client, "out@t.com", "Out")
    assert _get_exam(client, outsider["token"], a["id"]).status_code == 403

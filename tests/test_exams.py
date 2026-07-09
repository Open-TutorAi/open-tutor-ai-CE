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
    # Graced warnings shrink the time-to-return (60 → 30); the N-th ends the exam.
    r1 = _violation(client, student["token"], a["id"], "left_page")
    assert r1.status_code == 200, r1.text
    assert r1.json()["action"] == "warn"
    assert r1.json()["grace_seconds"] == 60
    assert r1.json()["session"]["violation_count"] == 1
    r2 = _violation(client, student["token"], a["id"], "left_page")
    assert r2.json()["action"] == "warn"
    assert r2.json()["grace_seconds"] == 30
    r3 = _violation(client, student["token"], a["id"], "left_page")
    assert r3.json()["action"] == "terminated"
    assert r3.json()["session"]["status"] == "terminated"


def test_terminates_after_warnings_exhausted(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=2)
    _start(client, student["token"], a["id"])
    assert _violation(client, student["token"], a["id"]).json()["action"] == "warn"
    # max_violations = N means the N-th warning ends the exam (2 of 2 here).
    second = _violation(client, student["token"], a["id"])
    assert second.json()["action"] == "terminated"
    assert second.json()["session"]["status"] == "terminated"
    assert second.json()["session"]["violation_count"] == 2


def test_terminated_exam_shows_auto_submitted_in_student_feed(client, db):
    """After a proctoring termination the client submits the work; the student's
    assignments feed must surface it as `auto_submitted`, not a normal hand-in.
    A teacher grade still wins afterwards."""
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=1)
    _start(client, student["token"], a["id"])
    assert (
        _violation(client, student["token"], a["id"]).json()["action"] == "terminated"
    )
    # The exam shell submits whatever the student had written.
    r = client.post(
        f"/api/v1/assignments/{a['id']}/submit",
        json={"content": "partial work"},
        headers=_auth(student["token"]),
    )
    assert r.status_code == 201, r.text

    r = client.get("/api/v1/assignments", headers=_auth(student["token"]))
    row = next(x for x in r.json() if x["id"] == a["id"])
    assert row["status"] == "auto_submitted"

    # Grading the auto-submitted work flips the status to graded as usual.
    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/assignments/{a['id']}/grade",
        json={"student_id": student["id"], "grade": 5},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200, r.text
    r = client.get("/api/v1/assignments", headers=_auth(student["token"]))
    row = next(x for x in r.json() if x["id"] == a["id"])
    assert row["status"] == "graded"


def test_terminated_exam_with_empty_answer_still_auto_submitted(client, db):
    """Termination with nothing written: the shell's auto-submit fails validation
    (no content), so no submission row exists — the feed must still show
    auto_submitted, never falling back to 'pending' (which would re-offer the exam)."""
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=1)
    _start(client, student["token"], a["id"])
    assert (
        _violation(client, student["token"], a["id"]).json()["action"] == "terminated"
    )

    r = client.get("/api/v1/assignments", headers=_auth(student["token"]))
    row = next(x for x in r.json() if x["id"] == a["id"])
    assert row["status"] == "auto_submitted"
    assert row["submission"] is None


def test_finished_exam_cannot_be_restarted(client, db):
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=1)
    _start(client, student["token"], a["id"])
    assert (
        _violation(client, student["token"], a["id"]).json()["action"] == "terminated"
    )
    r = _start(client, student["token"], a["id"])
    assert r.status_code == 422
    assert "retaken" in r.json()["detail"]


def test_ended_exam_submission_cannot_be_replaced(client, db):
    """The one auto-submit from the shell lands; any further submit is rejected."""
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=1)
    _start(client, student["token"], a["id"])
    assert (
        _violation(client, student["token"], a["id"]).json()["action"] == "terminated"
    )
    # The shell's single post-termination submit is accepted…
    r = client.post(
        f"/api/v1/assignments/{a['id']}/submit",
        json={"content": "what I had written"},
        headers=_auth(student["token"]),
    )
    assert r.status_code == 201, r.text
    # …but replacing it afterwards is not.
    r = client.post(
        f"/api/v1/assignments/{a['id']}/submit",
        json={"content": "polished at home"},
        headers=_auth(student["token"]),
    )
    assert r.status_code == 422


def test_teacher_detail_shows_auto_submitted_and_grades_empty_termination(client, db):
    """Teacher's per-student breakdown must mirror the student view: a terminated
    exam shows auto_submitted (not pending), and is gradable even when no answer
    was recovered (the grade lands on an empty submission)."""
    teacher, student, cls, a = _setup(client, db)
    _configure(client, teacher["token"], cls["id"], a["id"], max_violations=1)
    _start(client, student["token"], a["id"])
    assert (
        _violation(client, student["token"], a["id"]).json()["action"] == "terminated"
    )

    # Teacher sees auto_submitted, not pending — consistent with proctoring.
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{a['id']}",
        headers=_auth(teacher["token"]),
    )
    row = next(x for x in r.json()["submissions"] if x["student_id"] == student["id"])
    assert row["status"] == "auto_submitted"
    assert row["submission"] is None  # nothing was recovered

    # Grading the attempt works despite the missing copy.
    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/assignments/{a['id']}/grade",
        json={"student_id": student["id"], "grade": 0},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["grade"] == 0

    # Both views now show graded.
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{a['id']}",
        headers=_auth(teacher["token"]),
    )
    row = next(x for x in r.json()["submissions"] if x["student_id"] == student["id"])
    assert row["status"] == "graded"
    r = client.get("/api/v1/assignments", headers=_auth(student["token"]))
    row = next(x for x in r.json() if x["id"] == a["id"])
    assert row["status"] == "graded"


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

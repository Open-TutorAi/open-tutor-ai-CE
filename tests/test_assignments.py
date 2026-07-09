# tests/test_assignments.py
"""Assignment domain tests — Increment 6 (Epic E7).

Teachers author assignments in a class they own and grade submissions; enrolled
students submit once (re-submission replaces and clears any prior grade). Per-student
status (pending/submitted/late/missing/graded) is a computed read model.
"""

from datetime import datetime, timedelta

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
        "short_description": "A grade-6 maths class.",
        "subject": "Mathematics",
        "course": "National programme",
        "learning_objective": "Master fractions.",
        "competencies": "Reasoning",
        "learning_type": "course",
        "level": "Grade 6",
        "content_language": "English",
        "estimated_duration": "30h",
        "keywords": ["fractions"],
    }


def _create_class(client, token, name="Math · G6"):
    r = client.post(
        "/api/v1/classrooms", json=_class_payload(name), headers=_auth(token)
    )
    assert r.status_code == 201, r.text
    return r.json()


def _enrol(client, token, cid, email):
    return client.post(
        f"/api/v1/classrooms/{cid}/students",
        json={"email": email},
        headers=_auth(token),
    )


def _create_assignment(client, token, cid, **over):
    body = {"title": "Worksheet 1", "instructions": "Do all problems."}
    body.update(over)
    return client.post(
        f"/api/v1/classrooms/{cid}/assignments", json=body, headers=_auth(token)
    )


def _submit(client, token, aid, **over):
    body = {"content": "My answer"}
    body.update(over)
    return client.post(
        f"/api/v1/assignments/{aid}/submit", json=body, headers=_auth(token)
    )


def _grade(client, token, cid, aid, student_id, grade=90.0, feedback="Nice"):
    return client.post(
        f"/api/v1/classrooms/{cid}/assignments/{aid}/grade",
        json={"student_id": student_id, "grade": grade, "feedback": feedback},
        headers=_auth(token),
    )


# A teacher + class + one enrolled student — the common fixture for most tests.
def _setup(client, db, student_email="student@t.com"):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, student_email, "Student")
    cls = _create_class(client, teacher["token"])
    _enrol(client, teacher["token"], cls["id"], student_email)
    return teacher, student, cls


# ── teacher: authoring ──────────────────────────────────────────────────────


def test_create_assignment(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    r = _create_assignment(client, teacher["token"], cls["id"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "Worksheet 1"
    assert body["classroom_id"] == cls["id"]
    assert body["created_by"] == teacher["id"]
    assert body["student_count"] == 0
    assert body["submitted_count"] == 0
    assert "id" in body


def test_create_assignment_requires_title(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    r = _create_assignment(client, teacher["token"], cls["id"], title="   ")
    assert r.status_code == 422


def test_create_assignment_forbidden_for_non_teacher(client, db):
    _signup(client, "admin@t.com", "Admin")  # first → admin
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create_class(client, teacher["token"])
    r = _create_assignment(client, student["token"], cls["id"])
    assert r.status_code == 403


def test_create_assignment_other_teacher_is_403(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create_class(client, teacher["token"])
    r = _create_assignment(client, other["token"], cls["id"])
    assert r.status_code == 403


def test_create_assignment_nonexistent_class_is_404(client, db):
    teacher = _make_teacher(client, db)
    r = _create_assignment(client, teacher["token"], "no-such-class")
    assert r.status_code == 404


def test_list_assignments(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    _create_assignment(client, teacher["token"], cls["id"], title="A1")
    _create_assignment(client, teacher["token"], cls["id"], title="A2")
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments", headers=_auth(teacher["token"])
    )
    assert r.status_code == 200
    assert {a["title"] for a in r.json()} == {"A1", "A2"}


def test_list_assignments_forbidden_non_owner(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create_class(client, teacher["token"])
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments", headers=_auth(other["token"])
    )
    assert r.status_code == 403


def test_delete_assignment(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    r = client.delete(
        f"/api/v1/classrooms/{cls['id']}/assignments/{aid}",
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200
    rest = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments", headers=_auth(teacher["token"])
    ).json()
    assert rest == []


# ── teacher: assignment overview (per-student status) ───────────────────────


def test_overview_lists_roster_with_pending_status(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{aid}",
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["student_count"] == 1
    assert body["submitted_count"] == 0
    rows = body["submissions"]
    assert len(rows) == 1
    assert rows[0]["student_id"] == student["id"]
    assert rows[0]["status"] == "pending"  # no due date, no submission
    assert rows[0]["submission"] is None


def test_overview_missing_when_past_due_no_submission(client, db):
    teacher, student, cls = _setup(client, db)
    past = (datetime.utcnow() - timedelta(days=2)).isoformat()
    aid = _create_assignment(client, teacher["token"], cls["id"], due_date=past).json()[
        "id"
    ]
    rows = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{aid}",
        headers=_auth(teacher["token"]),
    ).json()["submissions"]
    assert rows[0]["status"] == "missing"


def test_overview_reflects_submission(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    _submit(client, student["token"], aid)
    body = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{aid}",
        headers=_auth(teacher["token"]),
    ).json()
    assert body["submitted_count"] == 1
    assert body["submissions"][0]["status"] == "submitted"
    assert body["submissions"][0]["submission"]["content"] == "My answer"


# ── student: submission ─────────────────────────────────────────────────────


def test_student_submit(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    r = _submit(client, student["token"], aid)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["student_id"] == student["id"]
    assert body["is_late"] is False
    assert body["status"] == "submitted"


def test_student_submit_not_enrolled_is_403(client, db):
    teacher, student, cls = _setup(client, db)
    outsider = _signup(client, "outsider@t.com", "Outsider")
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    r = _submit(client, outsider["token"], aid)
    assert r.status_code == 403


def test_student_submit_requires_content(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    r = client.post(
        f"/api/v1/assignments/{aid}/submit",
        json={"content": "   "},
        headers=_auth(student["token"]),
    )
    assert r.status_code == 422


def test_student_submit_nonexistent_assignment_404(client, db):
    teacher, student, cls = _setup(client, db)
    r = _submit(client, student["token"], "no-such-assignment")
    assert r.status_code == 404


def test_submit_is_late_when_past_due(client, db):
    teacher, student, cls = _setup(client, db)
    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    aid = _create_assignment(client, teacher["token"], cls["id"], due_date=past).json()[
        "id"
    ]
    body = _submit(client, student["token"], aid).json()
    assert body["is_late"] is True


def test_submit_on_time_when_future_due(client, db):
    teacher, student, cls = _setup(client, db)
    future = (datetime.utcnow() + timedelta(days=1)).isoformat()
    aid = _create_assignment(
        client, teacher["token"], cls["id"], due_date=future
    ).json()["id"]
    body = _submit(client, student["token"], aid).json()
    assert body["is_late"] is False


def test_resubmit_replaces_and_clears_grade(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    _submit(client, student["token"], aid, content="first")
    _grade(client, teacher["token"], cls["id"], aid, student["id"], grade=80.0)
    # student re-submits → grade is cleared, content replaced
    r = _submit(client, student["token"], aid, content="second")
    assert r.status_code == 201
    body = r.json()
    assert body["content"] == "second"
    assert body["grade"] is None
    assert body["status"] == "submitted"


def test_get_my_submission_null_then_value(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    before = client.get(
        f"/api/v1/assignments/{aid}/submission", headers=_auth(student["token"])
    )
    assert before.status_code == 200
    assert before.json() is None
    _submit(client, student["token"], aid)
    after = client.get(
        f"/api/v1/assignments/{aid}/submission", headers=_auth(student["token"])
    ).json()
    assert after["content"] == "My answer"


# ── teacher: grading ────────────────────────────────────────────────────────


def test_grade_submission(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    _submit(client, student["token"], aid)
    r = _grade(client, teacher["token"], cls["id"], aid, student["id"], grade=95.0)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grade"] == 95.0
    assert body["feedback"] == "Nice"
    assert body["status"] == "graded"
    assert body["graded_at"] is not None


def test_grade_missing_submission_404(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    r = _grade(client, teacher["token"], cls["id"], aid, student["id"])
    assert r.status_code == 404


def test_grade_forbidden_non_owner(client, db):
    teacher, student, cls = _setup(client, db)
    other = _make_teacher(client, db, "other@t.com")
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    _submit(client, student["token"], aid)
    r = _grade(client, other["token"], cls["id"], aid, student["id"])
    assert r.status_code == 403


def test_overview_graded_status(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    _submit(client, student["token"], aid)
    _grade(client, teacher["token"], cls["id"], aid, student["id"], grade=88.0)
    rows = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{aid}",
        headers=_auth(teacher["token"]),
    ).json()["submissions"]
    assert rows[0]["status"] == "graded"
    assert rows[0]["submission"]["grade"] == 88.0


# ── student: cross-class feed ───────────────────────────────────────────────


def test_student_feed_lists_enrolled_assignments(client, db):
    teacher, student, cls = _setup(client, db)
    _create_assignment(client, teacher["token"], cls["id"], title="Feed A1")
    r = client.get("/api/v1/assignments", headers=_auth(student["token"]))
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["title"] == "Feed A1"
    assert body[0]["class_name"] == "Math · G6"
    assert body[0]["status"] == "pending"


def test_student_feed_excludes_unenrolled_classes(client, db):
    teacher, student, cls = _setup(client, db)
    # A second class the student is NOT enrolled in.
    other_cls = _create_class(client, teacher["token"], name="Physics")
    _create_assignment(client, teacher["token"], other_cls["id"], title="Hidden")
    titles = {
        a["title"]
        for a in client.get(
            "/api/v1/assignments", headers=_auth(student["token"])
        ).json()
    }
    assert "Hidden" not in titles


def test_student_feed_empty_for_unenrolled_user(client, db):
    _make_teacher(client, db, "teacher@t.com")
    loner = _signup(client, "loner@t.com", "Loner")
    r = client.get("/api/v1/assignments", headers=_auth(loner["token"]))
    assert r.status_code == 200
    assert r.json() == []


# ── Attachments (E7 file attachments) ───────────────────────────────────────


def _upload(client, token, content=b"file-bytes", filename="doc.pdf"):
    """Upload a blob via the generic files endpoint; return its file_id."""
    r = client.post(
        "/api/v1/files/",
        files={"file": (filename, content, "application/pdf")},
        headers=_auth(token),
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_assignment_attachment_downloadable_by_enrolled_student(client, db):
    teacher, student, cls = _setup(client, db)
    fid = _upload(client, teacher["token"], b"worksheet-pdf", "ws.pdf")
    a = _create_assignment(
        client, teacher["token"], cls["id"], attachment_id=fid
    ).json()
    assert a["attachment_id"] == fid
    assert a["attachment_name"] == "ws.pdf"

    r = client.get(
        f"/api/v1/assignments/{a['id']}/attachment", headers=_auth(student["token"])
    )
    assert r.status_code == 200, r.text
    assert r.content == b"worksheet-pdf"
    # Teacher (owner) can read it too.
    rt = client.get(
        f"/api/v1/assignments/{a['id']}/attachment", headers=_auth(teacher["token"])
    )
    assert rt.status_code == 200


def test_assignment_attachment_denied_to_non_enrolled(client, db):
    teacher, student, cls = _setup(client, db)
    outsider = _signup(client, "out@t.com", "Out")
    fid = _upload(client, teacher["token"])
    a = _create_assignment(
        client, teacher["token"], cls["id"], attachment_id=fid
    ).json()
    r = client.get(
        f"/api/v1/assignments/{a['id']}/attachment", headers=_auth(outsider["token"])
    )
    assert r.status_code == 403


def test_assignment_without_attachment_is_404(client, db):
    teacher, student, cls = _setup(client, db)
    a = _create_assignment(client, teacher["token"], cls["id"]).json()
    r = client.get(
        f"/api/v1/assignments/{a['id']}/attachment", headers=_auth(student["token"])
    )
    assert r.status_code == 404


def test_submission_attachment_roundtrip(client, db):
    teacher, student, cls = _setup(client, db)
    a = _create_assignment(client, teacher["token"], cls["id"]).json()
    fid = _upload(client, student["token"], b"my-homework", "hw.pdf")
    sub = _submit(
        client, student["token"], a["id"], content="", attachment_id=fid
    ).json()
    assert sub["attachment_id"] == fid
    assert sub["attachment_name"] == "hw.pdf"

    # Student reads their own submission attachment.
    own = client.get(
        f"/api/v1/assignments/{a['id']}/submission/attachment",
        headers=_auth(student["token"]),
    )
    assert own.status_code == 200
    assert own.content == b"my-homework"

    # Teacher downloads the student's submission attachment.
    t = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{a['id']}/students/{student['id']}/submission/attachment",
        headers=_auth(teacher["token"]),
    )
    assert t.status_code == 200
    assert t.content == b"my-homework"


def test_submission_attachment_not_visible_to_other_student(client, db):
    teacher, student, cls = _setup(client, db)
    other = _signup(client, "other@t.com", "Other")
    _enrol(client, teacher["token"], cls["id"], "other@t.com")
    a = _create_assignment(client, teacher["token"], cls["id"]).json()
    fid = _upload(client, student["token"], b"secret", "s.pdf")
    _submit(client, student["token"], a["id"], content="", attachment_id=fid)

    # Other student hits the teacher route (denied — not the owner) ...
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{a['id']}/students/{student['id']}/submission/attachment",
        headers=_auth(other["token"]),
    )
    assert r.status_code in (403, 404)
    # ... and their own submission attachment doesn't exist.
    r2 = client.get(
        f"/api/v1/assignments/{a['id']}/submission/attachment",
        headers=_auth(other["token"]),
    )
    assert r2.status_code == 404


def test_cannot_attach_a_file_you_do_not_own(client, db):
    teacher, student, cls = _setup(client, db)
    others_file = _upload(client, student["token"], b"not-yours")  # owned by student
    r = _create_assignment(
        client, teacher["token"], cls["id"], attachment_id=others_file
    )
    assert r.status_code == 403


# ── teacher: editing (PUT) ──────────────────────────────────────────────────


def _update(client, token, cid, aid, **over):
    body = {"title": "Edited title", "instructions": "Edited."}
    body.update(over)
    return client.put(
        f"/api/v1/classrooms/{cid}/assignments/{aid}", json=body, headers=_auth(token)
    )


def test_update_assignment_edits_fields(client, db):
    teacher, _, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    r = _update(
        client,
        teacher["token"],
        cls["id"],
        aid,
        title="New title",
        instructions="New instructions",
        due_date="2030-01-01T10:00:00",
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["title"] == "New title"
    assert body["instructions"] == "New instructions"
    assert body["due_date"].startswith("2030-01-01")


def test_update_assignment_keeps_submissions(client, db):
    teacher, student, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    _submit(client, student["token"], aid)
    # Editing the assignment must not disturb the existing submission.
    _update(client, teacher["token"], cls["id"], aid, title="Renamed")
    detail = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments/{aid}",
        headers=_auth(teacher["token"]),
    ).json()
    assert detail["title"] == "Renamed"
    assert detail["submitted_count"] == 1
    row = next(r for r in detail["submissions"] if r["student_id"] == student["id"])
    assert row["submission"]["content"] == "My answer"


def test_update_exam_assignment_rejected(client, db):
    teacher, _, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    # Turn it into an exam, then editing must be refused.
    client.post(
        f"/api/v1/classrooms/{cls['id']}/assignments/{aid}/exam",
        json={"require_fullscreen": True},
        headers=_auth(teacher["token"]),
    )
    r = _update(client, teacher["token"], cls["id"], aid, title="nope")
    assert r.status_code == 422
    assert "Exam" in r.json()["detail"]


def test_update_assignment_forbidden_for_other_teacher(client, db):
    teacher, _, cls = _setup(client, db)
    other = _make_teacher(client, db, "other@t.com")
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    assert _update(client, other["token"], cls["id"], aid).status_code == 403


def test_update_missing_assignment_404(client, db):
    teacher, _, cls = _setup(client, db)
    assert _update(client, teacher["token"], cls["id"], "nope").status_code == 404


def test_update_assignment_requires_title(client, db):
    teacher, _, cls = _setup(client, db)
    aid = _create_assignment(client, teacher["token"], cls["id"]).json()["id"]
    assert (
        _update(client, teacher["token"], cls["id"], aid, title="   ").status_code
        == 422
    )

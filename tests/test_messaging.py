# tests/test_messaging.py
"""Messaging domain tests — teacher ↔ student 1:1 conversations.

Starting a conversation requires a shared class (teacher ↔ enrolled student); once it
exists either side may read/send. Unread counts come from each participant's last_read_at.
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


def _start(client, token, recipient_id):
    return client.post(
        "/api/v1/conversations",
        json={"recipient_id": recipient_id},
        headers=_auth(token),
    )


def _send(client, token, cid, body):
    return client.post(
        f"/api/v1/conversations/{cid}/messages",
        json={"body": body},
        headers=_auth(token),
    )


def _messages(client, token, cid):
    return client.get(f"/api/v1/conversations/{cid}/messages", headers=_auth(token))


def _list(client, token):
    return client.get("/api/v1/conversations", headers=_auth(token))


# A teacher + class + one enrolled student.
def _setup(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create_class(client, teacher["token"])
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    return teacher, student, cls


# ── starting conversations ──────────────────────────────────────────────────


def test_teacher_starts_conversation_with_enrolled_student(client, db):
    teacher, student, cls = _setup(client, db)
    r = _start(client, teacher["token"], student["id"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["other_user_id"] == student["id"]
    assert body["other_name"] == "Student"
    assert body["unread"] == 0


def test_start_is_idempotent(client, db):
    teacher, student, cls = _setup(client, db)
    first = _start(client, teacher["token"], student["id"]).json()
    second = _start(client, teacher["token"], student["id"]).json()
    assert first["id"] == second["id"]
    # And the student starting it resolves to the same thread.
    third = _start(client, student["token"], teacher["id"]).json()
    assert third["id"] == first["id"]


def test_cannot_message_unrelated_user(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    stranger = _signup(client, "stranger@t.com", "Stranger")  # not in any class
    r = _start(client, teacher["token"], stranger["id"])
    assert r.status_code == 403


def test_cannot_message_self(client, db):
    teacher, student, cls = _setup(client, db)
    r = _start(client, teacher["token"], teacher["id"])
    assert r.status_code == 422


def test_start_nonexistent_recipient_404(client, db):
    teacher, student, cls = _setup(client, db)
    r = _start(client, teacher["token"], "no-such-user")
    assert r.status_code == 404


# ── sending / reading ───────────────────────────────────────────────────────


def test_send_and_read_messages(client, db):
    teacher, student, cls = _setup(client, db)
    cid = _start(client, teacher["token"], student["id"]).json()["id"]
    r = _send(client, teacher["token"], cid, "Hello, please review fractions.")
    assert r.status_code == 201, r.text
    assert r.json()["body"] == "Hello, please review fractions."

    got = _messages(client, student["token"], cid)
    assert got.status_code == 200
    bodies = [m["body"] for m in got.json()["messages"]]
    assert bodies == ["Hello, please review fractions."]


def test_send_empty_body_is_422(client, db):
    teacher, student, cls = _setup(client, db)
    cid = _start(client, teacher["token"], student["id"]).json()["id"]
    r = _send(client, teacher["token"], cid, "   ")
    assert r.status_code == 422


def test_non_participant_cannot_read_or_send(client, db):
    teacher, student, cls = _setup(client, db)
    other = _make_teacher(client, db, "other@t.com")
    cid = _start(client, teacher["token"], student["id"]).json()["id"]
    # An unrelated teacher is not a participant → 404 (existence hidden).
    assert _messages(client, other["token"], cid).status_code == 404
    assert _send(client, other["token"], cid, "sneaky").status_code == 404


def test_two_way_conversation(client, db):
    teacher, student, cls = _setup(client, db)
    cid = _start(client, teacher["token"], student["id"]).json()["id"]
    _send(client, teacher["token"], cid, "Question?")
    _send(client, student["token"], cid, "Answer!")
    bodies = [
        m["body"] for m in _messages(client, teacher["token"], cid).json()["messages"]
    ]
    assert bodies == ["Question?", "Answer!"]


# ── unread + listing ────────────────────────────────────────────────────────


def test_unread_count_and_clear_on_read(client, db):
    teacher, student, cls = _setup(client, db)
    cid = _start(client, teacher["token"], student["id"]).json()["id"]
    _send(client, teacher["token"], cid, "m1")
    _send(client, teacher["token"], cid, "m2")

    # Student hasn't opened the thread → 2 unread in their list.
    convs = _list(client, student["token"]).json()
    assert len(convs) == 1
    assert convs[0]["unread"] == 2
    assert convs[0]["last_message"] == "m2"

    # Opening the thread marks read → 0 unread afterwards.
    _messages(client, student["token"], cid)
    convs = _list(client, student["token"]).json()
    assert convs[0]["unread"] == 0


def test_sender_has_no_unread_for_own_messages(client, db):
    teacher, student, cls = _setup(client, db)
    cid = _start(client, teacher["token"], student["id"]).json()["id"]
    _send(client, teacher["token"], cid, "hi")
    convs = _list(client, teacher["token"]).json()
    assert convs[0]["unread"] == 0


def test_list_orders_by_recent_activity(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    s1 = _signup(client, "s1@t.com", "S1")
    s2 = _signup(client, "s2@t.com", "S2")
    cls = _create_class(client, teacher["token"])
    _enrol(client, teacher["token"], cls["id"], "s1@t.com")
    _enrol(client, teacher["token"], cls["id"], "s2@t.com")
    c1 = _start(client, teacher["token"], s1["id"]).json()["id"]
    c2 = _start(client, teacher["token"], s2["id"]).json()["id"]
    _send(client, teacher["token"], c1, "to s1")
    _send(client, teacher["token"], c2, "to s2")  # most recent

    convs = _list(client, teacher["token"]).json()
    assert convs[0]["id"] == c2  # latest activity first
    assert convs[1]["id"] == c1


def test_empty_conversation_list(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    r = _list(client, teacher["token"])
    assert r.status_code == 200
    assert r.json() == []


# ── Attachments (file attachments on messages) ──────────────────────────────


def _upload(client, token, content=b"msg-file", filename="note.pdf"):
    r = client.post(
        "/api/v1/files/",
        files={"file": (filename, content, "application/pdf")},
        headers=_auth(token),
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_send_message_with_attachment(client, db):
    teacher, student, cls = _setup(client, db)
    conv = _start(client, teacher["token"], student["id"]).json()
    fid = _upload(client, teacher["token"], b"lesson-plan", "plan.pdf")
    r = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"body": "see attached", "attachment_id": fid},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 201, r.text
    msg = r.json()
    assert msg["attachment_id"] == fid
    assert msg["attachment_name"] == "plan.pdf"

    # The student (a participant) can download it.
    dl = client.get(
        f"/api/v1/conversations/{conv['id']}/messages/{msg['id']}/attachment",
        headers=_auth(student["token"]),
    )
    assert dl.status_code == 200
    assert dl.content == b"lesson-plan"


def test_attachment_only_message_allowed(client, db):
    teacher, student, cls = _setup(client, db)
    conv = _start(client, teacher["token"], student["id"]).json()
    fid = _upload(client, student["token"], b"hw", "hw.pdf")
    r = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"attachment_id": fid},
        headers=_auth(student["token"]),
    )
    assert r.status_code == 201, r.text
    assert r.json()["body"] in (None, "")
    assert r.json()["attachment_id"] == fid


def test_message_without_body_or_attachment_is_422(client, db):
    teacher, student, cls = _setup(client, db)
    conv = _start(client, teacher["token"], student["id"]).json()
    r = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"body": "   "},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 422


def test_message_attachment_not_downloadable_by_non_participant(client, db):
    teacher, student, cls = _setup(client, db)
    outsider = _make_teacher(client, db, "outsider@t.com")
    conv = _start(client, teacher["token"], student["id"]).json()
    fid = _upload(client, teacher["token"])
    msg = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"body": "x", "attachment_id": fid},
        headers=_auth(teacher["token"]),
    ).json()
    r = client.get(
        f"/api/v1/conversations/{conv['id']}/messages/{msg['id']}/attachment",
        headers=_auth(outsider["token"]),
    )
    assert r.status_code == 404  # membership 404 hides existence


def test_cannot_attach_unowned_file_to_message(client, db):
    teacher, student, cls = _setup(client, db)
    conv = _start(client, teacher["token"], student["id"]).json()
    students_file = _upload(client, student["token"], b"theirs")
    r = client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"body": "x", "attachment_id": students_file},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 403

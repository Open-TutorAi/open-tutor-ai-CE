# tests/test_resources.py
"""Resource domain tests — Increment 8 (Epic E8).

Class materials (teacher manages, enrolled students read/download) + teacher-owned
assignment templates (reusable; create-from-template delegates to the E7 context).
Blobs are stored/served via the existing `content/files` domain — this context owns
only metadata + links.
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


def _upload(
    client, token, cid, title="Week 1 notes", description="Intro", body=b"PDF-BYTES"
):
    return client.post(
        f"/api/v1/classrooms/{cid}/resources",
        files={"file": ("notes.pdf", body, "application/pdf")},
        data={"title": title, "description": description},
        headers=_auth(token),
    )


def _save_template(client, token, title="Weekly quiz", instructions="Answer all."):
    return client.post(
        "/api/v1/assignment-templates",
        json={"title": title, "instructions": instructions},
        headers=_auth(token),
    )


# A teacher + class + one enrolled student.
def _setup(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create_class(client, teacher["token"])
    _enrol(client, teacher["token"], cls["id"], "student@t.com")
    return teacher, student, cls


# ── class materials ─────────────────────────────────────────────────────────


def test_upload_material(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    r = _upload(client, teacher["token"], cls["id"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "Week 1 notes"
    assert body["filename"] == "notes.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["size"] == len(b"PDF-BYTES")
    assert body["classroom_id"] == cls["id"]


def test_upload_material_requires_title(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    r = _upload(client, teacher["token"], cls["id"], title="   ")
    assert r.status_code == 422


def test_upload_rejects_disallowed_mime(client, db):
    """A non-allowlisted type (e.g. an executable) is refused with 415."""
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/resources",
        files={"file": ("evil.exe", b"MZ...", "application/x-msdownload")},
        data={"title": "Bad", "description": "x"},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 415


def test_upload_forbidden_for_non_teacher(client, db):
    _signup(client, "admin@t.com", "Admin")  # first → admin
    teacher = _make_teacher(client, db, "teacher@t.com")
    student = _signup(client, "student@t.com", "Student")
    cls = _create_class(client, teacher["token"])
    r = _upload(client, student["token"], cls["id"])
    assert r.status_code == 403


def test_upload_other_teacher_class_is_403(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create_class(client, teacher["token"])
    r = _upload(client, other["token"], cls["id"])
    assert r.status_code == 403


def test_list_materials_teacher(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    _upload(client, teacher["token"], cls["id"], title="A")
    _upload(client, teacher["token"], cls["id"], title="B")
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/resources", headers=_auth(teacher["token"])
    )
    assert r.status_code == 200
    assert {m["title"] for m in r.json()} == {"A", "B"}


def test_list_materials_enrolled_student(client, db):
    teacher, student, cls = _setup(client, db)
    _upload(client, teacher["token"], cls["id"], title="Handout")
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/resources", headers=_auth(student["token"])
    )
    assert r.status_code == 200
    assert [m["title"] for m in r.json()] == ["Handout"]


def test_list_materials_forbidden_outsider(client, db):
    teacher, student, cls = _setup(client, db)
    outsider = _signup(client, "outsider@t.com", "Outsider")
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/resources", headers=_auth(outsider["token"])
    )
    assert r.status_code == 403


def test_download_material_enrolled_student(client, db):
    teacher, student, cls = _setup(client, db)
    rid = _upload(client, teacher["token"], cls["id"], body=b"HELLO-BLOB").json()["id"]
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/resources/{rid}/content",
        headers=_auth(student["token"]),
    )
    assert r.status_code == 200
    assert r.content == b"HELLO-BLOB"


def test_download_material_outsider_403(client, db):
    teacher, student, cls = _setup(client, db)
    outsider = _signup(client, "outsider@t.com", "Outsider")
    rid = _upload(client, teacher["token"], cls["id"]).json()["id"]
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/resources/{rid}/content",
        headers=_auth(outsider["token"]),
    )
    assert r.status_code == 403


def test_download_missing_material_404(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    r = client.get(
        f"/api/v1/classrooms/{cls['id']}/resources/nope/content",
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 404


def test_delete_material(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    rid = _upload(client, teacher["token"], cls["id"]).json()["id"]
    r = client.delete(
        f"/api/v1/classrooms/{cls['id']}/resources/{rid}",
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 200
    rest = client.get(
        f"/api/v1/classrooms/{cls['id']}/resources", headers=_auth(teacher["token"])
    ).json()
    assert rest == []


def test_delete_material_forbidden_non_owner(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create_class(client, teacher["token"])
    rid = _upload(client, teacher["token"], cls["id"]).json()["id"]
    r = client.delete(
        f"/api/v1/classrooms/{cls['id']}/resources/{rid}", headers=_auth(other["token"])
    )
    assert r.status_code == 403


# ── assignment templates ────────────────────────────────────────────────────


def test_save_template(client, db):
    teacher = _make_teacher(client, db)
    r = _save_template(client, teacher["token"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "Weekly quiz"
    assert body["owner_teacher_id"] == teacher["id"]


def test_save_template_requires_title(client, db):
    teacher = _make_teacher(client, db)
    r = client.post(
        "/api/v1/assignment-templates",
        json={"title": "   "},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 422


def test_list_templates_owner_only(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    _save_template(client, teacher["token"], title="Mine")
    other_list = client.get(
        "/api/v1/assignment-templates", headers=_auth(other["token"])
    ).json()
    assert other_list == []
    mine = client.get(
        "/api/v1/assignment-templates", headers=_auth(teacher["token"])
    ).json()
    assert {t["title"] for t in mine} == {"Mine"}


def test_delete_template(client, db):
    teacher = _make_teacher(client, db)
    tid = _save_template(client, teacher["token"]).json()["id"]
    r = client.delete(
        f"/api/v1/assignment-templates/{tid}", headers=_auth(teacher["token"])
    )
    assert r.status_code == 200
    assert (
        client.get(
            "/api/v1/assignment-templates", headers=_auth(teacher["token"])
        ).json()
        == []
    )


def test_delete_template_forbidden_non_owner(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    tid = _save_template(client, teacher["token"]).json()["id"]
    r = client.delete(
        f"/api/v1/assignment-templates/{tid}", headers=_auth(other["token"])
    )
    assert r.status_code == 403


# ── flat library ────────────────────────────────────────────────────────────


def test_library_lists_materials_and_templates(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    _upload(client, teacher["token"], cls["id"], title="Material A")
    _save_template(client, teacher["token"], title="Template A")
    r = client.get("/api/v1/resources", headers=_auth(teacher["token"]))
    assert r.status_code == 200
    body = r.json()
    assert {m["title"] for m in body["materials"]} == {"Material A"}
    assert body["materials"][0]["class_name"] == "Math · G6"
    assert {t["title"] for t in body["templates"]} == {"Template A"}


# ── create assignment from template (delegates to E7) ───────────────────────


def test_create_assignment_from_template(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    tid = _save_template(
        client, teacher["token"], title="Quiz 1", instructions="Solve it."
    ).json()["id"]
    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/assignments/from-template",
        json={"template_id": tid},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "Quiz 1"
    assert body["instructions"] == "Solve it."
    # It is a real assignment now — visible in the class assignment list.
    listed = client.get(
        f"/api/v1/classrooms/{cls['id']}/assignments", headers=_auth(teacher["token"])
    ).json()
    assert {a["title"] for a in listed} == {"Quiz 1"}


def test_from_template_other_teacher_template_is_403(client, db):
    teacher = _make_teacher(client, db, "teacher@t.com")
    other = _make_teacher(client, db, "other@t.com")
    cls = _create_class(client, other["token"])
    tid = _save_template(client, teacher["token"]).json()["id"]  # owned by `teacher`
    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/assignments/from-template",
        json={"template_id": tid},
        headers=_auth(other["token"]),
    )
    assert r.status_code == 403


def test_from_template_nonexistent_template_404(client, db):
    teacher = _make_teacher(client, db)
    cls = _create_class(client, teacher["token"])
    r = client.post(
        f"/api/v1/classrooms/{cls['id']}/assignments/from-template",
        json={"template_id": "nope"},
        headers=_auth(teacher["token"]),
    )
    assert r.status_code == 404

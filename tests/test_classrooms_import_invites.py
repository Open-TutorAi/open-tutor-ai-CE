import io
import csv
import uuid
from datetime import date


import pytest

from data.models import User, Enrollment


def _signup(client, email, name):
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": name, "password": "pass1234!"},
    )
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_import_students_from_csv_creates_and_enrolls(client, db):
    owner_token = _signup(client, "owner-import@t.com", "OwnerImport")
    # create classroom
    created = client.post(
        "/api/classrooms", json={"name": "CSV Class"}, headers=_auth(owner_token)
    ).json()

    # pre-create an existing student
    existing_token = _signup(client, "existing@t.com", "Existing")

    csv_rows = [
        ("email", "name", "password"),
        ("newstudent@t.com", "New Student", "secret1"),
        ("existing@t.com", "Existing", "secret2"),
        ("", "No Email", ""),
    ]
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerows(csv_rows)
    stream.seek(0)

    files = {"file": ("students.csv", stream.read().encode("utf-8"), "text/csv")}

    r = client.post(
        f"/api/classrooms/{created['id']}/import",
        files=files,
        headers=_auth(owner_token),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["created"] == 1
    assert data["enrolled"] >= 1

    # verify users and enrollments in DB
    new_user = db.query(User).filter(User.email == "newstudent@t.com").first()
    assert new_user is not None
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.classroom_id == created["id"],
            Enrollment.student_id == new_user.id,
        )
        .first()
    )
    assert enrollment is not None


@pytest.mark.integration
def test_invite_create_and_redeem(client, db):
    owner_token = _signup(client, "owner-invite@t.com", "OwnerInvite")
    created = client.post(
        "/api/classrooms", json={"name": "Invite Class"}, headers=_auth(owner_token)
    ).json()

    # create invite
    r = client.post(
        f"/api/classrooms/{created['id']}/invites", json={}, headers=_auth(owner_token)
    )
    assert r.status_code == 201
    invite = r.json()
    assert "code" in invite

    # redeem as another user
    redeemer_token = _signup(client, "redeemer@t.com", "Redeemer")
    r2 = client.post(
        f"/api/classrooms/invites/{invite['code']}/redeem",
        headers=_auth(redeemer_token),
    )
    assert r2.status_code == 200
    res = r2.json()
    assert res["enrolled"] is True or res["enrolled"] is False

    # check enrollment exists
    student = db.query(User).filter(User.email == "redeemer@t.com").first()
    assert student is not None
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.classroom_id == created["id"],
            Enrollment.student_id == student.id,
        )
        .first()
    )
    assert enrollment is not None


@pytest.mark.integration
def test_classroom_detail_exposes_a_persistent_join_code(client, db):
    owner_token = _signup(client, "owner-joincode@t.com", "OwnerJoinCode")
    created = client.post(
        "/api/classrooms", json={"name": "Join Code Class"}, headers=_auth(owner_token)
    ).json()

    r1 = client.get(f"/api/classrooms/{created['id']}", headers=_auth(owner_token))
    assert r1.status_code == 200
    code_1 = r1.json()["join_code"]
    assert code_1

    # fetching again returns the same code (not regenerated each time)
    r2 = client.get(f"/api/classrooms/{created['id']}", headers=_auth(owner_token))
    assert r2.json()["join_code"] == code_1

    # the persistent code can be redeemed like any other invite code
    student_token = _signup(client, "joincode-student@t.com", "JoinCodeStudent")
    redeemed = client.post(
        f"/api/classrooms/invites/{code_1}/redeem", headers=_auth(student_token)
    )
    assert redeemed.status_code == 200
    assert redeemed.json()["enrolled"] is True


@pytest.mark.integration
def test_redeem_invite_is_rate_limited_against_code_guessing(client):
    student_token = _signup(client, "guesser@t.com", "Guesser")
    statuses = [
        client.post(
            "/api/classrooms/invites/not-a-real-code/redeem",
            headers=_auth(student_token),
        ).status_code
        for _ in range(11)
    ]

    assert statuses[:10] == [404] * 10
    assert statuses[10] == 429

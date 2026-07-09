# tests/test_assignments.py
"""Repository- and service-layer tests for the Assignments domain."""

import json as jsonlib

import pytest

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import Assignment, Submission
from learning.assignments.repository import AssignmentRepository, SubmissionRepository

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _assignment_repo(db):
    return AssignmentRepository(db, Assignment)


def _submission_repo(db):
    return SubmissionRepository(db, Submission)


def test_create_assignment_persists_fields(db):
    repo = _assignment_repo(db)

    assignment = repo.create(
        id="a1",
        user_id="teacher-1",
        title="Fractions Practice Set",
        description="Solve the fraction problems.",
        rubric="Award points for correctness and shown working.",
    )

    assert assignment.id == "a1"
    assert assignment.user_id == "teacher-1"
    assert assignment.title == "Fractions Practice Set"
    assert assignment.description == "Solve the fraction problems."
    assert assignment.rubric == "Award points for correctness and shown working."
    assert assignment.due_date is None


def test_list_assignments_scoped_to_teacher(db):
    repo = _assignment_repo(db)
    repo.create(id="a1", user_id="teacher-1", title="A1", rubric="r")
    repo.create(id="a2", user_id="teacher-1", title="A2", rubric="r")
    repo.create(id="a3", user_id="teacher-2", title="A3", rubric="r")

    result = repo.get_by_user("teacher-1")

    assert {a.id for a in result} == {"a1", "a2"}


def test_create_submission_persists_fields(db):
    assignments = _assignment_repo(db)
    submissions = _submission_repo(db)
    assignment = assignments.create(
        id="a1", user_id="teacher-1", title="A1", rubric="r"
    )

    submission = submissions.create(
        id="s1",
        assignment_id=assignment.id,
        user_id="student-1",
        filename="answers.pdf",
        file_path="/var/uploads/answers.pdf",
        file_size=1024,
        status="submitted",
    )

    assert submission.id == "s1"
    assert submission.assignment_id == "a1"
    assert submission.user_id == "student-1"
    assert submission.filename == "answers.pdf"
    assert submission.status == "submitted"
    assert submission.extracted_text is None
    assert submission.ai_score is None
    assert submission.ai_feedback is None
    assert submission.teacher_score is None


def test_get_submission_by_id(db):
    assignments = _assignment_repo(db)
    submissions = _submission_repo(db)
    assignment = assignments.create(
        id="a1", user_id="teacher-1", title="A1", rubric="r"
    )
    created = submissions.create(
        id="s1",
        assignment_id=assignment.id,
        user_id="student-1",
        filename="a.pdf",
        file_path="/x/a.pdf",
        status="submitted",
    )

    fetched = submissions.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == "s1"


def test_list_submissions_by_assignment(db):
    assignments = _assignment_repo(db)
    submissions = _submission_repo(db)
    a1 = assignments.create(id="a1", user_id="teacher-1", title="A1", rubric="r")
    a2 = assignments.create(id="a2", user_id="teacher-1", title="A2", rubric="r")
    submissions.create(
        id="s1",
        assignment_id=a1.id,
        user_id="student-1",
        filename="a.pdf",
        file_path="/x/a.pdf",
        status="submitted",
    )
    submissions.create(
        id="s2",
        assignment_id=a1.id,
        user_id="student-2",
        filename="b.pdf",
        file_path="/x/b.pdf",
        status="submitted",
    )
    submissions.create(
        id="s3",
        assignment_id=a2.id,
        user_id="student-1",
        filename="c.pdf",
        file_path="/x/c.pdf",
        status="submitted",
    )

    result = submissions.get_by_assignment(a1.id)

    assert {s.id for s in result} == {"s1", "s2"}


def test_get_submission_by_assignment_and_user(db):
    assignments = _assignment_repo(db)
    submissions = _submission_repo(db)
    a1 = assignments.create(id="a1", user_id="teacher-1", title="A1", rubric="r")
    submissions.create(
        id="s1",
        assignment_id=a1.id,
        user_id="student-1",
        filename="a.pdf",
        file_path="/x/a.pdf",
        status="submitted",
    )

    result = submissions.get_by_assignment_and_user(a1.id, "student-1")
    assert result is not None
    assert result.id == "s1"

    missing = submissions.get_by_assignment_and_user(a1.id, "student-2")
    assert missing is None


# ---------------------------------------------------------------------------
# Service-layer tests.
#
# Written before learning/assignments/service.py exists (TDD red step).
# `extract_pdf_text`, `proxy_json` and `ProvidersService` are monkeypatched at
# the module level of learning.assignments.service, so the tests never touch
# a real PDF parser or a real AI provider.
# ---------------------------------------------------------------------------

from learning.assignments.service import AssignmentService  # noqa: E402


class _FakeProvidersService:
    """Stands in for ai.providers.service.ProvidersService in tests."""

    def __init__(self, session):
        pass

    async def resolve_provider(self, model_id):
        return "http://fake", "fake-key", "chat/completions"


def _mock_provider_resolution(monkeypatch, service_module):
    monkeypatch.setattr(service_module, "ProvidersService", _FakeProvidersService)


def test_create_assignment_via_service(db):
    svc = AssignmentService(db)

    assignment = svc.create_assignment(
        "teacher-1",
        {
            "title": "Fractions Practice Set",
            "description": "Solve the fraction problems.",
            "rubric": "Correctness + working shown.",
        },
    )

    assert assignment.id
    assert assignment.user_id == "teacher-1"
    assert assignment.title == "Fractions Practice Set"


def test_verify_assignment_ownership_raises_not_found(db):
    svc = AssignmentService(db)

    with pytest.raises(NotFoundError):
        svc.verify_assignment_ownership("teacher-1", "missing-id")


def test_verify_assignment_ownership_raises_for_other_teacher(db):
    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})

    with pytest.raises(AuthorizationError):
        svc.verify_assignment_ownership("teacher-2", assignment.id)


def test_verify_assignment_ownership_returns_assignment_when_owned(db):
    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})

    result = svc.verify_assignment_ownership("teacher-1", assignment.id)

    assert result.id == assignment.id


def test_submit_work_extracts_text_when_pdf_readable(db, tmp_path, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(
        service_module, "extract_pdf_text", lambda contents: "3/4 + 1/8 = 7/8"
    )

    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})

    submission = svc.submit_work(
        "student-1", assignment.id, "answers.pdf", b"%PDF-fake-bytes", str(tmp_path)
    )

    assert submission.extracted_text == "3/4 + 1/8 = 7/8"
    assert submission.status == "submitted"


def test_submit_work_falls_back_when_extraction_empty(db, tmp_path, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: None)

    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})

    submission = svc.submit_work(
        "student-1", assignment.id, "scan.pdf", b"not-real-pdf-bytes", str(tmp_path)
    )

    assert submission.extracted_text is None
    assert submission.status == "needs_manual_review"


def test_submit_work_raises_not_found_for_missing_assignment(db, tmp_path):
    svc = AssignmentService(db)

    with pytest.raises(NotFoundError):
        svc.submit_work("student-1", "missing-id", "a.pdf", b"bytes", str(tmp_path))


def test_verify_submission_ownership_raises_for_other_student(
    db, tmp_path, monkeypatch
):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")
    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})
    submission = svc.submit_work(
        "student-1", assignment.id, "a.pdf", b"bytes", str(tmp_path)
    )

    with pytest.raises(AuthorizationError):
        svc.verify_submission_ownership("student-2", submission.id)


async def test_request_ai_grade_success(db, tmp_path, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(
        service_module, "extract_pdf_text", lambda contents: "3/4 + 1/8 = 7/8"
    )
    _mock_provider_resolution(monkeypatch, service_module)

    async def fake_proxy_json(url, key, method, path, body=None):
        return {
            "choices": [
                {
                    "message": {
                        "content": jsonlib.dumps(
                            {"score": 78, "feedback": "Good work overall."}
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr(service_module, "proxy_json", fake_proxy_json)

    svc = AssignmentService(db)
    assignment = svc.create_assignment(
        "teacher-1", {"title": "A", "rubric": "Correctness"}
    )
    submission = svc.submit_work(
        "student-1", assignment.id, "a.pdf", b"bytes", str(tmp_path)
    )

    graded = await svc.request_ai_grade(
        "teacher-1", assignment.id, submission.id, "test-model"
    )

    assert graded.ai_score == 78
    assert graded.ai_feedback == "Good work overall."
    assert graded.status == "ai_graded"


async def test_request_ai_grade_upstream_failure_falls_back_gracefully(
    db, tmp_path, monkeypatch
):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")
    _mock_provider_resolution(monkeypatch, service_module)

    async def failing_proxy_json(*args, **kwargs):
        raise RuntimeError("upstream unreachable")

    monkeypatch.setattr(service_module, "proxy_json", failing_proxy_json)

    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})
    submission = svc.submit_work(
        "student-1", assignment.id, "a.pdf", b"bytes", str(tmp_path)
    )

    graded = await svc.request_ai_grade(
        "teacher-1", assignment.id, submission.id, "test-model"
    )

    assert graded.ai_score is None
    assert graded.status == "ai_grade_failed"


async def test_request_ai_grade_rejects_when_no_extracted_text(
    db, tmp_path, monkeypatch
):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: None)

    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})
    submission = svc.submit_work(
        "student-1", assignment.id, "a.pdf", b"bytes", str(tmp_path)
    )

    with pytest.raises(ValidationError):
        await svc.request_ai_grade(
            "teacher-1", assignment.id, submission.id, "test-model"
        )


async def test_request_ai_grade_requires_assignment_ownership(
    db, tmp_path, monkeypatch
):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")

    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})
    submission = svc.submit_work(
        "student-1", assignment.id, "a.pdf", b"bytes", str(tmp_path)
    )

    with pytest.raises(AuthorizationError):
        await svc.request_ai_grade(
            "teacher-2", assignment.id, submission.id, "test-model"
        )


def test_finalize_grade_overwrites_with_teacher_values(db, tmp_path, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")

    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})
    submission = svc.submit_work(
        "student-1", assignment.id, "a.pdf", b"bytes", str(tmp_path)
    )

    finalized = svc.finalize_grade(
        "teacher-1", assignment.id, submission.id, 90, "Great job."
    )

    assert finalized.teacher_score == 90
    assert finalized.teacher_feedback == "Great job."
    assert finalized.status == "finalized"


def test_finalize_grade_requires_assignment_ownership(db, tmp_path, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")

    svc = AssignmentService(db)
    assignment = svc.create_assignment("teacher-1", {"title": "A", "rubric": "r"})
    submission = svc.submit_work(
        "student-1", assignment.id, "a.pdf", b"bytes", str(tmp_path)
    )

    with pytest.raises(AuthorizationError):
        svc.finalize_grade("teacher-2", assignment.id, submission.id, 90, "Nope")


# ---------------------------------------------------------------------------
# Router-layer tests.
#
# Written before gateway/http/routers/assignments.py exists (TDD red step).
# Exercised through the real HTTP client, matching the pattern used across
# the rest of this test suite (see tests/test_chats.py).
# ---------------------------------------------------------------------------


def _token(client, role, email):
    # The very first signup in a fresh DB always becomes role="admin" (first-user
    # admin behavior, preserved intentionally — see AGENTS.md). Seed a throwaway
    # admin first so the signup below actually gets the role we ask for.
    if client.get("/auths/user-count").json()["count"] == 0:
        client.post(
            "/auths/signup",
            json={"email": "seed-admin@t.com", "name": "seed", "password": "pass1234!"},
        )
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": role, "password": "pass1234!", "role": role},
    )
    return r.json()["token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _create_assignment(client, teacher_token, **overrides):
    body = {"title": "Fractions Practice Set", "rubric": "Correctness + working shown."}
    body.update(overrides)
    r = client.post("/api/v1/assignments", json=body, headers=_auth(teacher_token))
    return r.json()


def test_create_assignment_as_teacher_succeeds(client):
    token = _token(client, "teacher", "teacher1@t.com")

    r = client.post(
        "/api/v1/assignments",
        json={
            "title": "Fractions Practice Set",
            "rubric": "Correctness + working shown.",
        },
        headers=_auth(token),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Fractions Practice Set"
    assert data["rubric"] == "Correctness + working shown."


def test_create_assignment_as_student_forbidden(client):
    token = _token(client, "student", "student1@t.com")

    r = client.post(
        "/api/v1/assignments",
        json={"title": "Fractions Practice Set", "rubric": "r"},
        headers=_auth(token),
    )

    assert r.status_code == 403


def test_get_assignment_not_found(client):
    token = _token(client, "teacher", "teacher2@t.com")

    r = client.get("/api/v1/assignments/missing-id", headers=_auth(token))

    assert r.status_code == 404
    assert (
        r.json()["detail"] != "Not Found"
    )  # must be our own message, not FastAPI's default


def test_list_assignments_endpoint_scoped_to_teacher(client):
    token1 = _token(client, "teacher", "teacher3@t.com")
    token2 = _token(client, "teacher", "teacher4@t.com")
    _create_assignment(client, token1, title="A1")
    _create_assignment(client, token2, title="A2")

    r = client.get("/api/v1/assignments", headers=_auth(token1))

    assert r.status_code == 200
    titles = {a["title"] for a in r.json()}
    assert titles == {"A1"}


def test_submit_work_as_student_succeeds(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")

    teacher_token = _token(client, "teacher", "teacher5@t.com")
    student_token = _token(client, "student", "student2@t.com")
    assignment = _create_assignment(client, teacher_token)

    r = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("answers.pdf", b"fake pdf bytes", "application/pdf")},
        headers=_auth(student_token),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "answers.pdf"
    assert data["status"] == "submitted"
    assert data["extracted_text"] == "7/8"


def test_submit_work_missing_assignment_returns_404(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")
    student_token = _token(client, "student", "student3@t.com")

    r = client.post(
        "/api/v1/assignments/missing-id/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    )

    assert r.status_code == 404
    assert (
        r.json()["detail"] != "Not Found"
    )  # must be our own message, not FastAPI's default


def test_get_submission_forbidden_for_other_student(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")

    teacher_token = _token(client, "teacher", "teacher6@t.com")
    student1_token = _token(client, "student", "student4@t.com")
    student2_token = _token(client, "student", "student5@t.com")
    assignment = _create_assignment(client, teacher_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student1_token),
    ).json()

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}",
        headers=_auth(student2_token),
    )

    assert r.status_code == 403


def test_get_submission_allowed_for_owning_teacher(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")

    teacher_token = _token(client, "teacher", "teacher7@t.com")
    student_token = _token(client, "student", "student6@t.com")
    assignment = _create_assignment(client, teacher_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    ).json()

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}",
        headers=_auth(teacher_token),
    )

    assert r.status_code == 200
    assert r.json()["id"] == submission["id"]
    assert "ai_score" in r.json()  # teacher sees the full shape, including AI fields


def test_get_submission_hides_ai_fields_from_owning_student(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")
    _mock_provider_resolution(monkeypatch, service_module)

    async def fake_proxy_json(url, key, method, path, body=None):
        return {
            "choices": [
                {
                    "message": {
                        "content": jsonlib.dumps({"score": 78, "feedback": "Nice."})
                    }
                }
            ]
        }

    monkeypatch.setattr(service_module, "proxy_json", fake_proxy_json)

    teacher_token = _token(client, "teacher", "teacher19@t.com")
    student_token = _token(client, "student", "student16@t.com")
    assignment = _create_assignment(client, teacher_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    ).json()
    client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}/ai-grade",
        json={"model": "test-model"},
        headers=_auth(teacher_token),
    )

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}",
        headers=_auth(student_token),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["id"] == submission["id"]
    assert "ai_score" not in data
    assert "ai_feedback" not in data
    assert "extracted_text" not in data


def test_list_submissions_forbidden_for_non_owning_teacher(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "text")

    teacher1_token = _token(client, "teacher", "teacher8@t.com")
    teacher2_token = _token(client, "teacher", "teacher9@t.com")
    assignment = _create_assignment(client, teacher1_token)

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        headers=_auth(teacher2_token),
    )

    assert r.status_code == 403


def test_ai_grade_endpoint_success(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")
    _mock_provider_resolution(monkeypatch, service_module)

    async def fake_proxy_json(url, key, method, path, body=None):
        return {
            "choices": [
                {
                    "message": {
                        "content": jsonlib.dumps(
                            {"score": 78, "feedback": "Good work overall."}
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr(service_module, "proxy_json", fake_proxy_json)

    teacher_token = _token(client, "teacher", "teacher10@t.com")
    student_token = _token(client, "student", "student7@t.com")
    assignment = _create_assignment(client, teacher_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    ).json()

    r = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}/ai-grade",
        json={"model": "test-model"},
        headers=_auth(teacher_token),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["ai_score"] == 78
    assert data["ai_feedback"] == "Good work overall."


def test_ai_grade_forbidden_for_non_owning_teacher(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")

    teacher1_token = _token(client, "teacher", "teacher11@t.com")
    teacher2_token = _token(client, "teacher", "teacher12@t.com")
    student_token = _token(client, "student", "student8@t.com")
    assignment = _create_assignment(client, teacher1_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    ).json()

    r = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}/ai-grade",
        json={"model": "test-model"},
        headers=_auth(teacher2_token),
    )

    assert r.status_code == 403


def test_finalize_grade_endpoint_success(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")

    teacher_token = _token(client, "teacher", "teacher13@t.com")
    student_token = _token(client, "student", "student9@t.com")
    assignment = _create_assignment(client, teacher_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    ).json()

    r = client.put(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}/finalize",
        json={"score": 90, "feedback": "Great job."},
        headers=_auth(teacher_token),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["teacher_score"] == 90
    assert data["teacher_feedback"] == "Great job."
    assert data["status"] == "finalized"


def test_finalize_grade_validation_error_on_bad_payload(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")

    teacher_token = _token(client, "teacher", "teacher14@t.com")
    student_token = _token(client, "student", "student10@t.com")
    assignment = _create_assignment(client, teacher_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("a.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    ).json()

    r = client.put(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}/finalize",
        json={"feedback": "Missing the score field."},
        headers=_auth(teacher_token),
    )

    assert r.status_code == 422


def test_get_my_submission_returns_none_when_not_submitted(client):
    teacher_token = _token(client, "teacher", "teacher15@t.com")
    student_token = _token(client, "student", "student11@t.com")
    assignment = _create_assignment(client, teacher_token)

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions/mine",
        headers=_auth(student_token),
    )

    assert r.status_code == 200
    assert r.json() is None


def test_get_my_submission_returns_own_submission(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")

    teacher_token = _token(client, "teacher", "teacher16@t.com")
    student_token = _token(client, "student", "student12@t.com")
    assignment = _create_assignment(client, teacher_token)
    client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("answers.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    )

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions/mine",
        headers=_auth(student_token),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "answers.pdf"
    assert data["status"] == "submitted"


def test_get_my_submission_never_exposes_ai_fields(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")
    _mock_provider_resolution(monkeypatch, service_module)

    async def fake_proxy_json(url, key, method, path, body=None):
        return {
            "choices": [
                {
                    "message": {
                        "content": jsonlib.dumps({"score": 78, "feedback": "Nice."})
                    }
                }
            ]
        }

    monkeypatch.setattr(service_module, "proxy_json", fake_proxy_json)

    teacher_token = _token(client, "teacher", "teacher17@t.com")
    student_token = _token(client, "student", "student13@t.com")
    assignment = _create_assignment(client, teacher_token)
    submission = client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("answers.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    ).json()
    client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions/{submission['id']}/ai-grade",
        json={"model": "test-model"},
        headers=_auth(teacher_token),
    )

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions/mine",
        headers=_auth(student_token),
    )

    assert r.status_code == 200
    data = r.json()
    assert "ai_score" not in data
    assert "ai_feedback" not in data
    assert "extracted_text" not in data


def test_get_my_submission_does_not_leak_other_students_work(client, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")

    teacher_token = _token(client, "teacher", "teacher18@t.com")
    student1_token = _token(client, "student", "student14@t.com")
    student2_token = _token(client, "student", "student15@t.com")
    assignment = _create_assignment(client, teacher_token)
    client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("student1.pdf", b"bytes", "application/pdf")},
        headers=_auth(student1_token),
    )

    r = client.get(
        f"/api/v1/assignments/{assignment['id']}/submissions/mine",
        headers=_auth(student2_token),
    )

    assert r.status_code == 200
    assert r.json() is None


def test_delete_assignment_as_owning_teacher_succeeds(client):
    teacher_token = _token(client, "teacher", "teacher19@t.com")
    assignment = _create_assignment(client, teacher_token)

    r = client.delete(
        f"/api/v1/assignments/{assignment['id']}", headers=_auth(teacher_token)
    )

    assert r.status_code == 204
    follow_up = client.get(
        f"/api/v1/assignments/{assignment['id']}", headers=_auth(teacher_token)
    )
    assert follow_up.status_code == 404


def test_delete_assignment_cascades_submissions(client, db, monkeypatch):
    import learning.assignments.service as service_module

    monkeypatch.setattr(service_module, "extract_pdf_text", lambda contents: "7/8")

    teacher_token = _token(client, "teacher", "teacher20@t.com")
    student_token = _token(client, "student", "student16@t.com")
    assignment = _create_assignment(client, teacher_token)
    client.post(
        f"/api/v1/assignments/{assignment['id']}/submissions",
        files={"file": ("answers.pdf", b"bytes", "application/pdf")},
        headers=_auth(student_token),
    )

    r = client.delete(
        f"/api/v1/assignments/{assignment['id']}", headers=_auth(teacher_token)
    )

    assert r.status_code == 204
    remaining = _submission_repo(db).get_by_assignment(assignment["id"])
    assert remaining == []


def test_delete_assignment_as_student_forbidden(client):
    teacher_token = _token(client, "teacher", "teacher21@t.com")
    student_token = _token(client, "student", "student17@t.com")
    assignment = _create_assignment(client, teacher_token)

    r = client.delete(
        f"/api/v1/assignments/{assignment['id']}", headers=_auth(student_token)
    )

    assert r.status_code == 403


def test_delete_assignment_forbidden_for_non_owning_teacher(client):
    teacher1_token = _token(client, "teacher", "teacher22@t.com")
    teacher2_token = _token(client, "teacher", "teacher23@t.com")
    assignment = _create_assignment(client, teacher1_token)

    r = client.delete(
        f"/api/v1/assignments/{assignment['id']}", headers=_auth(teacher2_token)
    )

    assert r.status_code == 403


def test_delete_assignment_not_found(client):
    teacher_token = _token(client, "teacher", "teacher24@t.com")

    r = client.delete("/api/v1/assignments/missing-id", headers=_auth(teacher_token))

    assert r.status_code == 404
    assert r.json()["detail"] != "Not Found"

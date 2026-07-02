# tests/test_assignments.py
"""Repository-layer tests for the Assignments domain.

Written before learning/assignments/repository.py exists (TDD red step).
"""

from data.models import Assignment, Submission
from learning.assignments.repository import AssignmentRepository, SubmissionRepository


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
    assignment = assignments.create(id="a1", user_id="teacher-1", title="A1", rubric="r")

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
    assignment = assignments.create(id="a1", user_id="teacher-1", title="A1", rubric="r")
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
        id="s1", assignment_id=a1.id, user_id="student-1",
        filename="a.pdf", file_path="/x/a.pdf", status="submitted",
    )
    submissions.create(
        id="s2", assignment_id=a1.id, user_id="student-2",
        filename="b.pdf", file_path="/x/b.pdf", status="submitted",
    )
    submissions.create(
        id="s3", assignment_id=a2.id, user_id="student-1",
        filename="c.pdf", file_path="/x/c.pdf", status="submitted",
    )

    result = submissions.get_by_assignment(a1.id)

    assert {s.id for s in result} == {"s1", "s2"}


def test_get_submission_by_assignment_and_user(db):
    assignments = _assignment_repo(db)
    submissions = _submission_repo(db)
    a1 = assignments.create(id="a1", user_id="teacher-1", title="A1", rubric="r")
    submissions.create(
        id="s1", assignment_id=a1.id, user_id="student-1",
        filename="a.pdf", file_path="/x/a.pdf", status="submitted",
    )

    result = submissions.get_by_assignment_and_user(a1.id, "student-1")
    assert result is not None
    assert result.id == "s1"

    missing = submissions.get_by_assignment_and_user(a1.id, "student-2")
    assert missing is None

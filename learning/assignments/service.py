"""Assignment service."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from common.exceptions import NotFoundError, AuthorizationError
from data.models.assignment import Assignment, Submission
from data.models.classroom import Enrollment
from learning.assignments.repository import AssignmentRepository, SubmissionRepository
from learning.classrooms.repository import ClassroomRepository
from data.models.classroom import Classroom


class AssignmentsService:

    def __init__(self, session: Session):
        self.repo = AssignmentRepository(session, Assignment)
        self.sub_repo = SubmissionRepository(session, Submission)
        self.classroom_repo = ClassroomRepository(session, Classroom)

    def create(self, teacher_id: str, classroom_id: str, title: str,
               instructions: str = None, due_date: datetime = None,
               attachment_url: str = None, max_score: int = 20) -> Assignment:
        classroom = self.classroom_repo.get_by_id(classroom_id)
        if not classroom:
            raise NotFoundError("Classroom", classroom_id)
        if classroom.teacher_id != teacher_id:
            raise AuthorizationError("Not your classroom")
        return self.repo.create(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            teacher_id=teacher_id,
            title=title,
            instructions=instructions,
            due_date=due_date,
            attachment_url=attachment_url,
            max_score=max_score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def get(self, assignment_id: str) -> Assignment:
        a = self.repo.get_by_id(assignment_id)
        if not a:
            raise NotFoundError("Assignment", assignment_id)
        return a

    def get_and_check_owner(self, assignment_id: str, teacher_id: str) -> Assignment:
        a = self.get(assignment_id)
        if a.teacher_id != teacher_id:
            raise AuthorizationError("Not your assignment")
        return a

    def list_for_teacher(self, teacher_id: str) -> List[Assignment]:
        return self.repo.get_by_teacher(teacher_id)

    def list_for_student(self, student_id: str) -> List[Assignment]:
        enrollments = self.classroom_repo.get_student_classrooms(student_id)
        classroom_ids = [e.classroom_id for e in enrollments]
        return self.repo.get_by_classrooms(classroom_ids)

    def submit(self, assignment_id: str, student_id: str,
               content: str = None, attachment_url: str = None) -> Submission:
        assignment = self.get(assignment_id)
        # Check student is enrolled
        enrollment = self.classroom_repo.get_enrollment(assignment.classroom_id, student_id)
        if not enrollment:
            raise AuthorizationError("Not enrolled in this classroom")

        existing = self.sub_repo.get_by_student_and_assignment(student_id, assignment_id)
        now = datetime.utcnow()
        is_late = now > assignment.due_date

        if existing:
            return self.sub_repo.update(
                existing.id,
                content=content,
                attachment_url=attachment_url,
                submitted_at=now,
                status="late" if is_late else "submitted",
            )
        return self.sub_repo.create(
            id=str(uuid.uuid4()),
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            attachment_url=attachment_url,
            submitted_at=now,
            status="late" if is_late else "submitted",
        )

    def grade(self, assignment_id: str, submission_id: str, teacher_id: str,
              score: int, feedback: str = None) -> Submission:
        self.get_and_check_owner(assignment_id, teacher_id)
        sub = self.sub_repo.get_by_id(submission_id)
        if not sub or sub.assignment_id != assignment_id:
            raise NotFoundError("Submission", submission_id)
        return self.sub_repo.update(
            submission_id,
            score=score,
            feedback=feedback,
            graded_at=datetime.utcnow(),
            status="returned",
        )

    def get_submissions(self, assignment_id: str, teacher_id: str) -> List[Submission]:
        self.get_and_check_owner(assignment_id, teacher_id)
        return self.sub_repo.get_by_assignment(assignment_id)

    def get_student_submission(self, assignment_id: str, student_id: str) -> Optional[Submission]:
        return self.sub_repo.get_by_student_and_assignment(student_id, assignment_id)

    def get_student_submissions(self, student_id: str) -> List[Submission]:
        return self.sub_repo.get_by_student(student_id)

    def update(self, assignment_id: str, teacher_id: str, **kwargs) -> Assignment:
        a = self.get_and_check_owner(assignment_id, teacher_id)
        allowed = {"title", "instructions", "due_date", "attachment_url", "max_score"}
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        fields["updated_at"] = datetime.utcnow()
        return self.repo.update(a.id, **fields)

    def delete(self, assignment_id: str, teacher_id: str) -> None:
        a = self.get_and_check_owner(assignment_id, teacher_id)
        self.sub_repo.delete_by_assignment(a.id)
        self.repo.delete(a.id)

    def cancel_submission(self, assignment_id: str, student_id: str) -> bool:
        sub = self.sub_repo.get_by_student_and_assignment(student_id, assignment_id)
        if not sub:
            raise NotFoundError("Submission", assignment_id)
        if sub.status == "returned":
            raise AuthorizationError("Cannot cancel a graded submission")
        return self.sub_repo.delete_by_student_and_assignment(student_id, assignment_id)

    def get_status_tracker(self, assignment_id: str, teacher_id: str) -> List[dict]:
        """Returns per-student status: not_submitted | submitted | late | missed."""
        assignment = self.get_and_check_owner(assignment_id, teacher_id)
        enrollments = self.classroom_repo.get_students(assignment.classroom_id)
        submissions = {s.student_id: s for s in self.sub_repo.get_by_assignment(assignment_id)}
        now = datetime.utcnow()
        result = []
        for e in enrollments:
            sub = submissions.get(e.student_id)
            if sub:
                status = sub.status  # submitted | late | returned
            elif now > assignment.due_date:
                status = "missed"
            else:
                status = "not_submitted"
            result.append({"student_id": e.student_id, "submission": sub, "status": status})
        return result

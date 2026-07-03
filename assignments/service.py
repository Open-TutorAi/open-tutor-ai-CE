"""Assignments service — business logic + authorization (no ORM directly).

Teachers author assignments in a class they own and grade submissions; enrolled
students submit once per assignment. Per-student status (pending/submitted/late/
missing/graded) is a computed read model, never stored.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from accounts.users.service import AccountService as IdentityService
from assignments.repository import AssignmentRepository, SubmissionRepository
from classrooms.repository import ClassroomRepository, EnrollmentRepository
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from content.files.service import FilesService
from data.models import Assignment, Classroom, Enrollment, ExamSession, Submission
from exams.repository import ExamSessionRepository


class AssignmentsService:
    """Service for assignment + submission operations."""

    def __init__(self, session: Session):
        self.session = session
        self.assignments = AssignmentRepository(session, Assignment)
        self.submissions = SubmissionRepository(session, Submission)
        self.classrooms = ClassroomRepository(session, Classroom)
        self.enrollments = EnrollmentRepository(session, Enrollment)
        self.identity = IdentityService(session)
        self.files = FilesService(session)
        self.exam_sessions = ExamSessionRepository(session, ExamSession)

    # ── internal helpers ─────────────────────────────────────────────────────

    def _owned_class(self, classroom_id: str, teacher_id: str) -> Classroom:
        room = self.classrooms.get_by_id(classroom_id)
        if not room:
            raise NotFoundError("Classroom", classroom_id)
        if room.teacher_id != teacher_id:
            raise AuthorizationError("Not authorized for this classroom")
        return room

    def _validate_attachment(self, attachment_id: Optional[str], user_id: str) -> None:
        """A user may only attach a file they own (uploaded). Raises 404/403 otherwise."""
        if attachment_id:
            self.files.require_owned(attachment_id, user_id)

    def _with_attachment(self, d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Add `attachment_name` next to an `attachment_id` in a serialized dict."""
        if d and d.get("attachment_id"):
            rec = self.files.get(d["attachment_id"])
            d["attachment_name"] = rec.filename if rec else None
        return d

    def _owned_assignment(self, assignment_id: str, teacher_id: str) -> Assignment:
        assignment = self.assignments.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", assignment_id)
        self._owned_class(assignment.classroom_id, teacher_id)
        return assignment

    @staticmethod
    def _parse_due(value: Optional[str]) -> Optional[datetime]:
        if value is None or value == "":
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except ValueError:
            raise ValidationError("due_date must be an ISO 8601 datetime")

    @staticmethod
    def _student_status(
        assignment: Assignment,
        submission: Optional[Submission],
        exam_terminated: bool = False,
    ) -> str:
        """Compute a student's standing on an assignment (read model)."""
        if submission is not None and submission.grade is not None:
            return "graded"
        if exam_terminated:
            # The proctoring policy ended the exam — even if the auto-submitted
            # answer was empty (no submission row), the exam is over for this
            # student. Surfaced distinctly so nobody mistakes it for a normal
            # hand-in, and so the UI never re-offers the exam gate.
            return "auto_submitted"
        if submission is not None:
            return "late" if submission.is_late else "submitted"
        if assignment.due_date and assignment.due_date < datetime.utcnow():
            return "missing"
        return "pending"

    def _exam_terminated(self, assignment_id: str, student_id: str) -> bool:
        sess = self.exam_sessions.get(assignment_id, student_id)
        return sess is not None and sess.status == "terminated"

    # ── teacher: authoring ───────────────────────────────────────────────────

    def create(
        self, classroom_id: str, teacher_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        self._owned_class(classroom_id, teacher_id)
        title = data.get("title")
        if not (isinstance(title, str) and title.strip()):
            raise ValidationError("title is required")
        due_date = self._parse_due(data.get("due_date"))
        attachment_id = data.get("attachment_id") or None
        self._validate_attachment(attachment_id, teacher_id)
        assignment = self.assignments.create(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            created_by=teacher_id,
            title=title.strip(),
            instructions=(data.get("instructions") or None),
            attachment_id=attachment_id,
            due_date=due_date,
            created_at=datetime.utcnow(),
        )
        return self._assignment_summary(assignment)

    def _assignment_summary(self, assignment: Assignment) -> Dict[str, Any]:
        """Assignment + roster-wide submission tallies (teacher view)."""
        roster = self.enrollments.list_active(assignment.classroom_id)
        subs = {
            s.student_id: s for s in self.submissions.list_for_assignment(assignment.id)
        }
        submitted = sum(1 for sid in [e.student_id for e in roster] if sid in subs)
        graded = sum(
            1
            for e in roster
            if e.student_id in subs and subs[e.student_id].grade is not None
        )
        return self._with_attachment(
            {
                **assignment.to_dict(),
                "student_count": len(roster),
                "submitted_count": submitted,
                "graded_count": graded,
            }
        )

    def list_for_class(
        self, classroom_id: str, teacher_id: str
    ) -> List[Dict[str, Any]]:
        self._owned_class(classroom_id, teacher_id)
        return [
            self._assignment_summary(a)
            for a in self.assignments.list_for_classroom(classroom_id)
        ]

    def get_assignment(self, assignment_id: str, teacher_id: str) -> Dict[str, Any]:
        """One assignment with a per-student submission breakdown over the roster."""
        assignment = self._owned_assignment(assignment_id, teacher_id)
        subs = {
            s.student_id: s for s in self.submissions.list_for_assignment(assignment_id)
        }
        rows: List[Dict[str, Any]] = []
        for enrollment in self.enrollments.list_active(assignment.classroom_id):
            student = self.identity.get_user(enrollment.student_id)
            submission = subs.get(enrollment.student_id)
            rows.append(
                {
                    "student_id": enrollment.student_id,
                    "name": student.name if student else None,
                    "email": student.email if student else None,
                    "status": self._student_status(
                        assignment,
                        submission,
                        self._exam_terminated(assignment.id, enrollment.student_id),
                    ),
                    "submission": self._with_attachment(
                        submission.to_dict() if submission else None
                    ),
                }
            )
        return {**self._assignment_summary(assignment), "submissions": rows}

    def delete(self, assignment_id: str, teacher_id: str) -> None:
        self._owned_assignment(assignment_id, teacher_id)
        self.assignments.delete(assignment_id)

    # ── teacher: grading ─────────────────────────────────────────────────────

    def grade(
        self,
        assignment_id: str,
        teacher_id: str,
        student_id: str,
        grade: Optional[float],
        feedback: Optional[str],
    ) -> Dict[str, Any]:
        self._owned_assignment(assignment_id, teacher_id)
        submission = self.submissions.get(assignment_id, student_id)
        if not submission:
            if self._exam_terminated(assignment_id, student_id):
                # A terminated exam may have recovered no answer (the student
                # wrote nothing before it ended). The teacher still grades the
                # attempt — record the grade on an empty submission instead of
                # refusing.
                submission = self.submissions.create(
                    id=str(uuid.uuid4()),
                    assignment_id=assignment_id,
                    student_id=student_id,
                    content=None,
                    attachment_id=None,
                    submitted_at=datetime.utcnow(),
                    is_late=False,
                    status="submitted",
                )
            else:
                raise NotFoundError("Submission", student_id)
        submission.grade = grade
        submission.feedback = feedback or None
        submission.graded_at = datetime.utcnow()
        submission.status = "graded"
        self.session.commit()
        self.session.refresh(submission)
        return self._with_attachment(submission.to_dict())

    # ── student: submission ──────────────────────────────────────────────────

    def list_for_student(self, student_id: str) -> List[Dict[str, Any]]:
        """Every assignment across the student's enrolled classes, with their status."""
        classroom_ids = [
            e.classroom_id for e in self.enrollments.list_for_student(student_id)
        ]
        rooms = {cid: self.classrooms.get_by_id(cid) for cid in set(classroom_ids)}
        out: List[Dict[str, Any]] = []
        for assignment in self.assignments.list_for_classrooms(classroom_ids):
            submission = self.submissions.get(assignment.id, student_id)
            room = rooms.get(assignment.classroom_id)
            out.append(
                self._with_attachment(
                    {
                        **assignment.to_dict(),
                        "class_name": room.name if room else None,
                        "status": self._student_status(
                            assignment,
                            submission,
                            self._exam_terminated(assignment.id, student_id),
                        ),
                        "submission": self._with_attachment(
                            submission.to_dict() if submission else None
                        ),
                    }
                )
            )
        return out

    def submit(
        self, assignment_id: str, student_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or replace a student's submission (must be enrolled in the class)."""
        assignment = self.assignments.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", assignment_id)
        if not self.enrollments.get(assignment.classroom_id, student_id):
            raise AuthorizationError("Not enrolled in this class")

        content = data.get("content")
        attachment_id = data.get("attachment_id") or None
        if not (isinstance(content, str) and content.strip()) and not attachment_id:
            raise ValidationError("content or an attachment is required")
        self._validate_attachment(attachment_id, student_id)

        now = datetime.utcnow()
        is_late = bool(assignment.due_date and now > assignment.due_date)
        existing = self.submissions.get(assignment_id, student_id)

        # Proctored exams accept a single hand-in: the one the exam shell sends when
        # the session ends. Once the exam is over and work exists, replacing it would
        # defeat the proctoring (polish-at-home-and-resubmit).
        sess = self.exam_sessions.get(assignment_id, student_id)
        if sess is not None and sess.status != "in_progress" and existing:
            raise ValidationError("This exam has ended — answers cannot be replaced")
        if existing:
            existing.content = content
            existing.attachment_id = attachment_id
            existing.submitted_at = now
            existing.is_late = is_late
            # Re-submission clears any prior grade — the teacher grades the new work.
            existing.grade = None
            existing.feedback = None
            existing.graded_at = None
            existing.status = "submitted"
            self.session.commit()
            self.session.refresh(existing)
            return self._with_attachment(existing.to_dict())

        submission = self.submissions.create(
            id=str(uuid.uuid4()),
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            attachment_id=attachment_id,
            submitted_at=now,
            is_late=is_late,
            status="submitted",
        )
        return self._with_attachment(submission.to_dict())

    def get_my_submission(
        self, assignment_id: str, student_id: str
    ) -> Optional[Dict[str, Any]]:
        submission = self.submissions.get(assignment_id, student_id)
        return self._with_attachment(submission.to_dict()) if submission else None

    # ── attachments: scoped download (authorize via class membership) ─────────

    def read_assignment_attachment(
        self, assignment_id: str, user_id: str
    ) -> tuple[bytes, str, str]:
        """Bytes of an assignment's attachment, readable by the owning teacher OR an
        enrolled student. Returns (data, content_type, filename)."""
        assignment = self.assignments.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", assignment_id)
        room = self.classrooms.get_by_id(assignment.classroom_id)
        is_teacher = room and room.teacher_id == user_id
        is_student = self.enrollments.get(assignment.classroom_id, user_id) is not None
        if not (is_teacher or is_student):
            raise AuthorizationError("Not authorized for this assignment")
        if not assignment.attachment_id:
            raise NotFoundError("Attachment", assignment_id)
        return self._read_file(assignment.attachment_id)

    def read_submission_attachment(
        self, assignment_id: str, student_id: str, requester_id: str
    ) -> tuple[bytes, str, str]:
        """Bytes of a student's submission attachment, readable by that student OR the
        owning teacher. Returns (data, content_type, filename)."""
        assignment = self.assignments.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", assignment_id)
        room = self.classrooms.get_by_id(assignment.classroom_id)
        is_teacher = room and room.teacher_id == requester_id
        if not (requester_id == student_id or is_teacher):
            raise AuthorizationError("Not authorized for this submission")
        submission = self.submissions.get(assignment_id, student_id)
        if not submission or not submission.attachment_id:
            raise NotFoundError("Attachment", assignment_id)
        return self._read_file(submission.attachment_id)

    def _read_file(self, file_id: str) -> tuple[bytes, str, str]:
        data, content_type = self.files.read_bytes(file_id)
        rec = self.files.get(file_id)
        return data, content_type, (rec.filename if rec else "attachment")

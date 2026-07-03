"""Exams service — business logic + authorization (Epic E10).

A proctored exam is an assignment with an `ExamConfig`. The teacher configures it and
watches a live proctoring view; the student runs one `ExamSession`, and each rule break
is an `ExamViolation`. Authorization reuses the assignments/classrooms data (teacher must
own the class; student must be enrolled). Realtime delivery (emit) is the router's job.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from accounts.users.service import AccountService as IdentityService
from assignments.repository import AssignmentRepository
from classrooms.repository import ClassroomRepository, EnrollmentRepository
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import (
    Assignment,
    Classroom,
    Enrollment,
    ExamConfig,
    ExamSession,
    ExamViolation,
)
from exams.repository import (
    ExamConfigRepository,
    ExamSessionRepository,
    ExamViolationRepository,
)

# Warnings allowed before the exam is auto-submitted (hard cap).
MAX_WARNINGS = 3
# Seconds the student may stay away after each warning before auto-submit (1st/2nd/3rd).
GRACE_SCHEDULE = (60, 30, 10)


class ExamsService:
    """Service for exam configuration, sessions and proctoring."""

    def __init__(self, session: Session):
        self.session = session
        self.assignments = AssignmentRepository(session, Assignment)
        self.classrooms = ClassroomRepository(session, Classroom)
        self.enrollments = EnrollmentRepository(session, Enrollment)
        self.configs = ExamConfigRepository(session, ExamConfig)
        self.sessions = ExamSessionRepository(session, ExamSession)
        self.violations = ExamViolationRepository(session, ExamViolation)
        self.identity = IdentityService(session)

    # ── authz helpers ────────────────────────────────────────────────────────

    def _assignment(self, assignment_id: str) -> Assignment:
        a = self.assignments.get_by_id(assignment_id)
        if not a:
            raise NotFoundError("Assignment", assignment_id)
        return a

    def _owned_assignment(self, assignment_id: str, teacher_id: str) -> Assignment:
        a = self._assignment(assignment_id)
        room = self.classrooms.get_by_id(a.classroom_id)
        if not room or room.teacher_id != teacher_id:
            raise AuthorizationError("Not authorized for this assignment")
        return a

    def _enrolled_assignment(self, assignment_id: str, student_id: str) -> Assignment:
        a = self._assignment(assignment_id)
        if not self.enrollments.get(a.classroom_id, student_id):
            raise AuthorizationError("Not enrolled in this class")
        return a

    # ── teacher: configuration ───────────────────────────────────────────────

    def configure_exam(
        self, assignment_id: str, teacher_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mark an assignment as a proctored exam (upsert its config).

        Policy is fixed: the exam is auto-submitted after a capped number of warnings.
        """
        self._owned_assignment(assignment_id, teacher_id)

        on_violation = "auto_submit"  # the only supported policy
        time_limit = self._positive_or_none(
            data.get("time_limit_minutes"), "time_limit_minutes"
        )
        # The N-th warning ends the exam: 1..MAX_WARNINGS, default MAX_WARNINGS.
        max_violations = (
            self._positive_or_none(data.get("max_violations"), "max_violations")
            or MAX_WARNINGS
        )
        if max_violations > MAX_WARNINGS:
            raise ValidationError(f"max_violations cannot exceed {MAX_WARNINGS}")
        require_fullscreen = bool(data.get("require_fullscreen", True))

        cfg = self.configs.get_for_assignment(assignment_id)
        if cfg:
            cfg.time_limit_minutes = time_limit
            cfg.max_violations = max_violations
            cfg.on_violation = on_violation
            cfg.require_fullscreen = require_fullscreen
            self.session.commit()
            self.session.refresh(cfg)
        else:
            cfg = self.configs.create(
                id=str(uuid.uuid4()),
                assignment_id=assignment_id,
                time_limit_minutes=time_limit,
                max_violations=max_violations,
                on_violation=on_violation,
                require_fullscreen=require_fullscreen,
                created_at=datetime.utcnow(),
            )
        return cfg.to_dict()

    def unset_exam(self, assignment_id: str, teacher_id: str) -> None:
        """Turn an exam back into an ordinary assignment (removes config + sessions)."""
        self._owned_assignment(assignment_id, teacher_id)
        cfg = self.configs.get_for_assignment(assignment_id)
        if cfg:
            self.configs.delete(cfg.id)

    @staticmethod
    def _positive_or_none(value: Any, field: str) -> Optional[int]:
        if value in (None, "", 0):
            return None
        try:
            n = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field} must be a whole number")
        if n <= 0:
            raise ValidationError(f"{field} must be positive")
        return n

    # ── shared read ──────────────────────────────────────────────────────────

    def get_exam(self, assignment_id: str, user_id: str) -> Dict[str, Any]:
        """Exam config (or null) for the owning teacher or an enrolled student, plus
        the caller's own session if they are a student."""
        a = self._assignment(assignment_id)
        room = self.classrooms.get_by_id(a.classroom_id)
        is_teacher = room and room.teacher_id == user_id
        is_student = self.enrollments.get(a.classroom_id, user_id) is not None
        if not (is_teacher or is_student):
            raise AuthorizationError("Not authorized for this assignment")
        cfg = self.configs.get_for_assignment(assignment_id)
        mine = None if is_teacher else self.sessions.get(assignment_id, user_id)
        return {
            "is_exam": cfg is not None,
            "config": cfg.to_dict() if cfg else None,
            "session": mine.to_dict() if mine else None,
        }

    # ── student: session lifecycle ───────────────────────────────────────────

    def start_session(self, assignment_id: str, student_id: str) -> Dict[str, Any]:
        """Begin (or resume) the student's exam attempt.

        One attempt per student: an in-progress session resumes, but a finished one
        (submitted or terminated) can never be restarted.
        """
        self._enrolled_assignment(assignment_id, student_id)
        cfg = self.configs.get_for_assignment(assignment_id)
        if not cfg:
            raise ValidationError("This assignment is not an exam")
        sess = self.sessions.get(assignment_id, student_id)
        if sess and sess.status != "in_progress":
            raise ValidationError("This exam has ended and cannot be retaken")
        if not sess:
            sess = self.sessions.create(
                id=str(uuid.uuid4()),
                assignment_id=assignment_id,
                student_id=student_id,
                status="in_progress",
                started_at=datetime.utcnow(),
                violation_count=0,
            )
        return {"config": cfg.to_dict(), "session": sess.to_dict()}

    def report_violation(
        self, assignment_id: str, student_id: str, vtype: str
    ) -> Dict[str, Any]:
        """Record a proctoring event and apply the policy.

        `max_violations` = N means the exam ends on the N-th warning. Warnings
        1..N-1 are *graced*: the student has `grace_seconds` (60 → 30 → 10) to
        return before the exam auto-submits (the client enforces the countdown via
        `terminate_session`). The N-th warning terminates immediately. Returns the
        action (warn | terminated), the grace window, and the teacher to notify live.
        """
        self._enrolled_assignment(assignment_id, student_id)
        cfg = self.configs.get_for_assignment(assignment_id)
        sess = self.sessions.get(assignment_id, student_id)
        if not cfg or not sess:
            raise NotFoundError("ExamSession", assignment_id)
        if not (isinstance(vtype, str) and vtype.strip()):
            raise ValidationError("violation type is required")

        action = "warn"
        grace_seconds = 0
        if sess.status == "in_progress":
            self.violations.create(
                commit=False,
                id=str(uuid.uuid4()),
                session_id=sess.id,
                student_id=student_id,
                type=vtype.strip()[:40],
                created_at=datetime.utcnow(),
            )
            sess.violation_count += 1
            n = sess.violation_count
            limit = cfg.max_violations or MAX_WARNINGS
            if n >= limit:
                # The N-th warning exhausts the allowance and ends the exam now.
                sess.status = "terminated"
                sess.submitted_at = datetime.utcnow()
                action = "terminated"
            else:
                # Graced warning: shrinking time-to-return before auto-submit.
                grace_seconds = GRACE_SCHEDULE[min(n, len(GRACE_SCHEDULE)) - 1]
            self.session.commit()
            self.session.refresh(sess)

        room = self.classrooms.get_by_id(self._assignment(assignment_id).classroom_id)
        target = {
            "teacher_id": room.teacher_id if room else None,
            "assignment_id": assignment_id,
            "student_id": student_id,
            "type": vtype,
            "violation_count": sess.violation_count,
            "status": sess.status,
        }
        return {
            "action": action,
            "grace_seconds": grace_seconds,
            "session": sess.to_dict(),
            "target": target,
        }

    def terminate_session(
        self, assignment_id: str, student_id: str, reason: str
    ) -> Dict[str, Any]:
        """End an in-progress exam now (grace/time expired). Records the reason and
        returns the teacher to notify live. No-op if already finished."""
        self._enrolled_assignment(assignment_id, student_id)
        sess = self.sessions.get(assignment_id, student_id)
        if not sess:
            raise NotFoundError("ExamSession", assignment_id)
        reason = (reason or "timeout").strip()[:40]
        if sess.status == "in_progress":
            self.violations.create(
                commit=False,
                id=str(uuid.uuid4()),
                session_id=sess.id,
                student_id=student_id,
                type=reason,
                created_at=datetime.utcnow(),
            )
            sess.status = "terminated"
            sess.submitted_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(sess)

        room = self.classrooms.get_by_id(self._assignment(assignment_id).classroom_id)
        target = {
            "teacher_id": room.teacher_id if room else None,
            "assignment_id": assignment_id,
            "student_id": student_id,
            "type": reason,
            "violation_count": sess.violation_count,
            "status": sess.status,
        }
        return {"session": sess.to_dict(), "target": target}

    def submit_session(self, assignment_id: str, student_id: str) -> Dict[str, Any]:
        """Mark the student's exam session submitted (called alongside the real submit)."""
        self._enrolled_assignment(assignment_id, student_id)
        sess = self.sessions.get(assignment_id, student_id)
        if not sess:
            raise NotFoundError("ExamSession", assignment_id)
        if sess.status == "in_progress":
            sess.status = "submitted"
            sess.submitted_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(sess)
        return sess.to_dict()

    # ── teacher: live proctoring ─────────────────────────────────────────────

    def get_proctoring(
        self, assignment_id: str, teacher_id: str
    ) -> List[Dict[str, Any]]:
        """Per-student proctoring rows (session status + violations), newest first."""
        a = self._owned_assignment(assignment_id, teacher_id)
        rows: List[Dict[str, Any]] = []
        sessions = {
            s.student_id: s for s in self.sessions.list_for_assignment(assignment_id)
        }
        for enrollment in self.enrollments.list_active(a.classroom_id):
            student = self.identity.get_user(enrollment.student_id)
            sess = sessions.get(enrollment.student_id)
            rows.append(
                {
                    "student_id": enrollment.student_id,
                    "name": student.name if student else None,
                    "email": student.email if student else None,
                    "status": sess.status if sess else "not_started",
                    "violation_count": sess.violation_count if sess else 0,
                    "violations": (
                        [v.to_dict() for v in self.violations.list_for_session(sess.id)]
                        if sess
                        else []
                    ),
                }
            )
        return rows

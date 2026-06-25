"""Classroom repositories — data access only (SQLAlchemy, no business logic)."""

from typing import List, Optional

from data.models import (
    Classroom,
    Enrollment,
    Invitation,
    MonitorAwayEvent,
    MonitorState,
)
from data.repositories import BaseRepository


class ClassroomRepository(BaseRepository[Classroom]):
    """Data access for classrooms."""

    def get_by_teacher(self, teacher_id: str) -> List[Classroom]:
        return (
            self.session.query(Classroom)
            .filter(Classroom.teacher_id == teacher_id)
            .order_by(Classroom.created_at.desc())
            .all()
        )

    def count_active_students(self, classroom_id: str) -> int:
        return (
            self.session.query(Enrollment)
            .filter(
                Enrollment.classroom_id == classroom_id,
                Enrollment.status == "active",
            )
            .count()
        )


class EnrollmentRepository(BaseRepository[Enrollment]):
    """Data access for roster membership."""

    def get(self, classroom_id: str, student_id: str) -> Optional[Enrollment]:
        return (
            self.session.query(Enrollment)
            .filter(
                Enrollment.classroom_id == classroom_id,
                Enrollment.student_id == student_id,
            )
            .first()
        )

    def list_active(self, classroom_id: str) -> List[Enrollment]:
        return (
            self.session.query(Enrollment)
            .filter(
                Enrollment.classroom_id == classroom_id,
                Enrollment.status == "active",
            )
            .order_by(Enrollment.enrolled_at.asc())
            .all()
        )

    def list_for_student(self, student_id: str) -> List[Enrollment]:
        """Every active enrolment for a student (across all their classes)."""
        return (
            self.session.query(Enrollment)
            .filter(
                Enrollment.student_id == student_id,
                Enrollment.status == "active",
            )
            .order_by(Enrollment.enrolled_at.asc())
            .all()
        )


class InvitationRepository(BaseRepository[Invitation]):
    """Data access for classroom invitations."""

    def get_by_token(self, token: str) -> Optional[Invitation]:
        return self.session.query(Invitation).filter(Invitation.token == token).first()

    def list_for_classroom(self, classroom_id: str) -> List[Invitation]:
        return (
            self.session.query(Invitation)
            .filter(Invitation.classroom_id == classroom_id)
            .order_by(Invitation.created_at.desc())
            .all()
        )


class MonitorStateRepository(BaseRepository[MonitorState]):
    """Data access for per-student monitor (screen-lock) state."""

    def get(self, classroom_id: str, student_id: str) -> Optional[MonitorState]:
        return (
            self.session.query(MonitorState)
            .filter(
                MonitorState.classroom_id == classroom_id,
                MonitorState.student_id == student_id,
            )
            .first()
        )

    def list_for_student(self, student_id: str) -> List[MonitorState]:
        """Every monitor row for a student, across all the classes they're in."""
        return (
            self.session.query(MonitorState)
            .filter(MonitorState.student_id == student_id)
            .all()
        )


class MonitorAwayEventRepository(BaseRepository[MonitorAwayEvent]):
    """Data access for the append-only tab-away history."""

    def list_for_classroom(
        self, classroom_id: str, limit: int = 100
    ) -> List[MonitorAwayEvent]:
        """Most-recent away/return events for a class, newest first."""
        return (
            self.session.query(MonitorAwayEvent)
            .filter(MonitorAwayEvent.classroom_id == classroom_id)
            .order_by(MonitorAwayEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    def delete_for_classroom(self, classroom_id: str) -> int:
        """Clear the whole away-log for a class. Returns the number removed."""
        n = (
            self.session.query(MonitorAwayEvent)
            .filter(MonitorAwayEvent.classroom_id == classroom_id)
            .delete(synchronize_session=False)
        )
        self.session.commit()
        return n

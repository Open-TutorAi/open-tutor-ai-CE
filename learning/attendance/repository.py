"""Attendance repository."""

from datetime import datetime
from typing import List, Optional

from common.exceptions import NotFoundError
from data.models import ClassSession, Presence, PresenceStatus
from data.repositories import BaseRepository


class AttendanceRepository(BaseRepository[ClassSession]):
    """Repository for class session and presence operations."""

    def create_session(
        self,
        classroom_id: str,
        scheduled_at: datetime,
        subject: Optional[str] = None,
        objectives: Optional[str] = None,
        auto_recorded: bool = True,
    ) -> ClassSession:
        session_row = ClassSession(
            classroom_id=classroom_id,
            scheduled_at=scheduled_at,
            subject=subject,
            objectives=objectives,
            auto_recorded=auto_recorded,
        )
        self.session.add(session_row)
        self.session.commit()
        return session_row

    def get_session_by_id(self, session_id: str) -> Optional[ClassSession]:
        return (
            self.session.query(ClassSession)
            .filter(ClassSession.id == session_id)
            .first()
        )

    def get_sessions_by_classroom(self, classroom_id: str) -> List[ClassSession]:
        return (
            self.session.query(ClassSession)
            .filter(ClassSession.classroom_id == classroom_id)
            .order_by(ClassSession.scheduled_at.asc())
            .all()
        )

    def get_open_session(self, classroom_id: str) -> Optional[ClassSession]:
        return (
            self.session.query(ClassSession)
            .filter(
                ClassSession.classroom_id == classroom_id,
                ClassSession.ended_at.is_(None),
            )
            .order_by(ClassSession.scheduled_at.desc())
            .first()
        )

    def end_session(self, session_id: str) -> Optional[ClassSession]:
        session_row = self.get_session_by_id(session_id)
        if session_row is None:
            return None
        session_row.ended_at = datetime.utcnow()
        self.session.commit()
        return session_row

    def delete_session(self, session_id: str) -> None:
        session_row = self.get_session_by_id(session_id)
        if session_row is None:
            return
        self.session.delete(session_row)
        self.session.commit()

    def create_presence(
        self,
        session_id: str,
        student_id: str,
        status: PresenceStatus = PresenceStatus.PRESENT,
    ) -> Presence:
        presence = Presence(session_id=session_id, student_id=student_id, status=status)
        self.session.add(presence)
        self.session.commit()
        return presence

    def get_presences_by_session(self, session_id: str) -> List[Presence]:
        return (
            self.session.query(Presence).filter(Presence.session_id == session_id).all()
        )

    def get_presence(self, session_id: str, student_id: str) -> Optional[Presence]:
        return (
            self.session.query(Presence)
            .filter(
                Presence.session_id == session_id,
                Presence.student_id == student_id,
            )
            .first()
        )

    def get_presence_by_id(self, presence_id: str) -> Optional[Presence]:
        return self.session.query(Presence).filter(Presence.id == presence_id).first()

    def update_presence_status(
        self, session_id: str, student_id: str, status: PresenceStatus
    ) -> Presence:
        presence = self.get_presence(session_id, student_id)
        if presence is None:
            raise NotFoundError("Presence", f"{session_id}:{student_id}")
        presence.status = status
        self.session.commit()
        return presence

    def get_presences_by_student(
        self, classroom_id: str, student_id: str
    ) -> List[Presence]:
        """Return a student's presences for a classroom, oldest session first."""
        return (
            self.session.query(Presence)
            .join(ClassSession, Presence.session_id == ClassSession.id)
            .filter(
                ClassSession.classroom_id == classroom_id,
                Presence.student_id == student_id,
            )
            .order_by(ClassSession.scheduled_at.asc())
            .all()
        )

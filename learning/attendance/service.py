"""Attendance business logic."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import Classroom, ClassSession, Presence, PresenceStatus
from learning.attendance.repository import AttendanceRepository
from learning.classrooms.repository import ClassroomRepository
from learning.sessions.schemas import (
    AttendanceStats,
    PresenceOut,
    SessionOut,
    SessionSummaryOut,
    StudentHistory,
)


def _to_presence_out(presence: Presence) -> PresenceOut:
    return PresenceOut(
        id=presence.id,
        student_id=presence.student_id,
        student_name=presence.student.name,
        status=presence.status.value,
        recorded_at=presence.recorded_at,
    )


class AttendanceService:

    def __init__(self, session: Session):
        self.repo = AttendanceRepository(session, ClassSession)
        self.classroom_repo = ClassroomRepository(session, Classroom)

    def _require_classroom_owner(self, classroom_id: str, caller_id: str) -> Classroom:
        classroom = self.classroom_repo.get_by_id(classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom", classroom_id)
        if classroom.owner_id != caller_id:
            raise AuthorizationError("not_owner")
        return classroom

    def _require_session_classroom_owner(
        self, session_id: str, caller_id: str
    ) -> ClassSession:
        session_row = self.repo.get_session_by_id(session_id)
        if session_row is None:
            raise NotFoundError("ClassSession", session_id)
        self._require_classroom_owner(session_row.classroom_id, caller_id)
        return session_row

    def start_session(
        self,
        classroom_id: str,
        caller_id: str,
        scheduled_at: datetime,
        subject: Optional[str] = None,
        objectives: Optional[str] = None,
    ) -> SessionOut:
        classroom = self._require_classroom_owner(classroom_id, caller_id)
        session_row = self.repo.create_session(
            classroom_id,
            scheduled_at,
            subject=subject,
            objectives=objectives,
            auto_recorded=True,
        )
        for enrollment in classroom.enrollments:
            self.repo.create_presence(
                session_row.id, enrollment.student_id, status=PresenceStatus.ABSENT
            )
        return SessionOut(
            id=session_row.id,
            classroom_id=session_row.classroom_id,
            scheduled_at=session_row.scheduled_at,
            subject=session_row.subject,
            objectives=session_row.objectives,
            auto_recorded=session_row.auto_recorded,
            ended_at=session_row.ended_at,
        )

    def end_session(self, session_id: str, caller_id: str) -> SessionOut:
        session_row = self._require_session_classroom_owner(session_id, caller_id)
        session_row = self.repo.end_session(session_row.id)
        return SessionOut(
            id=session_row.id,
            classroom_id=session_row.classroom_id,
            scheduled_at=session_row.scheduled_at,
            subject=session_row.subject,
            objectives=session_row.objectives,
            auto_recorded=session_row.auto_recorded,
            ended_at=session_row.ended_at,
        )

    def delete_session(self, session_id: str, caller_id: str) -> None:
        session_row = self._require_session_classroom_owner(session_id, caller_id)
        if session_row.ended_at is None:
            raise ValidationError("End the session before deleting it")
        self.repo.delete_session(session_row.id)

    def join_session(self, session_id: str, student_id: str) -> PresenceOut:
        session_row = self.repo.get_session_by_id(session_id)
        if session_row is None:
            raise NotFoundError("ClassSession", session_id)
        if session_row.ended_at is not None:
            raise ValidationError("This session has ended")
        if not self.classroom_repo.is_enrolled(session_row.classroom_id, student_id):
            raise AuthorizationError("not_enrolled")

        presence = self.repo.get_presence(session_id, student_id)
        if presence is None:
            presence = self.repo.create_presence(
                session_id, student_id, status=PresenceStatus.PRESENT
            )
        elif presence.status == PresenceStatus.ABSENT:
            presence = self.repo.update_presence_status(
                session_id, student_id, PresenceStatus.PRESENT
            )
        return _to_presence_out(presence)

    def get_session_presences(
        self, session_id: str, caller_id: str
    ) -> List[PresenceOut]:
        session_row = self.repo.get_session_by_id(session_id)
        if session_row is None:
            raise NotFoundError("ClassSession", session_id)
        classroom = self.classroom_repo.get_by_id(session_row.classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom", session_row.classroom_id)

        presences = self.repo.get_presences_by_session(session_id)
        if classroom.owner_id != caller_id:
            presences = [p for p in presences if p.student_id == caller_id]
            if not presences:
                raise AuthorizationError("not_authorized")
        return [_to_presence_out(p) for p in presences]

    def update_presence_status(
        self,
        session_id: str,
        student_id: str,
        caller_id: str,
        status: PresenceStatus,
    ) -> PresenceOut:
        self._require_session_classroom_owner(session_id, caller_id)
        presence = self.repo.update_presence_status(session_id, student_id, status)
        return _to_presence_out(presence)

    def update_presence(
        self, presence_id: str, caller_id: str, status: PresenceStatus
    ) -> PresenceOut:
        presence = self.repo.get_presence_by_id(presence_id)
        if presence is None:
            raise NotFoundError("Presence", presence_id)
        return self.update_presence_status(
            presence.session_id, presence.student_id, caller_id, status
        )

    def get_session_summaries(
        self, classroom_id: str, caller_id: str
    ) -> List[SessionSummaryOut]:
        self._require_classroom_owner(classroom_id, caller_id)
        sessions = self.repo.get_sessions_by_classroom(classroom_id)

        summaries = []
        for session_row in sessions:
            presences = self.repo.get_presences_by_session(session_row.id)
            summaries.append(
                SessionSummaryOut(
                    id=session_row.id,
                    classroom_id=session_row.classroom_id,
                    scheduled_at=session_row.scheduled_at,
                    subject=session_row.subject,
                    objectives=session_row.objectives,
                    auto_recorded=session_row.auto_recorded,
                    ended_at=session_row.ended_at,
                    present_count=sum(
                        1 for p in presences if p.status == PresenceStatus.PRESENT
                    ),
                    absent_count=sum(
                        1 for p in presences if p.status == PresenceStatus.ABSENT
                    ),
                    late_count=sum(
                        1 for p in presences if p.status == PresenceStatus.LATE
                    ),
                )
            )
        return summaries

    def get_attendance_stats(
        self, classroom_id: str, caller_id: str
    ) -> AttendanceStats:
        self._require_classroom_owner(classroom_id, caller_id)
        sessions = self.repo.get_sessions_by_classroom(classroom_id)

        total_absences = 0
        total_lates = 0
        rates = []
        for session_row in sessions:
            presences = self.repo.get_presences_by_session(session_row.id)
            total = len(presences)
            if total == 0:
                continue
            attended = sum(
                1
                for p in presences
                if p.status in (PresenceStatus.PRESENT, PresenceStatus.LATE)
            )
            total_absences += sum(
                1 for p in presences if p.status == PresenceStatus.ABSENT
            )
            total_lates += sum(1 for p in presences if p.status == PresenceStatus.LATE)
            rates.append(attended / total)

        avg_rate = (sum(rates) / len(rates) * 100) if rates else 0.0
        return AttendanceStats(
            avg_rate=avg_rate,
            sessions_count=len(sessions),
            total_absences=total_absences,
            total_lates=total_lates,
        )

    def get_student_history(
        self, classroom_id: str, student_id: str, caller_id: str
    ) -> StudentHistory:
        classroom = self.classroom_repo.get_by_id(classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom", classroom_id)
        if classroom.owner_id != caller_id and caller_id != student_id:
            raise AuthorizationError("not_authorized")

        presences = self.repo.get_presences_by_student(classroom_id, student_id)
        presences_count = sum(
            1 for p in presences if p.status == PresenceStatus.PRESENT
        )
        absences_count = sum(1 for p in presences if p.status == PresenceStatus.ABSENT)
        lates_count = sum(1 for p in presences if p.status == PresenceStatus.LATE)
        total = len(presences)
        rate = ((presences_count + lates_count) / total * 100) if total else 0.0

        return StudentHistory(
            student_id=student_id,
            rate=rate,
            presences=presences_count,
            absences=absences_count,
            lates=lates_count,
            last_10=[p.status.value for p in presences[-10:]],
        )

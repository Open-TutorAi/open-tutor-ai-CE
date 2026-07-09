"""Classrooms service — business logic + authorization (no ORM directly).

Increment 0–1: create (guided-wizard pedagogical payload, all-required validation),
list/get/delete with ownership checks. Later increments add roster, invitations, progress.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from accounts.users.service import AccountService as IdentityService
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import (
    Classroom,
    Enrollment,
    Invitation,
    MonitorAwayEvent,
    MonitorState,
    Submission,
)
from governance.self_regulation.service import SelfRegulationService
from learning.assignments.repository import SubmissionRepository
from learning.classrooms.repository import (
    ClassroomRepository,
    EnrollmentRepository,
    InvitationRepository,
    MonitorAwayEventRepository,
    MonitorStateRepository,
)
from learning.guardians.service import GuardiansService
from learning.supports.service import SupportsService

INVITE_EXPIRY_DAYS = 14
# A student counts as "active" if they've touched a support within this window.
ACTIVE_WITHIN_DAYS = 7

# All required (per the wizard). `custom_subject` is the only optional text field.
REQUIRED_FIELDS = [
    "name",
    "short_description",
    "subject",
    "course",
    "learning_objective",
    "competencies",
    "learning_type",
    "level",
    "content_language",
    "estimated_duration",
]


class ClassroomsService:
    """Service for classroom operations (teacher section)."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = ClassroomRepository(session, Classroom)
        self.enrollments = EnrollmentRepository(session, Enrollment)
        self.invitations = InvitationRepository(session, Invitation)
        self.monitors = MonitorStateRepository(session, MonitorState)
        self.away_events = MonitorAwayEventRepository(session, MonitorAwayEvent)
        # Read-only aggregation for the dashboard (reuse, not duplicate).
        self.submissions = SubmissionRepository(session, Submission)
        self.identity = IdentityService(session)
        # Existing contexts read for the progress read model (reuse, not duplicate).
        self.supports = SupportsService(session)
        self.self_regulation = SelfRegulationService(session)
        # The parent↔student bond lives in its own context; we initiate/read it here.
        self.guardians = GuardiansService(session)

    # ── internal helpers ────────────────────────────────────────────────────

    def _owned(self, classroom_id: str, teacher_id: str) -> Classroom:
        """Fetch a classroom and assert the teacher owns it (else 404/403)."""
        room = self.repo.get_by_id(classroom_id)
        if not room:
            raise NotFoundError("Classroom", classroom_id)
        if room.teacher_id != teacher_id:
            raise AuthorizationError("Not authorized for this classroom")
        return room

    def _with_count(self, room: Classroom) -> Dict[str, Any]:
        return {
            **room.to_dict(),
            "student_count": self.repo.count_active_students(room.id),
        }

    # ── operations ───────────────────────────────────────────────────────────

    def create(self, teacher_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        for field in REQUIRED_FIELDS:
            value = data.get(field)
            if not (isinstance(value, str) and value.strip()):
                raise ValidationError(f"{field} is required")
        keywords = data.get("keywords")
        if not keywords:
            raise ValidationError("keywords is required")

        # Optional teacher settings — schedule + capacity (validated leniently).
        capacity = data.get("capacity")
        if capacity is not None:
            try:
                capacity = int(capacity)
            except (TypeError, ValueError):
                raise ValidationError("capacity must be a whole number")
            if capacity <= 0:
                raise ValidationError("capacity must be a positive number")
        term_start = self._parse_date(data.get("term_start"))
        term_end = self._parse_date(data.get("term_end"))
        if term_start and term_end and term_end < term_start:
            raise ValidationError("term_end cannot be before term_start")
        meeting_days = data.get("meeting_days")
        meeting_days = (
            ",".join(meeting_days)
            if isinstance(meeting_days, list) and meeting_days
            else None
        )

        now = datetime.utcnow()
        room = self.repo.create(
            id=str(uuid.uuid4()),
            teacher_id=teacher_id,
            name=data["name"].strip(),
            short_description=data["short_description"].strip(),
            subject=data["subject"].strip(),
            custom_subject=(data.get("custom_subject") or None),
            course=data["course"].strip(),
            learning_objective=data["learning_objective"].strip(),
            competencies=data["competencies"].strip(),
            learning_type=data["learning_type"].strip(),
            level=data["level"].strip(),
            content_language=data["content_language"].strip(),
            estimated_duration=data["estimated_duration"].strip(),
            keywords=(
                ",".join(keywords) if isinstance(keywords, list) else str(keywords)
            ),
            capacity=capacity,
            term_start=term_start,
            term_end=term_end,
            meeting_days=meeting_days,
            created_at=now,
            updated_at=now,
        )
        return self._with_count(room)

    @staticmethod
    def _parse_date(value: Any) -> Any:
        """Parse an ISO date/datetime (e.g. '2026-09-01') → datetime, or None."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except ValueError:
            raise ValidationError("dates must be ISO 8601 (YYYY-MM-DD)")

    def list_for_teacher(self, teacher_id: str) -> List[dict]:
        """All classes owned by a teacher, each with its active student count."""
        rooms = self.repo.get_by_teacher(teacher_id)
        return [self._with_count(room) for room in rooms]

    def dashboard_stats(self, teacher_id: str) -> Dict[str, int]:
        """Headline counts for the teacher dashboard, aggregated across the
        teacher's own classes: number of classes, distinct enrolled students,
        pending invitations, and submissions still awaiting a grade. Each count
        is a single aggregate query — no rows are materialised to be counted."""
        room_ids = [r.id for r in self.repo.get_by_teacher(teacher_id)]
        return {
            "classes": len(room_ids),
            "students": self.enrollments.count_distinct_students(room_ids),
            "pending_invites": self.invitations.count_pending(room_ids),
            "to_grade": self.submissions.count_ungraded_for_classrooms(room_ids),
        }

    def get(self, classroom_id: str, teacher_id: str) -> Dict[str, Any]:
        return self._with_count(self._owned(classroom_id, teacher_id))

    def delete(self, classroom_id: str, teacher_id: str) -> None:
        self._owned(classroom_id, teacher_id)
        self.repo.delete(classroom_id)

    # ── roster: enrolment ────────────────────────────────────────────────────

    def _roster_entry(self, enrollment: Enrollment) -> Dict[str, Any]:
        student = self.identity.get_user(enrollment.student_id)
        return {
            "student_id": enrollment.student_id,
            "name": student.name if student else None,
            "email": student.email if student else None,
            "status": enrollment.status,
            "enrolled_at": (
                enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None
            ),
        }

    def list_roster(self, classroom_id: str, teacher_id: str) -> List[Dict[str, Any]]:
        self._owned(classroom_id, teacher_id)
        return [
            self._roster_entry(e) for e in self.enrollments.list_active(classroom_id)
        ]

    def list_roster_ids(self, classroom_id: str, teacher_id: str) -> List[str]:
        """Active student ids only — no per-student user lookup. Used by the live
        presence poll, where names already live client-side (in the loaded roster)."""
        self._owned(classroom_id, teacher_id)
        return [e.student_id for e in self.enrollments.list_active(classroom_id)]

    def _enrol_user(self, classroom_id: str, student_id: str) -> Enrollment:
        if self.enrollments.get(classroom_id, student_id):
            raise ValidationError("Student is already enrolled in this class")
        return self.enrollments.create(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            student_id=student_id,
            status="active",
            enrolled_at=datetime.utcnow(),
        )

    def enrol(self, classroom_id: str, teacher_id: str, email: str) -> Dict[str, Any]:
        self._owned(classroom_id, teacher_id)
        student = self.identity.get_user_by_email(email)
        if not student:
            raise NotFoundError("User", email)
        return self._roster_entry(self._enrol_user(classroom_id, student.id))

    def remove_student(
        self, classroom_id: str, teacher_id: str, student_id: str
    ) -> None:
        self._owned(classroom_id, teacher_id)
        enrollment = self.enrollments.get(classroom_id, student_id)
        if not enrollment:
            raise NotFoundError("Enrollment", student_id)
        self.enrollments.delete(enrollment.id)

    # ── roster: invitations ──────────────────────────────────────────────────

    def invite(
        self,
        classroom_id: str,
        teacher_id: str,
        email: str,
        invitee_role: str = "student",
    ) -> Dict[str, Any]:
        self._owned(classroom_id, teacher_id)
        if invitee_role not in ("student", "parent"):
            raise ValidationError("invitee_role must be 'student' or 'parent'")
        now = datetime.utcnow()
        invitation = self.invitations.create(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            email=email,
            invitee_role=invitee_role,
            token=secrets.token_urlsafe(24),
            status="pending",
            invited_by=teacher_id,
            created_at=now,
            expires_at=now + timedelta(days=INVITE_EXPIRY_DAYS),
        )
        # No email infrastructure yet → return a shareable join link (graceful
        # degradation per the product vision); a mailer can be wired later.
        return {
            "invitation": invitation.to_dict(),
            "join_url": f"/invite/{invitation.token}",
            "email_sent": False,
        }

    def list_invitations(
        self, classroom_id: str, teacher_id: str
    ) -> List[Dict[str, Any]]:
        self._owned(classroom_id, teacher_id)
        return [i.to_dict() for i in self.invitations.list_for_classroom(classroom_id)]

    def accept_invitation(
        self, token: str, accepting_user_id: str, accepting_email: str = ""
    ) -> Dict[str, Any]:
        """Accept a pending invitation.

        Student invites enrol the accepting user; **parent** invites resolve into an
        active guardian link (via the `guardians` context, matched by email).
        """
        invitation = self.invitations.get_by_token(token)
        if not invitation:
            raise NotFoundError("Invitation", token)
        if invitation.status != "pending":
            raise ValidationError("This invitation is no longer valid")
        if invitation.expires_at and invitation.expires_at < datetime.utcnow():
            invitation.status = "expired"
            self.session.commit()
            raise ValidationError("This invitation has expired")

        if invitation.invitee_role == "student":
            if not self.enrollments.get(invitation.classroom_id, accepting_user_id):
                self._enrol_user(invitation.classroom_id, accepting_user_id)
        elif invitation.invitee_role == "parent":
            self.guardians.resolve_on_accept(
                accepting_user_id, accepting_email or invitation.email
            )

        invitation.status = "accepted"
        invitation.accepted_user_id = accepting_user_id
        self.session.commit()
        return {
            "status": "accepted",
            "classroom_id": invitation.classroom_id,
            "invitee_role": invitation.invitee_role,
        }

    # ── guardians (parent link & contact) ────────────────────────────────────

    def _owned_and_enrolled(
        self, classroom_id: str, teacher_id: str, student_id: str
    ) -> None:
        self._owned(classroom_id, teacher_id)
        if not self.enrollments.get(classroom_id, student_id):
            raise NotFoundError("Student", student_id)

    def list_guardians(
        self, classroom_id: str, teacher_id: str, student_id: str
    ) -> List[Dict[str, Any]]:
        self._owned_and_enrolled(classroom_id, teacher_id, student_id)
        return self.guardians.get_links_for_student(student_id)

    def invite_guardian(
        self, classroom_id: str, teacher_id: str, student_id: str, email: str
    ) -> Dict[str, Any]:
        """Link or invite a parent for an enrolled student.

        Existing parent account → active link. Otherwise → pending link + a classroom
        invitation (role=parent) that the parent accepts to activate the link.
        """
        self._owned_and_enrolled(classroom_id, teacher_id, student_id)
        result = self.guardians.link(student_id, teacher_id, email)
        if result["status"] == "active":
            return {"guardian": result["link"], "status": "active"}

        now = datetime.utcnow()
        invitation = self.invitations.create(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            email=email,
            invitee_role="parent",
            token=secrets.token_urlsafe(24),
            status="pending",
            invited_by=teacher_id,
            created_at=now,
            expires_at=now + timedelta(days=INVITE_EXPIRY_DAYS),
        )
        return {
            "guardian": result["link"],
            "status": "pending",
            "join_url": f"/invite/{invitation.token}",
            "email_sent": False,
        }

    # ── student-facing: my teachers (messaging contacts) ─────────────────────

    def list_my_teachers(self, student_id: str) -> List[Dict[str, Any]]:
        """Deduplicated teachers across the classes the student is enrolled in.

        Lets a student see who they may message (the symmetric counterpart of the
        teacher's Students directory). Read-only, assembled from existing data.
        """
        agg: Dict[str, Dict[str, Any]] = {}
        for enrollment in self.enrollments.list_for_student(student_id):
            room = self.repo.get_by_id(enrollment.classroom_id)
            if not room:
                continue
            entry = agg.get(room.teacher_id)
            if entry is None:
                teacher = self.identity.get_user(room.teacher_id)
                entry = {
                    "teacher_id": room.teacher_id,
                    "name": teacher.name if teacher else None,
                    "email": teacher.email if teacher else None,
                    "classes": [],
                }
                agg[room.teacher_id] = entry
            entry["classes"].append({"id": room.id, "name": room.name})
        return list(agg.values())

    # ── classroom control: student monitors (E6) ─────────────────────────────

    def _set_monitor_row(
        self,
        classroom_id: str,
        student_id: str,
        enabled: bool,
        teacher_id: str,
        commit: bool = True,
    ) -> None:
        """Upsert the persisted desired monitor state (the truth behind the event).

        Pass ``commit=False`` when upserting many rows in a loop (class-level toggle)
        so the caller can commit once for the whole batch.
        """
        row = self.monitors.get(classroom_id, student_id)
        now = datetime.utcnow()
        if row:
            row.enabled = enabled
            row.updated_by = teacher_id
            row.updated_at = now
            if commit:
                self.session.commit()
        else:
            self.monitors.create(
                commit=commit,
                id=str(uuid.uuid4()),
                classroom_id=classroom_id,
                student_id=student_id,
                enabled=enabled,
                updated_by=teacher_id,
                updated_at=now,
            )

    def get_monitor_state(
        self, classroom_id: str, teacher_id: str, student_id: str
    ) -> Dict[str, Any]:
        """Current desired monitor state for one enrolled student (defaults to on)."""
        self._owned_and_enrolled(classroom_id, teacher_id, student_id)
        row = self.monitors.get(classroom_id, student_id)
        return {"student_id": student_id, "enabled": row.enabled if row else True}

    def set_monitor(
        self, classroom_id: str, teacher_id: str, student_id: str, enabled: bool
    ) -> Dict[str, Any]:
        """Persist a single student's monitor state (authz + enrolment enforced).

        Realtime *delivery* (emit + online check) is the router's concern; this returns
        the target so the router can fan out the `monitor:set` event.
        """
        self._owned_and_enrolled(classroom_id, teacher_id, student_id)
        self._set_monitor_row(classroom_id, student_id, enabled, teacher_id)
        return {"student_id": student_id, "enabled": enabled}

    def set_class_monitor(
        self, classroom_id: str, teacher_id: str, enabled: bool
    ) -> List[Dict[str, Any]]:
        """Persist the monitor state for every enrolled student in the class."""
        self._owned(classroom_id, teacher_id)
        targets: List[Dict[str, Any]] = []
        for enrollment in self.enrollments.list_active(classroom_id):
            # Defer per-row commits; persist the whole roster in one transaction below.
            self._set_monitor_row(
                classroom_id, enrollment.student_id, enabled, teacher_id, commit=False
            )
            targets.append({"student_id": enrollment.student_id, "enabled": enabled})
        self.session.commit()
        return targets

    def get_my_monitor_state(self, student_id: str) -> Dict[str, Any]:
        """The calling student's own screen-lock state, aggregated across every class.

        The student has one screen, so any class that locks them locks the screen:
        `enabled=False` (locked) if *any* monitor row is disabled; otherwise on.
        Read by the client on (re)connect to re-apply a lock set while it was offline.
        """
        rows = self.monitors.list_for_student(student_id)
        enabled = all(row.enabled for row in rows)
        return {"enabled": enabled}

    def report_presence(self, student_id: str, away: bool) -> List[Dict[str, Any]]:
        """Resolve who should hear that a *locked* student left/returned to the screen.

        Tab-away telemetry only matters while a teacher is actively locking the student,
        so this returns one target per class that currently has them locked
        (`enabled=False`): the owning teacher + classroom. The router fans the live
        `monitor:student-away` event out to those teachers. No lock → no targets → silence.
        The caller reports their *own* presence (no authz needed beyond authentication).
        """
        targets: List[Dict[str, Any]] = []
        now = datetime.utcnow()
        for row in self.monitors.list_for_student(student_id):
            if row.enabled:
                continue  # not locked in this class → nothing to report
            room = self.repo.get_by_id(row.classroom_id)
            if not room:
                continue
            # Persist the transition (durable history) — deferred commit, one below.
            self.away_events.create(
                commit=False,
                id=str(uuid.uuid4()),
                classroom_id=row.classroom_id,
                student_id=student_id,
                away=away,
                created_at=now,
            )
            targets.append(
                {
                    "teacher_id": room.teacher_id,
                    "classroom_id": row.classroom_id,
                    "student_id": student_id,
                    "away": away,
                }
            )
        if targets:
            self.session.commit()
        return targets

    def list_away_log(
        self, classroom_id: str, teacher_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Recent tab-away history for a class (teacher-owned), newest first.

        Lets a teacher see what happened while they weren't watching the Control tab —
        the durable counterpart of the live `monitor:student-away` event.
        """
        self._owned(classroom_id, teacher_id)
        events: List[Dict[str, Any]] = []
        for ev in self.away_events.list_for_classroom(classroom_id, limit):
            student = self.identity.get_user(ev.student_id)
            events.append(
                {
                    **ev.to_dict(),
                    "student_name": student.name if student else None,
                    "student_email": student.email if student else None,
                }
            )
        return events

    def clear_away_log(self, classroom_id: str, teacher_id: str) -> int:
        """Clear a class's tab-away history (teacher-owned). Returns the count removed."""
        self._owned(classroom_id, teacher_id)
        return self.away_events.delete_for_classroom(classroom_id)

    # ── students directory (across all the teacher's classes) ────────────────

    def list_all_students(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Deduplicated roster across every class the teacher owns.

        Each student carries the classes they're in plus the same read-only signals
        used elsewhere (supports total, activity status, guardian count). Assembled
        from existing data — no writes.
        """
        agg: Dict[str, Dict[str, Any]] = {}
        for room in self.repo.get_by_teacher(teacher_id):
            for enrollment in self.enrollments.list_active(room.id):
                entry = agg.get(enrollment.student_id)
                if entry is None:
                    student = self.identity.get_user(enrollment.student_id)
                    supports = self._supports_for(enrollment.student_id)
                    last_active = self._last_active(supports)
                    entry = {
                        "student_id": enrollment.student_id,
                        "name": student.name if student else None,
                        "email": student.email if student else None,
                        "classes": [],
                        "supports_total": len(supports),
                        "last_active": (
                            last_active.isoformat() if last_active else None
                        ),
                        "status": self._activity_status(last_active, len(supports)),
                        "guardians": len(
                            self.guardians.get_links_for_student(enrollment.student_id)
                        ),
                    }
                    agg[enrollment.student_id] = entry
                entry["classes"].append({"id": room.id, "name": room.name})
        return list(agg.values())

    # ── progress monitoring (read-only) ──────────────────────────────────────

    def _supports_for(self, student_id: str) -> List[Any]:
        return self.supports.list_for_user(student_id)

    @staticmethod
    def _last_active(supports: List[Any]):
        stamps = [s.updated_at for s in supports if s.updated_at]
        return max(stamps) if stamps else None

    @staticmethod
    def _activity_status(last_active, total: int) -> str:
        if total == 0:
            return "not_started"
        if last_active and (datetime.utcnow() - last_active) <= timedelta(
            days=ACTIVE_WITHIN_DAYS
        ):
            return "active"
        return "idle"

    def _engagement(self, student_id: str) -> Dict[str, int]:
        feedbacks = self.self_regulation.get_by_user(student_id)
        return {
            "feedback_positive": sum(
                1 for f in feedbacks if f.feedback_type == "positive"
            ),
            "feedback_negative": sum(
                1 for f in feedbacks if f.feedback_type == "negative"
            ),
            "feedback_total": len(feedbacks),
        }

    def get_class_progress(
        self, classroom_id: str, teacher_id: str
    ) -> List[Dict[str, Any]]:
        """Compact per-student signals for a class (read-only)."""
        self._owned(classroom_id, teacher_id)
        rows: List[Dict[str, Any]] = []
        for enrollment in self.enrollments.list_active(classroom_id):
            student = self.identity.get_user(enrollment.student_id)
            supports = self._supports_for(enrollment.student_id)
            last_active = self._last_active(supports)
            rows.append(
                {
                    "student_id": enrollment.student_id,
                    "name": student.name if student else None,
                    "email": student.email if student else None,
                    "supports_total": len(supports),
                    "last_active": last_active.isoformat() if last_active else None,
                    "status": self._activity_status(last_active, len(supports)),
                }
            )
        return rows

    def get_student_progress(
        self, classroom_id: str, teacher_id: str, student_id: str
    ) -> Dict[str, Any]:
        """Detailed, read-only progress for one enrolled student.

        Assembled from existing data (supports + feedback). Missing signals render
        as empty/None rather than raising. No writes occur.
        """
        self._owned(classroom_id, teacher_id)
        if not self.enrollments.get(classroom_id, student_id):
            raise NotFoundError("Student", student_id)

        student = self.identity.get_user(student_id)
        supports = self._supports_for(student_id)
        last_active = self._last_active(supports)

        by_status: Dict[str, int] = {}
        for s in supports:
            by_status[s.status] = by_status.get(s.status, 0) + 1
        items = [
            {
                "id": s.id,
                "title": s.title,
                "subject": s.subject,
                "level": s.level,
                "status": s.status,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in supports
        ]

        return {
            "student_id": student_id,
            "name": student.name if student else None,
            "email": student.email if student else None,
            "activity": {
                "last_active": last_active.isoformat() if last_active else None,
                "status": self._activity_status(last_active, len(supports)),
            },
            "supports": {
                "total": len(supports),
                "by_status": by_status,
                "items": items,
            },
            "engagement": self._engagement(student_id),
        }

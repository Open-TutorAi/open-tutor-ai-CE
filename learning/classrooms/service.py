"""Classrooms business logic."""

from typing import List, Optional, IO
import csv
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from accounts.users.service import AccountService
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import Classroom
from learning.attendance.repository import AttendanceRepository
from learning.classrooms.repository import ClassroomRepository
from learning.classrooms.schemas import (
    AddStudentResult,
    ClassroomCreate,
    ClassroomDetail,
    ClassroomOut,
    ClassroomUpdate,
    EnrolledClassroomOut,
    StudentOut,
    ImportResult,
    ImportRowReport,
    InviteCreate,
    InviteOut,
    InviteRedeemResult,
)
from data.models import ClassSession, Invite


def _objectives_list(objectives: Optional[str]) -> List[str]:
    if not objectives:
        return []
    return [line.strip() for line in objectives.splitlines() if line.strip()]


def _to_classroom_out(classroom, student_count: int) -> ClassroomOut:
    return ClassroomOut(
        id=classroom.id,
        name=classroom.name,
        subject=classroom.subject,
        course=classroom.course,
        objectives=classroom.objectives,
        level=classroom.level,
        description=classroom.description,
        created_at=classroom.created_at,
        owner_id=classroom.owner_id,
        student_count=student_count,
    )


class ClassroomsService:

    def __init__(self, session: Session):
        self.session = session
        self.repo = ClassroomRepository(session, Classroom)
        self.attendance_repo = AttendanceRepository(session, ClassSession)

    def _require_owned(self, classroom_id: str, caller_id: str) -> Classroom:
        classroom = self.repo.get_by_id(classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom", classroom_id)
        if classroom.owner_id != caller_id:
            raise AuthorizationError("not_owner")
        return classroom

    def create_classroom(self, owner_id: str, data: ClassroomCreate) -> ClassroomOut:
        classroom = self.repo.create(owner_id, data)
        return _to_classroom_out(classroom, student_count=0)

    def get_my_classrooms(
        self, owner_id: str, limit: int = 100, offset: int = 0
    ) -> List[ClassroomOut]:
        classrooms = self.repo.get_by_owner(owner_id, limit=limit, offset=offset)
        return [_to_classroom_out(c, student_count=c.student_count) for c in classrooms]

    def list_enrolled_classrooms(
        self, student_id: str, limit: int = 100, offset: int = 0
    ) -> List[EnrolledClassroomOut]:
        classrooms = self.repo.get_enrolled_classrooms(
            student_id, limit=limit, offset=offset
        )
        result = []
        for classroom in classrooms:
            open_session = self.attendance_repo.get_open_session(classroom.id)
            base = _to_classroom_out(classroom, student_count=classroom.student_count)
            result.append(
                EnrolledClassroomOut(
                    **base.model_dump(),
                    active_session_id=open_session.id if open_session else None,
                )
            )
        return result

    def get_classroom_detail(
        self, classroom_id: str, caller_id: str
    ) -> ClassroomDetail:
        classroom = self._require_owned(classroom_id, caller_id)
        base = _to_classroom_out(classroom, student_count=len(classroom.enrollments))
        join_code = self.get_or_create_join_code(classroom_id, caller_id)
        return ClassroomDetail(
            **base.model_dump(),
            objectives_list=_objectives_list(classroom.objectives),
            recent_activity=[],
            join_code=join_code,
        )

    def get_or_create_join_code(self, classroom_id: str, caller_id: str) -> str:
        self._require_owned(classroom_id, caller_id)
        invite = self.repo.get_primary_invite(classroom_id)
        if invite is None:
            invite = self.repo.create_invite(
                classroom_id=classroom_id,
                code=uuid.uuid4().hex[:16],
                created_by=caller_id,
                is_primary=True,
            )
        return invite.code

    def update_classroom(
        self, classroom_id: str, caller_id: str, data: ClassroomUpdate
    ) -> ClassroomOut:
        classroom = self._require_owned(classroom_id, caller_id)
        updates = data.model_dump(exclude_unset=True)
        if updates:
            classroom = self.repo.update(classroom_id, **updates)
        return _to_classroom_out(classroom, student_count=len(classroom.enrollments))

    def delete_classroom(self, classroom_id: str, caller_id: str) -> None:
        self._require_owned(classroom_id, caller_id)
        self.repo.delete(classroom_id)

    def list_students(
        self, classroom_id: str, caller_id: str, limit: int = 100, offset: int = 0
    ) -> List[StudentOut]:
        self._require_owned(classroom_id, caller_id)
        enrollments = self.repo.get_enrollments(
            classroom_id, limit=limit, offset=offset
        )
        return [
            StudentOut(
                id=e.student.id,
                name=e.student.name,
                email=e.student.email,
                enrolled_at=e.enrolled_at,
                profile_image_url=e.student.profile_image_url,
            )
            for e in enrollments
        ]

    _CSV_MAX_ROWS = 2_000

    def import_students_from_csv(
        self, classroom_id: str, caller_id: str, file: IO
    ) -> ImportResult:
        # permission check
        self._require_owned(classroom_id, caller_id)
        reader = csv.DictReader(
            line.decode() if isinstance(line, bytes) else line for line in file
        )
        result = ImportResult()
        row_no = 0
        acct = AccountService(self.session)
        for row in reader:
            if row_no >= self._CSV_MAX_ROWS:
                raise ValidationError(
                    f"CSV must not exceed {self._CSV_MAX_ROWS} data rows"
                )
            row_no += 1
            email = (row.get("email") or "").strip()
            name = (row.get("name") or "").strip()
            password = (row.get("password") or "").strip()
            report = ImportRowReport(row_number=row_no, email=email or None, name=name)
            if not email:
                report.error = "missing_email"
                result.rows.append(report)
                result.skipped += 1
                continue
            try:
                user = acct.get_user_by_email(email)
                created = False
                if user is None:
                    # create with provided password or random one
                    pw = password if password else uuid.uuid4().hex[:12]
                    user = acct.create_user(
                        email=email, name=name or email, password_plain=pw
                    )
                    created = True
                    result.created += 1
                enrolled = False
                if not self.repo.is_enrolled(classroom_id, user.id):
                    self.repo.add_student(classroom_id, user.id)
                    enrolled = True
                    result.enrolled += 1
                else:
                    result.skipped += 1
                report.created = created
                report.enrolled = enrolled
            except Exception as exc:
                report.error = str(exc)
                result.skipped += 1
            result.rows.append(report)
        return result

    def create_invite(
        self, classroom_id: str, caller_id: str, data: InviteCreate
    ) -> InviteOut:
        classroom = self._require_owned(classroom_id, caller_id)
        code = uuid.uuid4().hex[:16]
        invite = self.repo.create_invite(
            classroom_id=classroom_id,
            code=code,
            created_by=caller_id,
            expires_at=data.expires_at,
            max_uses=data.max_uses,
        )
        return InviteOut(**invite.to_dict())

    def redeem_invite(self, code: str, student_id: str) -> InviteRedeemResult:
        invite = self.repo.get_invite_by_code(code)
        if invite is None:
            raise NotFoundError("Invite", code)
        # check expiration
        if invite.expires_at and invite.expires_at < datetime.utcnow():
            raise ValidationError("Invite expired")
        if invite.max_uses is not None and (invite.uses or 0) >= invite.max_uses:
            raise ValidationError("Invite uses exceeded")
        # enroll
        if self.repo.is_enrolled(invite.classroom_id, student_id):
            enrolled = False
        else:
            self.repo.add_student(invite.classroom_id, student_id)
            enrolled = True
        self.repo.increment_invite_use(invite.id)
        return InviteRedeemResult(student_id=student_id, enrolled=enrolled)

    def add_student(
        self, classroom_id: str, caller_id: str, email: str
    ) -> AddStudentResult:
        self._require_owned(classroom_id, caller_id)
        student = AccountService(self.session).get_user_by_email(email)
        if student is None:
            error = NotFoundError("User", email)
            error.message = f"User not found: {email}"
            raise error
        if self.repo.is_enrolled(classroom_id, student.id):
            raise ValidationError(
                "Student is already enrolled in this classroom", field="email"
            )
        self.repo.add_student(classroom_id, student.id)
        return AddStudentResult(
            student_id=student.id,
            student_name=student.name,
            student_email=student.email,
        )

    def remove_student(
        self, classroom_id: str, caller_id: str, student_id: str
    ) -> None:
        self._require_owned(classroom_id, caller_id)
        if not self.repo.is_enrolled(classroom_id, student_id):
            error = NotFoundError("Enrollment", student_id)
            error.message = "Student is not enrolled in this classroom"
            raise error
        self.repo.remove_student(classroom_id, student_id)

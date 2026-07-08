"""Classroom repository."""

from typing import List, Optional

from sqlalchemy import func

from data.models import Classroom, Enrollment, Invite
from data.repositories import BaseRepository
from learning.classrooms.schemas import ClassroomCreate


class ClassroomRepository(BaseRepository[Classroom]):
    """Repository for classroom operations."""

    def create(self, owner_id: str, data: ClassroomCreate) -> Classroom:
        classroom = Classroom(
            owner_id=owner_id,
            name=data.name,
            subject=data.subject,
            course=data.course,
            objectives=data.objectives,
            level=data.level,
            description=data.description,
        )
        self.session.add(classroom)
        self.session.commit()
        return classroom

    def get_by_owner(
        self, owner_id: str, limit: int = 100, offset: int = 0
    ) -> List[Classroom]:
        """Return owner's classrooms with student_count joined from enrollments."""
        rows = (
            self.session.query(
                Classroom, func.count(Enrollment.id).label("student_count")
            )
            .outerjoin(Enrollment, Enrollment.classroom_id == Classroom.id)
            .filter(Classroom.owner_id == owner_id)
            .group_by(Classroom.id)
            .order_by(Classroom.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        classrooms = []
        for classroom, student_count in rows:
            classroom.student_count = student_count
            classrooms.append(classroom)
        return classrooms

    def get_by_id(self, classroom_id: str) -> Optional[Classroom]:
        return (
            self.session.query(Classroom).filter(Classroom.id == classroom_id).first()
        )

    def delete(self, classroom_id: str) -> None:
        classroom = self.get_by_id(classroom_id)
        if classroom is None:
            return
        self.session.query(Enrollment).filter(
            Enrollment.classroom_id == classroom_id
        ).delete(synchronize_session=False)
        self.session.delete(classroom)
        self.session.commit()

    def add_student(self, classroom_id: str, student_id: str) -> Enrollment:
        enrollment = Enrollment(classroom_id=classroom_id, student_id=student_id)
        self.session.add(enrollment)
        self.session.commit()
        return enrollment

    def remove_student(self, classroom_id: str, student_id: str) -> None:
        self.session.query(Enrollment).filter(
            Enrollment.classroom_id == classroom_id,
            Enrollment.student_id == student_id,
        ).delete(synchronize_session=False)
        self.session.commit()

    def get_enrollments(
        self, classroom_id: str, limit: int = 100, offset: int = 0
    ) -> List[Enrollment]:
        return (
            self.session.query(Enrollment)
            .filter(Enrollment.classroom_id == classroom_id)
            .order_by(Enrollment.enrolled_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_enrolled_classrooms(
        self, student_id: str, limit: int = 100, offset: int = 0
    ) -> List[Classroom]:
        """Return classrooms the student is enrolled in, with student_count joined."""
        rows = (
            self.session.query(
                Classroom, func.count(Enrollment.id).label("student_count")
            )
            .join(Enrollment, Enrollment.classroom_id == Classroom.id)
            .filter(
                Classroom.id.in_(
                    self.session.query(Enrollment.classroom_id).filter(
                        Enrollment.student_id == student_id
                    )
                )
            )
            .group_by(Classroom.id)
            .order_by(Classroom.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        classrooms = []
        for classroom, student_count in rows:
            classroom.student_count = student_count
            classrooms.append(classroom)
        return classrooms

    def is_enrolled(self, classroom_id: str, student_id: str) -> bool:
        return (
            self.session.query(Enrollment)
            .filter(
                Enrollment.classroom_id == classroom_id,
                Enrollment.student_id == student_id,
            )
            .first()
            is not None
        )

    # Invite operations
    def create_invite(
        self,
        classroom_id: str,
        code: str,
        created_by: str,
        expires_at=None,
        max_uses=None,
        is_primary: bool = False,
    ) -> Invite:
        invite = Invite(
            classroom_id=classroom_id,
            code=code,
            created_by=created_by,
            expires_at=expires_at,
            max_uses=max_uses,
            is_primary=is_primary,
        )
        self.session.add(invite)
        self.session.commit()
        return invite

    def get_invite_by_code(self, code: str) -> Optional[Invite]:
        return self.session.query(Invite).filter(Invite.code == code).first()

    def get_primary_invite(self, classroom_id: str) -> Optional[Invite]:
        return (
            self.session.query(Invite)
            .filter(Invite.classroom_id == classroom_id, Invite.is_primary.is_(True))
            .first()
        )

    def increment_invite_use(self, invite_id: str) -> None:
        invite = self.session.query(Invite).filter(Invite.id == invite_id).first()
        if not invite:
            return
        invite.uses = (invite.uses or 0) + 1
        self.session.commit()

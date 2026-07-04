"""Resource repositories — data access only (SQLAlchemy, no business logic)."""

from typing import List

from data.models import AssignmentTemplate, ClassResource
from data.repositories import BaseRepository


class ClassResourceRepository(BaseRepository[ClassResource]):
    """Data access for class materials."""

    def list_for_classroom(self, classroom_id: str) -> List[ClassResource]:
        return (
            self.session.query(ClassResource)
            .filter(ClassResource.classroom_id == classroom_id)
            .order_by(ClassResource.created_at.desc())
            .all()
        )

    def list_for_classrooms(self, classroom_ids: List[str]) -> List[ClassResource]:
        if not classroom_ids:
            return []
        return (
            self.session.query(ClassResource)
            .filter(ClassResource.classroom_id.in_(classroom_ids))
            .order_by(ClassResource.created_at.desc())
            .all()
        )


class AssignmentTemplateRepository(BaseRepository[AssignmentTemplate]):
    """Data access for assignment templates (teacher-owned)."""

    def list_for_owner(self, owner_teacher_id: str) -> List[AssignmentTemplate]:
        return (
            self.session.query(AssignmentTemplate)
            .filter(AssignmentTemplate.owner_teacher_id == owner_teacher_id)
            .order_by(AssignmentTemplate.created_at.desc())
            .all()
        )

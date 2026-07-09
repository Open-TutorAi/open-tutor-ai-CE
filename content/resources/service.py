"""Resources service — business logic + authorization (no ORM directly).

Two kinds of thing live here, both metadata-only (blobs stay in `content/files`):
  • **class materials** — a file linked to a class; teachers manage, enrolled students read.
  • **assignment templates** — teacher-owned, reusable; creating an assignment from one is
    an E7 action delegated to the `assignments` context.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from content.files.service import FilesService
from content.resources.repository import (
    AssignmentTemplateRepository,
    ClassResourceRepository,
)
from data.models import (
    AssignmentTemplate,
    ClassResource,
    Classroom,
    Enrollment,
)
from learning.assignments.service import AssignmentsService
from learning.classrooms.repository import ClassroomRepository, EnrollmentRepository


class ResourcesService:
    """Service for class materials + assignment templates."""

    def __init__(self, session: Session):
        self.session = session
        self.materials = ClassResourceRepository(session, ClassResource)
        self.templates = AssignmentTemplateRepository(session, AssignmentTemplate)
        self.classrooms = ClassroomRepository(session, Classroom)
        self.enrollments = EnrollmentRepository(session, Enrollment)
        self.files = FilesService(session)
        # Create-from-template produces a real assignment in the E7 context.
        self.assignments = AssignmentsService(session)

    # ── access helpers ───────────────────────────────────────────────────────

    def _owned_class(self, classroom_id: str, teacher_id: str) -> Classroom:
        room = self.classrooms.get_by_id(classroom_id)
        if not room:
            raise NotFoundError("Classroom", classroom_id)
        if room.teacher_id != teacher_id:
            raise AuthorizationError("Not authorized for this classroom")
        return room

    def _readable_class(self, classroom_id: str, user_id: str) -> Classroom:
        """A class is readable by its teacher OR an enrolled student."""
        room = self.classrooms.get_by_id(classroom_id)
        if not room:
            raise NotFoundError("Classroom", classroom_id)
        if room.teacher_id == user_id:
            return room
        if self.enrollments.get(classroom_id, user_id):
            return room
        raise AuthorizationError("Not authorized for this classroom")

    def _material_dict(self, resource: ClassResource) -> Dict[str, Any]:
        """Material metadata enriched with the linked file's name/type/size."""
        file = self.files.get(resource.file_id)
        return {
            **resource.to_dict(),
            "filename": file.filename if file else None,
            "content_type": file.content_type if file else None,
            "size": file.size if file else None,
        }

    # ── class materials ──────────────────────────────────────────────────────

    def upload_material(
        self,
        classroom_id: str,
        teacher_id: str,
        filename: str,
        content_type: Optional[str],
        contents: bytes,
        title: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._owned_class(classroom_id, teacher_id)
        if not (isinstance(title, str) and title.strip()):
            raise ValidationError("title is required")
        # Blob storage is delegated to content/files (owned by the uploading teacher).
        file = self.files.upload(teacher_id, filename, content_type, contents)
        resource = self.materials.create(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            file_id=file.id,
            title=title.strip(),
            description=(
                description.strip() if description and description.strip() else None
            ),
            uploaded_by=teacher_id,
            created_at=datetime.utcnow(),
        )
        return self._material_dict(resource)

    def list_materials(self, classroom_id: str, user_id: str) -> List[Dict[str, Any]]:
        self._readable_class(classroom_id, user_id)
        return [
            self._material_dict(r)
            for r in self.materials.list_for_classroom(classroom_id)
        ]

    def _owned_material(self, classroom_id: str, rid: str) -> ClassResource:
        resource = self.materials.get_by_id(rid)
        if not resource or resource.classroom_id != classroom_id:
            raise NotFoundError("Resource", rid)
        return resource

    def read_material(
        self, classroom_id: str, rid: str, user_id: str
    ) -> Tuple[bytes, str, str]:
        """Return (bytes, content_type, filename) for download. Access-checked."""
        self._readable_class(classroom_id, user_id)
        resource = self._owned_material(classroom_id, rid)
        data, content_type = self.files.read_bytes(resource.file_id)
        file = self.files.get(resource.file_id)
        return data, content_type, (file.filename if file else "download")

    def delete_material(self, classroom_id: str, teacher_id: str, rid: str) -> None:
        self._owned_class(classroom_id, teacher_id)
        resource = self._owned_material(classroom_id, rid)
        # Remove the blob too (best-effort) then the metadata link.
        try:
            self.files.delete(resource.file_id, teacher_id)
        except (NotFoundError, AuthorizationError):
            pass
        self.materials.delete(rid)

    # ── flat library (across the teacher's classes) ──────────────────────────

    def list_library(self, teacher_id: str) -> Dict[str, Any]:
        rooms = self.classrooms.get_by_teacher(teacher_id)
        names = {r.id: r.name for r in rooms}
        materials = self.materials.list_for_classrooms(list(names.keys()))
        return {
            "materials": [
                {**self._material_dict(r), "class_name": names.get(r.classroom_id)}
                for r in materials
            ],
            "templates": [
                t.to_dict() for t in self.templates.list_for_owner(teacher_id)
            ],
        }

    # ── assignment templates (teacher-owned, reusable) ───────────────────────

    def list_templates(self, teacher_id: str) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.templates.list_for_owner(teacher_id)]

    def save_template(
        self,
        teacher_id: str,
        title: str,
        instructions: Optional[str] = None,
        attachment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not (isinstance(title, str) and title.strip()):
            raise ValidationError("title is required")
        template = self.templates.create(
            id=str(uuid.uuid4()),
            owner_teacher_id=teacher_id,
            title=title.strip(),
            instructions=(
                instructions.strip() if instructions and instructions.strip() else None
            ),
            attachment_id=(attachment_id or None),
            created_at=datetime.utcnow(),
        )
        return template.to_dict()

    def _owned_template(self, tid: str, teacher_id: str) -> AssignmentTemplate:
        template = self.templates.get_by_id(tid)
        if not template:
            raise NotFoundError("Template", tid)
        if template.owner_teacher_id != teacher_id:
            raise AuthorizationError("Not authorized for this template")
        return template

    def delete_template(self, tid: str, teacher_id: str) -> None:
        self._owned_template(tid, teacher_id)
        self.templates.delete(tid)

    def create_assignment_from_template(
        self,
        classroom_id: str,
        teacher_id: str,
        template_id: str,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pre-fill a new assignment from a template (delegates to the E7 context)."""
        self._owned_class(classroom_id, teacher_id)
        template = self._owned_template(template_id, teacher_id)
        return self.assignments.create(
            classroom_id,
            teacher_id,
            {
                "title": template.title,
                "instructions": template.instructions,
                "attachment_id": template.attachment_id,
                "due_date": due_date,
            },
        )

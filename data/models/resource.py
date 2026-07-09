"""Resource domain models — class materials + assignment templates.

Part of the `resources` bounded context. This context owns only metadata + links: the
actual file blob lives in the existing `content/files` domain (`FileRecord`). A
`ClassResource` is class-scoped (drives student access); an `AssignmentTemplate` is
teacher-owned and reusable across classes (feeds E7).
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from data.database import Base


class ClassResource(Base):
    __tablename__ = "class_resources"

    id = Column(String(36), primary_key=True)
    classroom_id = Column(
        String(36),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id = Column(String(36), nullable=False)  # → content/files (FileRecord)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "file_id": self.file_id,
            "title": self.title,
            "description": self.description,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AssignmentTemplate(Base):
    __tablename__ = "assignment_templates"

    id = Column(String(36), primary_key=True)
    owner_teacher_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    title = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    attachment_id = Column(String(36), nullable=True)  # → content/files (optional)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_teacher_id": self.owner_teacher_id,
            "title": self.title,
            "instructions": self.instructions,
            "attachment_id": self.attachment_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

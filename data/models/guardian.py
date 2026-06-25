"""Guardian link model — the parent↔student bond.

Part of the `guardians` bounded context. The bond is platform-wide (the future parent
portal reads the same links), which is why it lives here and not in `classrooms`.
A link is `pending` until the parent account accepts (then `parent_user_id` is set and
status becomes `active`).
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint

from data.database import Base


class GuardianLink(Base):
    __tablename__ = "guardian_links"
    __table_args__ = (
        UniqueConstraint(
            "student_user_id", "parent_user_id", name="uq_guardian_student_parent"
        ),
    )

    id = Column(String(36), primary_key=True)
    student_user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    # Null while the invited parent has no account yet (pending link).
    parent_user_id = Column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    invited_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_user_id": self.student_user_id,
            "parent_user_id": self.parent_user_id,
            "invited_email": self.invited_email,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

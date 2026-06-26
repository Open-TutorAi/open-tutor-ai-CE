import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from data.database import Base
 
 
class ParentStudentLink(Base):
    """Liaison entre un compte parent et un compte étudiant."""
 
    __tablename__ = "parent_student_links"
 
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    invitation_code = Column(String(10), nullable=True, unique=True, index=True)
    # active | pending | revoked
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
 
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "student_id": self.student_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
 
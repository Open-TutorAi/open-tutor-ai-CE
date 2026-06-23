import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from data.database import Base


class ErrorCard(Base):
    __tablename__ = "error_cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    support_id = Column(
        String,
        ForeignKey("supports.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    concept = Column(String(200), nullable=False)
    error_description = Column(Text, nullable=False)
    simple_explanation = Column(Text, nullable=False)
    correct_example = Column(Text, nullable=False)

    # Traçabilité : depuis quel échange la fiche a été générée
    source_user_message = Column(Text, nullable=True)
    source_assistant_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_error_cards_support_user", "support_id", "user_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "support_id": self.support_id,
            "user_id": self.user_id,
            "concept": self.concept,
            "error_description": self.error_description,
            "simple_explanation": self.simple_explanation,
            "correct_example": self.correct_example,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

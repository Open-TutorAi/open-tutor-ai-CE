"""Model configuration overlay model."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, String

from data.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(String(255), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    base_model_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    meta = Column(JSON, nullable=True)
    params = Column(JSON, nullable=True)
    access_control = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "base_model_id": self.base_model_id,
            "name": self.name,
            "meta": self.meta or {},
            "params": self.params or {},
            "access_control": self.access_control,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

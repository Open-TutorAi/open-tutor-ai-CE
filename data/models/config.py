"""Application config key-value store."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String

from data.database import Base


class AppConfig(Base):
    __tablename__ = "app_configs"

    key = Column(String(255), primary_key=True)
    value = Column(JSON, nullable=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

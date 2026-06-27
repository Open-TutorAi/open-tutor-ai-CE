"""User domain model."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from data.database import Base


class User(Base):
    """User model - independent from open_webui.models.users.Users."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    profile_image_url = Column(String(255), nullable=True)
    settings = Column(JSON, nullable=True)
    info = Column(JSON, nullable=True)
    role = Column(String(50), nullable=True, default="user")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    supports = relationship("Support", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        import time as _time

        created_ts = (
            int(self.created_at.timestamp()) if self.created_at else int(_time.time())
        )
        updated_ts = int(self.updated_at.timestamp()) if self.updated_at else created_ts
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "profile_image_url": self.profile_image_url or "/user.png",
            "role": self.role or "user",
            "settings": self.settings,
            "info": self.info,
            "created_at": created_ts,
            "updated_at": updated_ts,
            "last_active_at": updated_ts,
            "oauth_sub": None,
        }

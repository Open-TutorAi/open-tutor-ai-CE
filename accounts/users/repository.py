"""User repository for the accounts domain."""

from typing import Any, Dict, List, Optional

from data.models import User
from data.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def get_active_users(self) -> list[User]:
        return self.session.query(User).filter(User.is_active.is_(True)).all()

    def count(self) -> int:
        return self.session.query(User).count()

    def get_all(self, skip: int = 0, limit: int = 500) -> List[User]:
        return self.session.query(User).offset(skip).limit(limit).all()

    def search(self, query: str) -> List[User]:
        q = f"%{query}%"
        return (
            self.session.query(User)
            .filter((User.name.ilike(q)) | (User.email.ilike(q)))
            .all()
        )

    def update_settings(self, user_id: str, settings: Dict[str, Any]) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.settings = settings
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_info(self, user_id: str, info: Dict[str, Any]) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.info = info
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_role(self, user_id: str, role: str) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.is_admin = role == "admin"
        user.role = role
        self.session.commit()
        self.session.refresh(user)
        return user

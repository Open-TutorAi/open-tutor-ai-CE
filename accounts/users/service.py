"""Account service for users and authentication."""

import uuid
from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from common.exceptions import NotFoundError
from data.models import User
from accounts.users.repository import UserRepository

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AccountService:
    """Service for account and user operations."""

    def __init__(self, session: Session):
        self.repo = UserRepository(session, User)

    def get_user(self, user_id: str) -> Optional[User]:
        return self.repo.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.repo.get_by_email(email)

    def count_users(self) -> int:
        return self.repo.count()

    def create_user(
        self,
        email: str,
        name: str,
        password_plain: str,
        profile_image_url: Optional[str] = None,
        is_admin: bool = False,
        role: str = "user",
    ) -> User:
        """Create a new user; first user is automatically admin."""
        if self.repo.get_by_email(email):
            raise ValueError("Email already registered")
        return self.repo.create(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            password_hash=_pwd_context.hash(password_plain),
            profile_image_url=profile_image_url,
            is_active=True,
            is_admin=is_admin,
            role="admin" if is_admin else role,
        )

    def authenticate(self, email: str, password_plain: str) -> Optional[User]:
        """Return user if credentials are valid, None otherwise."""
        user = self.repo.get_by_email(email)
        if not user:
            return None
        if not _pwd_context.verify(password_plain, user.password_hash):
            return None
        return user

    def list_users(self, skip: int = 0, limit: int = 500) -> List[User]:
        return self.repo.get_all(skip=skip, limit=limit)

    def search_users(self, query: str) -> List[User]:
        return self.repo.search(query)

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        try:
            return self.repo.update(user_id, **kwargs)
        except NotFoundError:
            return None

    def update_password(self, user_id: str, new_password: str) -> bool:
        hashed = _pwd_context.hash(new_password)
        try:
            self.repo.update(user_id, password_hash=hashed)
            return True
        except NotFoundError:
            return False

    def delete_user(self, user_id: str) -> bool:
        return self.repo.delete(user_id)

    def get_user_settings(self, user_id: str) -> dict:
        user = self.repo.get_by_id(user_id)
        stored = (user.settings or {}) if user else {}
        # Wrap bare dicts in {"ui": ...} so the UI's userSettings.ui is always defined
        if "ui" not in stored:
            return {"ui": stored}
        return stored

    def update_user_settings(self, user_id: str, settings: dict) -> dict:
        user = self.repo.update_settings(user_id, settings)
        return user.settings or {} if user else {}

    def get_user_info(self, user_id: str) -> dict:
        user = self.repo.get_by_id(user_id)
        return user.info or {} if user else {}

    def update_user_info(self, user_id: str, info: dict) -> dict:
        user = self.repo.update_info(user_id, info)
        return user.info or {} if user else {}

    def update_role(self, user_id: str, role: str) -> Optional[User]:
        return self.repo.update_role(user_id, role)

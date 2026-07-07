"""Base repository class with common CRUD operations."""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from common.exceptions import NotFoundError

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository for CRUD operations."""

    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def create(self, **kwargs) -> T:
        """Create new instance."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def get_by_id(self, id: str) -> Optional[T]:
        """Get instance by ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all instances with pagination."""
        return self.session.query(self.model).offset(skip).limit(limit).all()

    def update(self, id: str, **kwargs) -> T:
        """Update instance."""
        instance = self.get_by_id(id)
        if not instance:
            raise NotFoundError(self.model.__name__, id)
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, id: str) -> bool:
        """Delete instance."""
        instance = self.get_by_id(id)
        if not instance:
            return False
        self.session.delete(instance)
        self.session.commit()
        return True

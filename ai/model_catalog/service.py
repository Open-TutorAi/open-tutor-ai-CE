"""Model overlay service.

Base models come from providers (Ollama, OpenAI, Gemini) at runtime.
Custom model configs stored in DB overlay the base model list.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai.model_catalog.repository import ModelRepository
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import ModelConfig


class ModelsService:
    def __init__(self, session: Session):
        self.repo = ModelRepository(session, ModelConfig)

    def list_active(self) -> List[ModelConfig]:
        return self.repo.get_all_active()

    def list_base(self) -> List[dict]:
        """Base models from providers — stub; providers router populates at runtime."""
        return []

    def get(self, model_id: str) -> Optional[ModelConfig]:
        return self.repo.get_by_id(model_id)

    def create(self, user_id: str, data: Dict[str, Any]) -> ModelConfig:
        model_id = data.get("id")
        name = data.get("name")
        if not model_id:
            raise ValidationError("Model 'id' is required", field="id")
        if not name:
            raise ValidationError("Model 'name' is required", field="name")
        if self.repo.get_by_id(model_id):
            raise ValidationError(f"Model '{model_id}' already exists", field="id")
        try:
            return self.repo.create(
                id=model_id,
                user_id=user_id,
                base_model_id=data.get("base_model_id"),
                name=name,
                meta=data.get("meta", {}),
                params=data.get("params", {}),
                access_control=data.get("access_control"),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        except IntegrityError:
            self.repo.session.rollback()
            raise ValidationError(f"Model '{model_id}' already exists", field="id")

    def update(
        self, model_id: str, user_id: str, data: Dict[str, Any], is_admin: bool = False
    ) -> ModelConfig:
        model = self.repo.get_by_id(model_id)
        if not model:
            raise NotFoundError("ModelConfig", model_id)
        if model.user_id != user_id and not is_admin:
            raise AuthorizationError("You do not own this model")
        return self.repo.update(
            model_id,
            name=data.get("name", model.name),
            base_model_id=data.get("base_model_id", model.base_model_id),
            meta=data.get("meta", model.meta),
            params=data.get("params", model.params),
            access_control=data.get("access_control", model.access_control),
            updated_at=datetime.utcnow(),
        )

    def toggle(
        self, model_id: str, user_id: str, is_admin: bool = False
    ) -> ModelConfig:
        model = self.repo.get_by_id(model_id)
        if not model:
            raise NotFoundError("ModelConfig", model_id)
        if model.user_id != user_id and not is_admin:
            raise AuthorizationError("You do not own this model")
        toggled = self.repo.toggle(model_id)
        return toggled

    def delete(self, model_id: str, user_id: str, is_admin: bool = False) -> bool:
        model = self.repo.get_by_id(model_id)
        if not model:
            return False
        if model.user_id != user_id and not is_admin:
            raise AuthorizationError("You do not own this model")
        return self.repo.delete(model_id)

    def delete_all(self) -> int:
        return self.repo.delete_all()

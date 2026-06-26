"""Model config repository."""

from typing import List, Optional

from data.models import ModelConfig
from data.repositories import BaseRepository


class ModelRepository(BaseRepository[ModelConfig]):
    def get_all_active(self) -> List[ModelConfig]:
        return (
            self.session.query(ModelConfig)
            .filter(ModelConfig.is_active.is_(True))
            .all()
        )

    def get_all(self) -> List[ModelConfig]:
        return self.session.query(ModelConfig).all()

    def toggle(self, model_id: str) -> Optional[ModelConfig]:
        model = self.get_by_id(model_id)
        if not model:
            return None
        model.is_active = not model.is_active
        self.session.commit()
        self.session.refresh(model)
        return model

    def delete_all(self) -> int:
        count = self.session.query(ModelConfig).count()
        self.session.query(ModelConfig).delete()
        self.session.commit()
        return count

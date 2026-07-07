"""Images service — config + proxy to image generation provider."""

from sqlalchemy.orm import Session

from data.models.config import AppConfig

_KEY = "images_config"
_DEFAULTS = {
    "engine": "",
    "enabled": False,
    "url": "",
    "key": "",
    "image": {"model": "dall-e-3", "size": "1024x1024", "n": 1},
}


class ImagesService:
    def __init__(self, db: Session):
        self.db = db

    def _cfg(self) -> AppConfig:
        c = self.db.query(AppConfig).filter(AppConfig.key == _KEY).first()
        if not c:
            c = AppConfig(key=_KEY, value=_DEFAULTS.copy())
            self.db.add(c)
            self.db.commit()
            self.db.refresh(c)
        return c

    def get_config(self) -> dict:
        return self._cfg().value or _DEFAULTS.copy()

    def update_config(self, data: dict) -> dict:
        c = self._cfg()
        current = dict(c.value or _DEFAULTS)
        current.update({k: v for k, v in data.items() if v is not None})
        c.value = current
        self.db.commit()
        return current

    def get_image_config(self) -> dict:
        return self.get_config().get("image", _DEFAULTS["image"])

    def update_image_config(self, data: dict) -> dict:
        c = self._cfg()
        current = dict(c.value or _DEFAULTS)
        current.setdefault("image", _DEFAULTS["image"].copy())
        current["image"].update({k: v for k, v in data.items() if v is not None})
        c.value = current
        self.db.commit()
        return current["image"]

    def get_models(self) -> list:
        return [
            {"id": "dall-e-3", "name": "DALL-E 3"},
            {"id": "dall-e-2", "name": "DALL-E 2"},
        ]

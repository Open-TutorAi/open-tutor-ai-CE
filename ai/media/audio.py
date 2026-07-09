"""Audio service — config + proxy to TTS/STT provider."""

from sqlalchemy.orm import Session

from data.models.config import AppConfig

_KEY = "audio_config"
# Flat schema matching the UI's OpenAIConfigForm: {url, key, model, speaker}
_DEFAULTS = {
    "url": "",
    "key": "",
    "model": "tts-1",
    "speaker": "alloy",
}


class AudioService:
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

    def get_models(self) -> list:
        return [
            {"id": "tts-1", "name": "TTS-1"},
            {"id": "tts-1-hd", "name": "TTS-1 HD"},
        ]

    def get_voices(self) -> list:
        return [
            {"id": "alloy"},
            {"id": "echo"},
            {"id": "fable"},
            {"id": "onyx"},
            {"id": "nova"},
            {"id": "shimmer"},
        ]

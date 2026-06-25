"""AppConfig-backed provider configuration store."""

import os
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ai.providers.profiles import REGISTRY
from data.models import AppConfig

_OPENAI_KEY = "provider_openai_config"
_OLLAMA_KEY = "provider_ollama_config"


def _default_openai() -> Dict[str, Any]:
    return {
        "ENABLE_OPENAI_API": True,
        "OPENAI_API_BASE_URLS": list(REGISTRY["openai"].default_base_urls),
        "OPENAI_API_KEYS": [os.getenv("OPENAI_API_KEY", "")],
        "OPENAI_API_CONFIGS": {},
    }


def _default_ollama() -> Dict[str, Any]:
    return {
        "ENABLE_OLLAMA_API": True,
        "OLLAMA_BASE_URLS": list(REGISTRY["ollama"].default_base_urls),
        "OLLAMA_API_CONFIGS": {},
    }


class ProviderConfigService:
    """Reads/writes provider config to the AppConfig KV store."""

    def __init__(self, session: Session):
        self.session = session

    def _get(self, key: str, default_factory) -> Dict[str, Any]:
        rec = self.session.query(AppConfig).filter(AppConfig.key == key).first()
        if rec and rec.value:
            merged = default_factory()
            merged.update(rec.value)
            return merged
        return default_factory()

    def _set(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        rec = self.session.query(AppConfig).filter(AppConfig.key == key).first()
        if rec:
            rec.value = value
        else:
            rec = AppConfig(key=key, value=value)
            self.session.add(rec)
        self.session.commit()
        return value

    # ── OpenAI ────────────────────────────────────────────────────────────
    def get_openai(self) -> Dict[str, Any]:
        return self._get(_OPENAI_KEY, _default_openai)

    def set_openai(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.get_openai()
        cfg.update({k: v for k, v in data.items() if k in _default_openai()})
        return self._set(_OPENAI_KEY, cfg)

    def set_openai_urls(self, urls: List[str]) -> Dict[str, Any]:
        cfg = self.get_openai()
        cfg["OPENAI_API_BASE_URLS"] = list(urls)
        return self._set(_OPENAI_KEY, cfg)

    def set_openai_keys(self, keys: List[str]) -> Dict[str, Any]:
        cfg = self.get_openai()
        cfg["OPENAI_API_KEYS"] = list(keys)
        return self._set(_OPENAI_KEY, cfg)

    # ── Ollama ────────────────────────────────────────────────────────────
    def get_ollama(self) -> Dict[str, Any]:
        return self._get(_OLLAMA_KEY, _default_ollama)

    def set_ollama(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.get_ollama()
        cfg.update({k: v for k, v in data.items() if k in _default_ollama()})
        return self._set(_OLLAMA_KEY, cfg)

    def set_ollama_urls(self, urls: List[str]) -> Dict[str, Any]:
        cfg = self.get_ollama()
        cfg["OLLAMA_BASE_URLS"] = list(urls)
        return self._set(_OLLAMA_KEY, cfg)

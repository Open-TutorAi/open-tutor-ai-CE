"""Retrieval service — config stored in AppConfig KV."""

from sqlalchemy.orm import Session

from data.models.config import AppConfig

_CONFIG_KEY = "retrieval_config"

_DEFAULTS = {
    "pdf_extract_images": False,
    "enable_google_drive_integration": False,
    "web_loader_ssl_verification": True,
    "chunk": {
        "chunk_size": 1000,
        "chunk_overlap": 100,
    },
    "content_extraction": {
        "engine": "",
        "tika_server_url": None,
    },
    "youtube": {
        "language": ["en"],
        "translation": None,
        "proxy_url": "",
    },
    "query": {
        "k": 5,
        "r": 0.0,
        "template": None,
        "hybrid": False,
    },
    "embedding": {
        "embedding_engine": "",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_batch_size": 1,
        "openai_config": None,
    },
    "reranking": {
        "reranking_model": "",
        "enabled": False,
    },
}


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def _get_config_record(self) -> AppConfig:
        cfg = self.db.query(AppConfig).filter(AppConfig.key == _CONFIG_KEY).first()
        if not cfg:
            cfg = AppConfig(key=_CONFIG_KEY, value=_DEFAULTS.copy())
            self.db.add(cfg)
            self.db.commit()
            self.db.refresh(cfg)
        return cfg

    def get_config(self) -> dict:
        return self._get_config_record().value or _DEFAULTS.copy()

    def update_config(self, data: dict) -> dict:
        cfg = self._get_config_record()
        current = dict(cfg.value or _DEFAULTS)
        # Top-level scalar fields
        for key in (
            "pdf_extract_images",
            "enable_google_drive_integration",
            "web_loader_ssl_verification",
        ):
            if key in data:
                current[key] = data[key]
        # Nested objects — merge deeply
        for key in ("chunk", "content_extraction", "youtube"):
            if key in data and isinstance(data[key], dict):
                current.setdefault(key, _DEFAULTS.get(key, {}).copy())
                current[key].update(
                    {k: v for k, v in data[key].items() if v is not None}
                )
        cfg.value = current
        self.db.commit()
        return current

    def get_template(self) -> str:
        cfg = self.get_config()
        return cfg.get("query", {}).get("template") or "[context]\n\n[query]"

    def get_query_settings(self) -> dict:
        return self.get_config().get("query", _DEFAULTS["query"])

    def update_query_settings(self, data: dict) -> dict:
        cfg = self._get_config_record()
        current = dict(cfg.value or _DEFAULTS)
        current.setdefault("query", _DEFAULTS["query"].copy())
        current["query"].update({k: v for k, v in data.items() if v is not None})
        cfg.value = current
        self.db.commit()
        return current["query"]

    def get_embedding(self) -> dict:
        return self.get_config().get("embedding", _DEFAULTS["embedding"])

    def update_embedding(self, data: dict) -> dict:
        cfg = self._get_config_record()
        current = dict(cfg.value or _DEFAULTS)
        current.setdefault("embedding", _DEFAULTS["embedding"].copy())
        current["embedding"].update({k: v for k, v in data.items() if v is not None})
        cfg.value = current
        self.db.commit()
        return current["embedding"]

    def get_reranking(self) -> dict:
        return self.get_config().get("reranking", _DEFAULTS["reranking"])

    def update_reranking(self, data: dict) -> dict:
        cfg = self._get_config_record()
        current = dict(cfg.value or _DEFAULTS)
        current.setdefault("reranking", _DEFAULTS["reranking"].copy())
        current["reranking"].update({k: v for k, v in data.items() if v is not None})
        cfg.value = current
        self.db.commit()
        return current["reranking"]

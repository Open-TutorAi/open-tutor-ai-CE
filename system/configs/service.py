"""App config service — wraps AppConfig KV store."""

import copy
from typing import Any, Dict

from sqlalchemy.orm import Session

from data.models import AppConfig

# Default values for all config keys
_TUTOR_SYSTEM_PROMPT_DEFAULT = (
    "You are a highly experienced educator, instructional designer, and tutor. "
    "You specialize in creating clear, engaging, and progressive step-by-step lessons "
    "for any topic and any academic level. You combine best practices in pedagogy "
    "(e.g., scaffolding, active recall, formative feedback) with adaptive teaching strategies. "
    "Your role is to guide the learner one concept at a time, combining effective teaching "
    "strategies, personalized communication style, and the most suitable reasoning method, "
    "in a way that is tailored to their needs, level, and learning goals."
)

_DEFAULTS: Dict[str, Any] = {
    "banners": [],
    "suggestions": [],
    "models": {"DEFAULT_MODELS": "", "MODEL_ORDER_LIST": []},
    "code_execution": {"enabled": False},
    "direct_connections": {"enabled": False},
    "tutor_system_prompt": _TUTOR_SYSTEM_PROMPT_DEFAULT,
}


class ConfigsService:
    def __init__(self, session: Session):
        self.session = session

    def get(self, key: str) -> Any:
        record = self.session.query(AppConfig).filter(AppConfig.key == key).first()
        if record:
            return record.value
        return copy.deepcopy(_DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> Any:
        record = self.session.query(AppConfig).filter(AppConfig.key == key).first()
        if record:
            record.value = value
        else:
            record = AppConfig(key=key, value=value)
            self.session.add(record)
        self.session.commit()
        return value

    def export_all(self) -> Dict[str, Any]:
        rows = self.session.query(AppConfig).all()
        result = copy.deepcopy(_DEFAULTS)
        result.update({r.key: r.value for r in rows})
        return result

    def import_all(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if key not in _DEFAULTS:
                continue  # ignore unknown keys
            self.set(key, value)

"""Declarative provider profiles — Hermes-style single source of provider identity."""

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ProviderProfile:
    """Describes one inference provider. Declarative — no client construction here."""

    name: str
    display_name: str
    default_base_urls: tuple = ()
    # transport: all our providers speak the OpenAI-compatible chat protocol.
    # Ollama also exposes a native API used only by the model-management adapter.
    transport: str = "openai_chat"


def _env_list(var: str, fallback: str) -> List[str]:
    raw = os.getenv(var, "").strip()
    if raw:
        return [u.strip() for u in raw.split(",") if u.strip()]
    return [fallback]


REGISTRY: Dict[str, ProviderProfile] = {
    "openai": ProviderProfile(
        name="openai",
        display_name="OpenAI-Compatible",
        default_base_urls=tuple(
            _env_list("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        ),
        transport="openai_chat",
    ),
    "ollama": ProviderProfile(
        name="ollama",
        display_name="Ollama",
        default_base_urls=tuple(_env_list("OLLAMA_BASE_URL", "http://localhost:11434")),
        transport="openai_chat",
    ),
}

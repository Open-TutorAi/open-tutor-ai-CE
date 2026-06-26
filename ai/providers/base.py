# providers/base.py
"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Provider(ABC):
    """Base provider interface."""

    name: str

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure provider with settings."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass

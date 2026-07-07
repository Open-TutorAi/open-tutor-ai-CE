# providers/registry.py
"""Provider registry for managing available providers."""

from typing import Dict, Optional, Type

from ai.providers.base import Provider


class ProviderRegistry:
    """Registry for managing providers."""

    def __init__(self):
        self._providers: Dict[str, Type[Provider]] = {}

    def register(self, name: str, provider_class: Type[Provider]) -> None:
        """Register a provider."""
        self._providers[name] = provider_class

    def get(self, name: str) -> Optional[Type[Provider]]:
        """Get a provider by name."""
        return self._providers.get(name)

    def list_available(self) -> list[str]:
        """List all registered providers."""
        return list(self._providers.keys())


# Global registry instance
registry = ProviderRegistry()

"""Base transport for LLM providers."""

from abc import ABC, abstractmethod

from ai.llm.schemas import LLMRequest, LLMResponse


class LLMTransport(ABC):
    """Abstract base for LLM transport implementations."""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request to LLM provider."""
        pass

"""LLM request/response schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    """Chat message."""

    role: str  # user, assistant, system
    content: str


class LLMRequest(BaseModel):
    """LLM completion request."""

    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None


class LLMResponse(BaseModel):
    """LLM completion response."""

    model: str
    completion: str
    stop_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None

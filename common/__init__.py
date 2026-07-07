"""Common utilities and shared exceptions for OpenTutorAI.

This module provides:
- Exception hierarchy for domain-specific error handling
- Logging configuration utilities

Exceptions should be raised with appropriate error codes and messages
that can be transformed into API responses. The logging utilities provide
consistent formatting across all application modules.
"""

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    FileOperationError,
    NotFoundError,
    TutorAIException,
    ValidationError,
)
from .logging import get_logger

__all__ = [
    "TutorAIException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "DatabaseError",
    "FileOperationError",
    "get_logger",
]

# common/logging.py
"""Logging configuration."""

import logging
from typing import Optional

from config import settings

# Cache configured loggers to avoid repeated handler setup
_configured_loggers = {}


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (defaults to root logger if None or empty)

    Returns:
        Configured logging.Logger instance

    Raises:
        ValueError: If logger name is invalid
    """
    if name is None:
        name = ""

    # Validate name
    if not isinstance(name, str):
        raise ValueError(f"Logger name must be a string, got {type(name)}")

    # Return cached logger if already configured
    if name in _configured_loggers:
        return _configured_loggers[name]

    try:
        logger = logging.getLogger(name)

        # Only configure if no handlers already attached
        if not logger.handlers:
            logger.setLevel(settings.LOG_LEVEL)

            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # Prevent propagation to root logger to avoid duplicate messages
            if name:  # Only set for named loggers, not root logger
                logger.propagate = False

        _configured_loggers[name] = logger
        return logger

    except Exception as e:
        raise RuntimeError(f"Failed to configure logger '{name}': {str(e)}")

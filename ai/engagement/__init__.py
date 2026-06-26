"""Engagement domain — multimodal engagement analysis (text / audio / video).

Pure compute lives in ``text_core`` / ``audio_core`` / ``video_core`` /
``fusion``; ``cache`` holds short-lived runtime signals; ``service`` and
``repository`` provide the business-logic and persistence layers used by the
``/engagement`` HTTP router.
"""

from .service import EngagementService
from .repository import EngagementRepository

__all__ = ["EngagementService", "EngagementRepository"]

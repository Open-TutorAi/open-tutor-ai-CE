from .chat import Chat
from .config import AppConfig
from .feedback import Feedback
from .file import FileRecord
from .knowledge import KnowledgeBase, KnowledgeFile
from .model import ModelConfig
from .support import Support, SupportFile
from .user import User
from .message import (
    ParentStudent,
    TeacherStudent,
    ParentTeacherConversation,
    ParentTeacherMessage,
)
from .attachment import MessageAttachment
from .availability import TeacherAvailability
from .announcement import Announcement, AnnouncementRead

__all__ = [
    "User",
    "Support",
    "SupportFile",
    "Feedback",
    "FileRecord",
    "Chat",
    "ModelConfig",
    "AppConfig",
    "KnowledgeBase",
    "KnowledgeFile",
    "ParentStudent",
    "TeacherStudent",
    "ParentTeacherConversation",
    "ParentTeacherMessage",
    "MessageAttachment",
    "TeacherAvailability",
    "Announcement",
    "AnnouncementRead",
]

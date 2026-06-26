from .user import User
from .support import Support, SupportFile
from .feedback import Feedback
from .file import FileRecord
from .chat import Chat
from .model import ModelConfig
from .config import AppConfig
from .knowledge import KnowledgeBase, KnowledgeFile
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

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from open_webui.internal.db import Base

PREFIX = "opentutorai_"


class ChatChannel(Base):
    __tablename__ = f"{PREFIX}chat_channel"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subtitle = Column(String, nullable=True)
    code = Column(String, nullable=True)
    members_count = Column(Integer, default=0)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ChatChannelMessage(Base):
    __tablename__ = f"{PREFIX}chat_channel_message"
    id = Column(String, primary_key=True, index=True)
    channel_id = Column(
        String,
        ForeignKey(f"{PREFIX}chat_channel.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    sender_role = Column(String, nullable=True)
    avatar_color = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    is_svg = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    channel = relationship("ChatChannel", backref="messages")

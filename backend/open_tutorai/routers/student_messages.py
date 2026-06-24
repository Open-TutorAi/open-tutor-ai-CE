from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

from open_webui.utils.auth import get_verified_user
from open_tutorai.models.database import Base
from open_tutorai.models.chat_channels import ChatChannel, ChatChannelMessage
from sqlalchemy.orm import sessionmaker
from open_webui.internal.db import engine

log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter()


def get_db_session():
    Session = sessionmaker(bind=engine)
    return Session()


# Models for request and response
class ChannelCreateRequest(BaseModel):
    name: str
    subtitle: Optional[str] = None
    code: Optional[str] = None


class ChannelResponse(BaseModel):
    id: str
    name: str
    subtitle: Optional[str] = None
    code: Optional[str] = None
    members_count: int
    created_by: str
    created_at: datetime
    unread: int = 0


class MessageCreateRequest(BaseModel):
    content: str
    is_svg: Optional[bool] = False


class MessageResponse(BaseModel):
    id: str
    channel_id: str
    sender_id: str
    sender_name: str
    sender_role: Optional[str] = None
    avatar_color: Optional[str] = None
    content: str
    is_svg: bool
    created_at: datetime
    time: str  # Formatted time for UI


@router.get("/channels", response_model=List[ChannelResponse])
async def get_channels(user=Depends(get_verified_user)):
    """Get all available channels"""
    try:
        session = get_db_session()
        try:
            channels = (
                session.query(ChatChannel).order_by(ChatChannel.created_at.desc()).all()
            )

            # Auto-seed mock channels if none exist (for demo purposes)
            if not channels:
                mock_channels = [
                    ChatChannel(
                        id=str(uuid.uuid4()),
                        name="Général - Cours Java",
                        subtitle="N'oubliez pas le TP de demain.",
                        members_count=45,
                        code="JAV-101",
                        created_by=user.id,
                        created_at=datetime.now(),
                    ),
                    ChatChannel(
                        id=str(uuid.uuid4()),
                        name="Projet Final - Web",
                        subtitle="Le cahier des charges est en ligne.",
                        members_count=12,
                        code="WEB-302",
                        created_by=user.id,
                        created_at=datetime.now(),
                    ),
                    ChatChannel(
                        id=str(uuid.uuid4()),
                        name="Algorithmique Avancée",
                        subtitle="Quelqu'un a compris le tri fusion ?",
                        members_count=30,
                        code="ALG-201",
                        created_by=user.id,
                        created_at=datetime.now(),
                    ),
                    ChatChannel(
                        id=str(uuid.uuid4()),
                        name="Base de Données SQL",
                        subtitle="La jointure externe est complexe.",
                        members_count=22,
                        code="BDD-105",
                        created_by=user.id,
                        created_at=datetime.now(),
                    ),
                    ChatChannel(
                        id=str(uuid.uuid4()),
                        name="Intelligence Artificielle",
                        subtitle="Nouveau papier sur les LLMs.",
                        members_count=15,
                        code="IA-404",
                        created_by=user.id,
                        created_at=datetime.now(),
                    ),
                ]
                session.add_all(mock_channels)
                session.commit()
                channels = mock_channels

            results = []
            for c in channels:
                results.append(
                    ChannelResponse(
                        id=c.id,
                        name=c.name,
                        subtitle=c.subtitle,
                        code=c.code,
                        members_count=c.members_count,
                        created_by=c.created_by,
                        created_at=c.created_at,
                        unread=0,
                    )
                )
            return results
        finally:
            session.close()
    except Exception as e:
        log.error(f"Error getting channels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")


@router.post("/channels", response_model=ChannelResponse)
async def create_channel(
    channel_data: ChannelCreateRequest, user=Depends(get_verified_user)
):
    """Create a new channel"""
    try:
        session = get_db_session()
        try:
            channel = ChatChannel(
                id=str(uuid.uuid4()),
                name=channel_data.name,
                subtitle=channel_data.subtitle,
                code=channel_data.code,
                members_count=1,
                created_by=user.id,
                created_at=datetime.now(),
            )
            session.add(channel)
            session.commit()

            return ChannelResponse(
                id=channel.id,
                name=channel.name,
                subtitle=channel.subtitle,
                code=channel.code,
                members_count=channel.members_count,
                created_by=channel.created_by,
                created_at=channel.created_at,
                unread=0,
            )
        finally:
            session.close()
    except Exception as e:
        log.error(f"Error creating channel: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create channel: {str(e)}"
        )


@router.get("/channels/{channel_id}/messages", response_model=List[MessageResponse])
async def get_channel_messages(channel_id: str, user=Depends(get_verified_user)):
    """Get all messages for a specific channel"""
    try:
        session = get_db_session()
        try:
            messages = (
                session.query(ChatChannelMessage)
                .filter(ChatChannelMessage.channel_id == channel_id)
                .order_by(ChatChannelMessage.created_at.asc())
                .all()
            )

            results = []
            for m in messages:
                results.append(
                    MessageResponse(
                        id=m.id,
                        channel_id=m.channel_id,
                        sender_id=m.sender_id,
                        sender_name=m.sender_name,
                        sender_role=m.sender_role,
                        avatar_color=m.avatar_color,
                        content=m.content,
                        is_svg=m.is_svg,
                        created_at=m.created_at,
                        time=m.created_at.strftime("%H:%M"),  # Format time for UI
                    )
                )
            return results
        finally:
            session.close()
    except Exception as e:
        log.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post("/channels/{channel_id}/messages", response_model=MessageResponse)
async def create_channel_message(
    channel_id: str, message_data: MessageCreateRequest, user=Depends(get_verified_user)
):
    """Post a message to a channel"""
    try:
        session = get_db_session()
        try:
            # Check if channel exists
            channel = (
                session.query(ChatChannel).filter(ChatChannel.id == channel_id).first()
            )
            if not channel:
                raise HTTPException(status_code=404, detail="Channel not found")

            # Determine colors and roles (simplified logic based on user role)
            # In OpenWebUI, user role is user.role. We'll map "admin" to "ENSEIGNANT", others to ""
            sender_role = "ENSEIGNANT" if user.role in ["admin", "teacher"] else ""
            avatar_color = (
                "bg-[#0084FF] text-white"
                if user.role in ["admin", "teacher"]
                else "bg-[#9333EA] text-white"
            )

            message = ChatChannelMessage(
                id=str(uuid.uuid4()),
                channel_id=channel_id,
                sender_id=user.id,
                sender_name=user.name,
                sender_role=sender_role,
                avatar_color=avatar_color,
                content=message_data.content,
                is_svg=message_data.is_svg,
                created_at=datetime.now(),
            )
            session.add(message)
            session.commit()

            return MessageResponse(
                id=message.id,
                channel_id=message.channel_id,
                sender_id=message.sender_id,
                sender_name=message.sender_name,
                sender_role=message.sender_role,
                avatar_color=message.avatar_color,
                content=message.content,
                is_svg=message.is_svg,
                created_at=message.created_at,
                time=message.created_at.strftime("%H:%M"),
            )
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error creating message: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create message: {str(e)}"
        )

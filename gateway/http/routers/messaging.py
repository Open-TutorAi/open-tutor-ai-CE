"""Messaging router — teacher ↔ student 1:1 conversations.

Open to any authenticated user (`get_current_user`); the service enforces the relationship
(teacher ↔ enrolled student) for *starting* a conversation and participation for read/send.
New messages are delivered live over the existing Socket.IO layer (`message:new`).
"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import User
from gateway.http.attachments import attachment_response
from gateway.http.dependencies import (
    Pagination,
    get_current_user,
    get_messaging_service,
    pagination,
)
from gateway.http.errors import http_from_domain as _http_from_domain
from learning.messaging.service import MessagingService

router = APIRouter(prefix="/conversations", tags=["messaging"])


class StartRequest(BaseModel):
    recipient_id: str = Field(..., min_length=1, max_length=64)


class SendRequest(BaseModel):
    body: Optional[str] = Field("", max_length=10000)
    attachment_id: Optional[str] = Field(None, max_length=64)


@router.get("")
def list_conversations(
    current_user: User = Depends(get_current_user),
    svc: MessagingService = Depends(get_messaging_service),
    page: Pagination = Depends(pagination),
):
    return page.apply(svc.list_conversations(current_user.id))


@router.post("", status_code=status.HTTP_201_CREATED)
def start_conversation(
    data: StartRequest,
    current_user: User = Depends(get_current_user),
    svc: MessagingService = Depends(get_messaging_service),
):
    try:
        return svc.start(current_user.id, data.recipient_id)
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    svc: MessagingService = Depends(get_messaging_service),
):
    # Returns a {conversation, messages} envelope (not a bare list), so it isn't sliced
    # here; the message list is already bounded by a single conversation.
    try:
        return svc.get_messages(conversation_id, current_user.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    data: SendRequest,
    current_user: User = Depends(get_current_user),
    svc: MessagingService = Depends(get_messaging_service),
):
    from gateway.realtime.socket import emit_message_new, is_user_online

    try:
        result = svc.send_message(
            conversation_id, current_user.id, data.body, data.attachment_id
        )
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)
    payload = {"conversation_id": conversation_id, "message": result["message"]}
    for recipient_id in result["recipients"]:
        if is_user_online(recipient_id):
            await emit_message_new(recipient_id, payload)
    return result["message"]


@router.get("/{conversation_id}/messages/{message_id}/attachment")
def download_message_attachment(
    conversation_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    svc: MessagingService = Depends(get_messaging_service),
):
    """Download a message's attachment (any participant of the conversation)."""
    try:
        data, content_type, filename = svc.read_message_attachment(
            conversation_id, message_id, current_user.id
        )
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return attachment_response(data, content_type, filename)

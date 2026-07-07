"""Channels router — /api/v1/channels/* matching channels/index.ts UI client."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("/")
def list_channels(user: User = Depends(get_current_user)):
    return []


@router.post("/create")
def create_channel(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {**body, "id": "", "user_id": user.id}


@router.get("/{channel_id}")
def get_channel(channel_id: str, user: User = Depends(get_current_user)):
    return None


@router.post("/{channel_id}/update")
def update_channel(
    channel_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "id": channel_id}


@router.delete("/{channel_id}/delete")
def delete_channel(channel_id: str, user: User = Depends(get_current_user)):
    return {"id": channel_id}


@router.get("/{channel_id}/messages")
def get_messages(
    channel_id: str,
    skip: int = Query(0),
    limit: int = Query(50),
    user: User = Depends(get_current_user),
):
    return []


@router.post("/{channel_id}/messages/post")
def post_message(
    channel_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "id": "", "channel_id": channel_id, "user_id": user.id}


@router.get("/{channel_id}/messages/{message_id}/thread")
def get_message_thread(
    channel_id: str,
    message_id: str,
    skip: int = Query(0),
    limit: int = Query(50),
    user: User = Depends(get_current_user),
):
    return []


@router.post("/{channel_id}/messages/{message_id}/update")
def update_message(
    channel_id: str,
    message_id: str,
    body: Dict[str, Any],
    user: User = Depends(get_current_user),
):
    return {**body, "id": message_id}


@router.delete("/{channel_id}/messages/{message_id}/delete")
def delete_message(
    channel_id: str, message_id: str, user: User = Depends(get_current_user)
):
    return {"id": message_id}


@router.post("/{channel_id}/messages/{message_id}/reactions/add")
def add_reaction(
    channel_id: str,
    message_id: str,
    body: Dict[str, Any],
    user: User = Depends(get_current_user),
):
    return body


@router.post("/{channel_id}/messages/{message_id}/reactions/remove")
def remove_reaction(
    channel_id: str,
    message_id: str,
    body: Dict[str, Any],
    user: User = Depends(get_current_user),
):
    return body

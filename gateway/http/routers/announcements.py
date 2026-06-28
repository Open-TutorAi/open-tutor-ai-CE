"""Announcements router — /announcements/* for classroom announcements."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import User
from gateway.http.dependencies import get_announcements_service, get_current_user
from learning.announcements.service import AnnouncementsService

router = APIRouter(prefix="/announcements", tags=["announcements"])


class CreateAnnouncementRequest(BaseModel):
    title: str
    content: str
    priority: str = "normal"
    target_type: str = "all"


class UpdateAnnouncementRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    target_type: Optional[str] = None


# ── Teacher endpoints ─────────────────────────────────────────────────────────


@router.get("/mine")
async def list_my_announcements(
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> List[Dict[str, Any]]:
    try:
        return svc.list_for_teacher(current_user)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.post("")
async def create_announcement(
    body: CreateAnnouncementRequest,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> Dict[str, Any]:
    try:
        return svc.create(
            current_user, body.title, body.content, body.priority, body.target_type
        )
    except (AuthorizationError, ValidationError) as exc:
        code = (
            status.HTTP_403_FORBIDDEN
            if isinstance(exc, AuthorizationError)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=exc.message)


@router.patch("/{announcement_id}")
async def update_announcement(
    announcement_id: str,
    body: UpdateAnnouncementRequest,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> Dict[str, Any]:
    try:
        return svc.update(
            current_user,
            announcement_id,
            body.title,
            body.content,
            body.priority,
            body.target_type,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.post("/{announcement_id}/publish")
async def publish_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> Dict[str, Any]:
    try:
        return svc.publish(current_user, announcement_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.post("/{announcement_id}/unpublish")
async def unpublish_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> Dict[str, Any]:
    try:
        return svc.unpublish(current_user, announcement_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> Dict[str, Any]:
    try:
        return svc.delete(current_user, announcement_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


# ── Parent endpoints ──────────────────────────────────────────────────────────


@router.get("")
async def list_published_announcements(
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> List[Dict[str, Any]]:
    return svc.list_published(current_user)


@router.post("/{announcement_id}/read")
async def mark_announcement_read(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> Dict[str, Any]:
    try:
        return svc.mark_read(current_user, announcement_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
) -> Dict[str, Any]:
    return {"unread_count": svc.count_unread(current_user)}

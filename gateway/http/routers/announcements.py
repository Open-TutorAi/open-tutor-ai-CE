"""Classroom announcements (stream) router — /api/classrooms/{id}/announcements."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from learning.announcements.schemas import AnnouncementOut
from learning.announcements.service import AnnouncementsService

router = APIRouter(tags=["announcements"])


def get_announcements_service(db: Session = Depends(get_db)) -> AnnouncementsService:
    return AnnouncementsService(db)


class CreateAnnouncementRequest(BaseModel):
    content: str


@router.post(
    "/api/classrooms/{classroom_id}/announcements",
    response_model=AnnouncementOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_announcement(
    classroom_id: str,
    body: CreateAnnouncementRequest,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
):
    try:
        return svc.create_announcement(classroom_id, current_user.id, body.content)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/api/classrooms/{classroom_id}/announcements",
    response_model=List[AnnouncementOut],
)
async def list_announcements(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
):
    try:
        return svc.list_announcements(classroom_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/api/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    svc: AnnouncementsService = Depends(get_announcements_service),
):
    try:
        svc.delete_announcement(announcement_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return {"status": "deleted"}

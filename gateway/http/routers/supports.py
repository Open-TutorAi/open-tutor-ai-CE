"""Support router — /supports/* routes matching UI calls."""

from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from config import settings
from data.models import User
from gateway.http.dependencies import get_current_user, get_supports_service
from learning.supports.service import SupportsService

router = APIRouter(prefix="/supports", tags=["supports"])


class SupportCreateRequest(BaseModel):
    title: str
    short_description: Optional[str] = None
    subject: Optional[str] = None
    custom_subject: Optional[str] = None
    course_id: Optional[str] = None
    learning_objective: Optional[str] = None
    learning_type: Optional[str] = None
    level: Optional[str] = None
    content_language: Optional[str] = "English"
    estimated_duration: Optional[str] = None
    access_type: Optional[str] = "Private"
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    avatar_id: Optional[str] = None
    chat_id: Optional[str] = None


class SupportFileInfo(BaseModel):
    id: str
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class SupportResponse(BaseModel):
    id: str
    user_id: str
    title: str
    short_description: Optional[str] = None
    subject: Optional[str] = None
    custom_subject: Optional[str] = None
    course_id: Optional[str] = None
    learning_objective: Optional[str] = None
    learning_type: Optional[str] = None
    level: Optional[str] = None
    content_language: Optional[str] = None
    estimated_duration: Optional[str] = None
    access_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    avatar_id: Optional[str] = None
    chat_id: Optional[str] = None
    files: List[SupportFileInfo] = []
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _to_response(support, files=None) -> SupportResponse:
    return SupportResponse(
        id=support.id,
        user_id=support.user_id,
        title=support.title,
        short_description=support.short_description,
        subject=support.subject,
        custom_subject=support.custom_subject,
        course_id=support.course_id,
        learning_objective=support.learning_objective,
        learning_type=support.learning_type,
        level=support.level,
        content_language=support.content_language,
        estimated_duration=support.estimated_duration,
        access_type=support.access_type,
        keywords=support.keywords.split(",") if support.keywords else None,
        start_date=support.start_date,
        end_date=support.end_date,
        avatar_id=support.avatar_id,
        chat_id=support.chat_id,
        files=[
            SupportFileInfo(
                id=f.id,
                filename=f.filename,
                file_type=f.file_type,
                file_size=f.file_size,
            )
            for f in (files or [])
        ],
        status=support.status,
        created_at=support.created_at,
        updated_at=support.updated_at,
    )


@router.post("/create", response_model=SupportResponse)
async def create_support(
    data: SupportCreateRequest,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
):
    support = svc.create(current_user.id, data.model_dump())
    return _to_response(support)


@router.post("/upload-file")
async def upload_support_file(
    request: Request,
    support_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
):
    # 1. Ownership check — cheap DB query, zero I/O
    try:
        svc.verify_ownership(current_user.id, support_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    _too_large = HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
    )

    # 2. Fast rejection via Content-Length header before any network read
    raw_cl = request.headers.get("content-length")
    if raw_cl and raw_cl.isdigit() and int(raw_cl) > max_bytes:
        raise _too_large

    # 3. Chunked read — reject as soon as running total exceeds the limit
    contents = b""
    async for chunk in file:
        contents += chunk
        if len(contents) > max_bytes:
            raise _too_large

    # 4. Delegate write + persist (service re-validates as defense-in-depth)
    try:
        record = svc.upload_file(
            user_id=current_user.id,
            support_id=support_id,
            filename=file.filename or "",
            content_type=file.content_type,
            contents=contents,
            upload_dir=settings.UPLOAD_DIR,
            max_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        )
    except (NotFoundError, AuthorizationError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except ValidationError:
        raise _too_large
    return {"id": record.id, "filename": record.filename, "status": "success"}


@router.get("/list", response_model=List[SupportResponse])
async def list_supports(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
):
    return [_to_response(s) for s in svc.list_for_user(current_user.id, status)]


@router.get("/{support_id}", response_model=SupportResponse)
async def get_support(
    support_id: str,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
):
    support = svc.get(support_id)
    if not support:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Support not found"
        )
    if support.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    files = svc.repo.get_files(support_id)
    return _to_response(support, files=files)


@router.patch("/{support_id}/update-chat")
async def update_chat_id(
    support_id: str,
    chat_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
):
    if not chat_id:
        raise HTTPException(
            status_code=400, detail="chat_id query parameter is required"
        )
    support = svc.get(support_id)
    if not support or support.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Support not found"
        )
    updated = svc.update_chat_id(support_id, chat_id)
    return {"id": updated.id, "chat_id": updated.chat_id, "status": "success"}


@router.patch("/{support_id}", response_model=SupportResponse)
async def update_support(
    support_id: str,
    data: SupportCreateRequest,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
):
    support = svc.get(support_id)
    if not support or support.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Support not found"
        )
    updated = svc.update(support_id, data.model_dump())
    return _to_response(updated)


@router.delete("/{support_id}")
async def delete_support(
    support_id: str,
    current_user: User = Depends(get_current_user),
    svc: SupportsService = Depends(get_supports_service),
):
    support = svc.get(support_id)
    if not support or support.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Support not found"
        )
    svc.delete(support_id)
    return JSONResponse(content={"status": "success", "message": "Support deleted"})

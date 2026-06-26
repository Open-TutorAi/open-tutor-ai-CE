"""Messages router — /messages/* for parent-teacher messaging."""

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import User
from gateway.http.dependencies import get_current_user, get_messages_service
from learning.messages.service import MessagesService

router = APIRouter(prefix="/messages", tags=["messages"])


class SendMessageRequest(BaseModel):
    receiver_id: str
    student_id: str
    content: str
    attachment_ids: Optional[List[str]] = None


class LinkParentStudentRequest(BaseModel):
    parent_id: str
    student_id: str


class LinkTeacherStudentRequest(BaseModel):
    teacher_id: str
    student_id: str


@router.get("/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> List[Dict[str, Any]]:
    try:
        return svc.get_conversations(current_user)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.get("/conversations/{conversation_id}")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> List[Dict[str, Any]]:
    try:
        return svc.get_messages(current_user, conversation_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.post("/send")
async def send_message(
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> Dict[str, Any]:
    try:
        msg = svc.send_message(
            current_user,
            body.receiver_id,
            body.student_id,
            body.content,
            body.attachment_ids,
        )
        return {"message_id": msg["id"], "status": "sent", "message": msg}
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.get("/teachers/{student_id}")
async def get_teachers_of_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> List[Dict[str, Any]]:
    if current_user.role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Parents only"
        )
    try:
        return svc.get_teachers_of_child(current_user, student_id)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.get("/my-children-teachers")
async def get_all_children_teachers(
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> List[Dict[str, Any]]:
    if current_user.role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Parents only"
        )
    return svc.get_all_children_teachers(current_user)


@router.patch("/{message_id}/read")
async def mark_message_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> Dict[str, Any]:
    try:
        return svc.mark_message_read(current_user, message_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


# ── Attachment endpoints ───────────────────────────────────────────────────────


@router.post("/conversations/{conversation_id}/attachments")
async def upload_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> Dict[str, Any]:
    try:
        file_bytes = await file.read()
        return svc.upload_attachment(
            current_user=current_user,
            conversation_id=conversation_id,
            filename=file.filename or "upload",
            content_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        )
    except (NotFoundError, AuthorizationError) as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if isinstance(exc, NotFoundError)
            else status.HTTP_403_FORBIDDEN
        )
        raise HTTPException(status_code=code, detail=exc.message)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> FileResponse:
    try:
        att = svc.get_attachment(current_user, attachment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)

    # att_dict has no file_path; fetch the raw record through the repo
    raw = svc.repo.get_attachment(attachment_id)
    if not raw or not os.path.exists(raw.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk"
        )
    return FileResponse(
        path=raw.file_path,
        media_type=raw.mime_type,
        filename=raw.original_filename,
    )


# ── Admin endpoints for linking ───────────────────────────────────────────────


@router.post("/admin/link-parent-student")
async def link_parent_student(
    body: LinkParentStudentRequest,
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> Dict[str, Any]:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin only"
        )
    return svc.link_parent_student(body.parent_id, body.student_id)


@router.post("/admin/link-teacher-student")
async def link_teacher_student(
    body: LinkTeacherStudentRequest,
    current_user: User = Depends(get_current_user),
    svc: MessagesService = Depends(get_messages_service),
) -> Dict[str, Any]:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin only"
        )
    return svc.link_teacher_student(body.teacher_id, body.student_id)

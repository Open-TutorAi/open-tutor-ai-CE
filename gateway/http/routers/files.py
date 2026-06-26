"""Files router — /files/* routes matching ui/src/lib/apis/files/index.ts."""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from config import settings
from content.files.service import FilesService
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/files", tags=["files"])


def get_files_service(db: Session = Depends(get_db)) -> FilesService:
    return FilesService(db)


# ── Upload ────────────────────────────────────────────────────────────────────


@router.post("/")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: FilesService = Depends(get_files_service),
):
    """POST /api/v1/files/  ← uploadFile() in files/index.ts:8"""
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    _too_large = HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
    )
    raw_cl = request.headers.get("content-length")
    if raw_cl and raw_cl.isdigit() and int(raw_cl) > max_bytes:
        raise _too_large

    contents = b""
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        contents += chunk
        if len(contents) > max_bytes:
            raise _too_large

    try:
        record = svc.upload(
            user_id=current_user.id,
            filename=file.filename or "",
            content_type=file.content_type,
            contents=contents,
        )
    except ValidationError:
        raise _too_large
    return record.to_dict()


@router.post("/upload/dir")
async def upload_dir(
    current_user: User = Depends(get_current_user),
):
    """POST /api/v1/files/upload/dir  ← uploadDir() in files/index.ts:36
    Directory upload is not supported in CE; returns empty list."""
    return []


# ── List / Get ────────────────────────────────────────────────────────────────


@router.get("/")
async def get_files(
    current_user: User = Depends(get_current_user),
    svc: FilesService = Depends(get_files_service),
):
    """GET /api/v1/files/  ← getFiles() in files/index.ts:62"""
    return [r.to_dict() for r in svc.list_for_user(current_user.id)]


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    svc: FilesService = Depends(get_files_service),
):
    """GET /api/v1/files/{id}  ← getFileById() in files/index.ts:93"""
    try:
        record = svc.require_owned(file_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return record.to_dict()


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    current_user: User = Depends(get_current_user),
    svc: FilesService = Depends(get_files_service),
):
    """GET /api/v1/files/{id}/content  ← getFileContentById() in files/index.ts:158"""
    try:
        svc.require_owned(file_id, current_user.id)
        data, content_type = svc.read_bytes(file_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return Response(content=data, media_type=content_type)


# ── Update ────────────────────────────────────────────────────────────────────


@router.post("/{file_id}/data/content/update")
async def update_file_content(
    file_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    svc: FilesService = Depends(get_files_service),
):
    """POST /api/v1/files/{id}/data/content/update  ← updateFileDataContentById() in files/index.ts:124"""
    try:
        record = svc.update_content(file_id, current_user.id, body.get("content", ""))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return record.to_dict()


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete("/all")
async def delete_all_files(
    current_user: User = Depends(get_current_user),
    svc: FilesService = Depends(get_files_service),
):
    """DELETE /api/v1/files/all  ← deleteAllFiles() in files/index.ts:217"""
    count = svc.delete_all(current_user.id)
    return {"count": count}


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    svc: FilesService = Depends(get_files_service),
):
    """DELETE /api/v1/files/{id}  ← deleteFileById() in files/index.ts:186"""
    try:
        svc.delete(file_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return {"id": file_id}

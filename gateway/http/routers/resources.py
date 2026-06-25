"""Resources router — class materials + assignment templates.

  • Class-material management (`POST`/`DELETE`) is teacher-only (ownership);
    listing/downloading is allowed for the teacher OR an enrolled student.
  • Templates are owner-only (a teacher sees/uses only their own).

Thin HTTP layer only; the blob itself is stored/served via `content/files`.
"""

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from pydantic import BaseModel, Field

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from config import settings
from data.models import User
from gateway.http.dependencies import (
    Pagination,
    get_current_user,
    get_resources_service,
    pagination,
    require_teacher,
)
from resources.service import ResourcesService

# Class-scoped material routes live under /classrooms; the flat library + templates
# live at the top level. Both register under /api/v1.
router = APIRouter(prefix="/classrooms", tags=["resources"])
library_router = APIRouter(tags=["resources"])


class TemplateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    instructions: Optional[str] = Field(None, max_length=10000)
    attachment_id: Optional[str] = Field(None, max_length=64)


class FromTemplateRequest(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=64)
    due_date: Optional[str] = Field(None, max_length=40)


def _http_from_domain(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, AuthorizationError):
        return HTTPException(status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ValidationError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    raise exc


# ── class materials ────────────────────────────────────────────────────────────


@router.post("/{id}/resources", status_code=status.HTTP_201_CREATED)
async def upload_material(
    id: str,
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    teacher: User = Depends(require_teacher),
    svc: ResourcesService = Depends(get_resources_service),
):
    # Reject disallowed file types up front (allowlist, not denylist) — blocks
    # executables/scripts from the materials library before any bytes are stored.
    ctype = (file.content_type or "").split(";")[0].strip().lower()
    allowed = ctype in settings.ALLOWED_MATERIAL_MIME or ctype.startswith(
        settings.ALLOWED_MATERIAL_MIME_PREFIXES
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{ctype or 'unknown'}' is not allowed",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    _too_large = HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
    )
    contents = b""
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        contents += chunk
        if len(contents) > max_bytes:
            raise _too_large
    try:
        return svc.upload_material(
            id,
            teacher.id,
            file.filename or "",
            file.content_type,
            contents,
            title,
            description,
        )
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


@router.get("/{id}/resources")
def list_materials(
    id: str,
    current_user: User = Depends(get_current_user),
    svc: ResourcesService = Depends(get_resources_service),
    page: Pagination = Depends(pagination),
):
    """Teacher (owner) or enrolled student lists the class materials."""
    try:
        return page.apply(svc.list_materials(id, current_user.id))
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.get("/{id}/resources/{rid}/content")
def download_material(
    id: str,
    rid: str,
    current_user: User = Depends(get_current_user),
    svc: ResourcesService = Depends(get_resources_service),
):
    try:
        data, content_type, filename = svc.read_material(id, rid, current_user.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return Response(
        content=data,
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.delete("/{id}/resources/{rid}")
def delete_material(
    id: str,
    rid: str,
    teacher: User = Depends(require_teacher),
    svc: ResourcesService = Depends(get_resources_service),
):
    try:
        svc.delete_material(id, teacher.id, rid)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return {"status": "deleted", "id": rid}


# ── create assignment from a template (delegates to E7) ─────────────────────────


@router.post("/{id}/assignments/from-template", status_code=status.HTTP_201_CREATED)
def create_from_template(
    id: str,
    data: FromTemplateRequest,
    teacher: User = Depends(require_teacher),
    svc: ResourcesService = Depends(get_resources_service),
):
    try:
        return svc.create_assignment_from_template(
            id, teacher.id, data.template_id, data.due_date
        )
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


# ── flat library + templates (teacher) ─────────────────────────────────────────


@library_router.get("/resources")
def my_library(
    teacher: User = Depends(require_teacher),
    svc: ResourcesService = Depends(get_resources_service),
):
    """The teacher's materials across all their classes + their templates.
    Returns a {materials, templates} envelope (not a bare list), so it isn't sliced."""
    return svc.list_library(teacher.id)


@library_router.get("/assignment-templates")
def list_templates(
    teacher: User = Depends(require_teacher),
    svc: ResourcesService = Depends(get_resources_service),
    page: Pagination = Depends(pagination),
):
    return page.apply(svc.list_templates(teacher.id))


@library_router.post("/assignment-templates", status_code=status.HTTP_201_CREATED)
def save_template(
    data: TemplateRequest,
    teacher: User = Depends(require_teacher),
    svc: ResourcesService = Depends(get_resources_service),
):
    try:
        return svc.save_template(
            teacher.id, data.title, data.instructions, data.attachment_id
        )
    except ValidationError as exc:
        raise _http_from_domain(exc)


@library_router.delete("/assignment-templates/{tid}")
def delete_template(
    tid: str,
    teacher: User = Depends(require_teacher),
    svc: ResourcesService = Depends(get_resources_service),
):
    try:
        svc.delete_template(tid, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return {"status": "deleted", "id": tid}

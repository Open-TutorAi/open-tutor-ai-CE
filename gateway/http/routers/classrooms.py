"""Classrooms router — /api/classrooms/*."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from gateway.http.rate_limit import limiter
from learning.classrooms.schemas import (
    AddStudentRequest,
    AddStudentResult,
    ClassroomCreate,
    ClassroomDetail,
    ClassroomOut,
    ClassroomUpdate,
    EnrolledClassroomOut,
    StudentOut,
    ImportResult,
    InviteCreate,
    InviteOut,
    InviteRedeemResult,
)

from learning.classrooms.service import ClassroomsService
from fastapi import UploadFile, File

router = APIRouter(prefix="/api/classrooms", tags=["classrooms"])


def get_classrooms_service(db: Session = Depends(get_db)) -> ClassroomsService:
    return ClassroomsService(db)


@router.post("", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    body: ClassroomCreate,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    return svc.create_classroom(current_user.id, body)


@router.get("", response_model=List[ClassroomOut])
async def list_my_classrooms(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    return svc.get_my_classrooms(current_user.id, limit=limit, offset=offset)


@router.get("/enrolled", response_model=List[EnrolledClassroomOut])
async def list_enrolled_classrooms(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    return svc.list_enrolled_classrooms(current_user.id, limit=limit, offset=offset)


@router.get("/{classroom_id}", response_model=ClassroomDetail)
async def get_classroom(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.get_classroom_detail(classroom_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.put("/{classroom_id}", response_model=ClassroomOut)
async def update_classroom(
    classroom_id: str,
    body: ClassroomUpdate,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.update_classroom(classroom_id, current_user.id, body)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/{classroom_id}")
async def delete_classroom(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        svc.delete_classroom(classroom_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return {"message": "Classroom deleted"}


@router.get("/{classroom_id}/students", response_model=List[StudentOut])
async def list_students(
    classroom_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.list_students(
            classroom_id, current_user.id, limit=limit, offset=offset
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post(
    "/{classroom_id}/students",
    response_model=AddStudentResult,
    status_code=status.HTTP_201_CREATED,
)
async def add_student(
    classroom_id: str,
    body: AddStudentRequest,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.add_student(classroom_id, current_user.id, body.email)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


_CSV_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/{classroom_id}/import", response_model=ImportResult)
async def import_students(
    classroom_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted",
        )
    try:
        content = await file.read(_CSV_MAX_BYTES + 1)
        if len(content) > _CSV_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="CSV file must be smaller than 5 MB",
            )
        from io import BytesIO, TextIOWrapper

        bio = BytesIO(content)
        text = TextIOWrapper(bio, encoding="utf-8")
        return svc.import_students_from_csv(classroom_id, current_user.id, text)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post(
    "/{classroom_id}/invites",
    response_model=InviteOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    classroom_id: str,
    body: InviteCreate,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.create_invite(classroom_id, current_user.id, body)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/invites/{code}/redeem", response_model=InviteRedeemResult)
@limiter.limit("10/minute")
async def redeem_invite(
    request: Request,
    code: str,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.redeem_invite(code, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.delete("/{classroom_id}/students/{student_id}")
async def remove_student(
    classroom_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        svc.remove_student(classroom_id, current_user.id, student_id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return {"status": "removed"}

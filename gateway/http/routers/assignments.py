"""Assignment router — /assignments/* routes for teacher assignments and AI-assisted grading."""

from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from config import settings
from data.models import User
from gateway.http.dependencies import get_assignment_service, get_current_user
from learning.assignments.service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    rubric: str
    due_date: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    rubric: str
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    user_id: str
    filename: str
    file_size: Optional[int] = None
    extracted_text: Optional[str] = None
    ai_score: Optional[int] = None
    ai_feedback: Optional[str] = None
    teacher_score: Optional[int] = None
    teacher_feedback: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FinalizeGradeRequest(BaseModel):
    score: int
    feedback: str


class AiGradeRequest(BaseModel):
    model: str


class MySubmissionResponse(BaseModel):
    """A student's own view of their submission — never exposes the AI draft."""

    id: str
    assignment_id: str
    filename: str
    file_size: Optional[int] = None
    teacher_score: Optional[int] = None
    teacher_feedback: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _require_teacher(current_user: User) -> None:
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can perform this action",
        )


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    data: AssignmentCreateRequest,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    _require_teacher(current_user)
    return svc.create_assignment(current_user.id, data.model_dump())


@router.get("", response_model=List[AssignmentResponse])
async def list_assignments(
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    if current_user.role == "teacher":
        return svc.list_assignments_for_teacher(current_user.id)
    # No classroom/roster concept yet — students see every assignment.
    return svc.assignments.get_all()


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    assignment = svc.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
        )
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    _require_teacher(current_user)
    try:
        svc.delete_assignment(current_user.id, assignment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.post("/{assignment_id}/submissions", response_model=SubmissionResponse)
async def submit_work(
    assignment_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    too_large = HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
    )

    raw_cl = request.headers.get("content-length")
    if raw_cl and raw_cl.isdigit() and int(raw_cl) > max_bytes:
        raise too_large

    contents = b""
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        contents += chunk
        if len(contents) > max_bytes:
            raise too_large

    try:
        return svc.submit_work(
            current_user.id,
            assignment_id,
            file.filename or "upload",
            contents,
            settings.UPLOAD_DIR,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def list_submissions(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    try:
        return svc.list_submissions_for_assignment(current_user.id, assignment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.get(
    "/{assignment_id}/submissions/mine",
    response_model=Optional[MySubmissionResponse],
)
async def get_my_submission(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    """The current student's own submission for this assignment, if any.

    Registered before the generic {submission_id} route below so the literal
    "mine" segment isn't swallowed by that route's path parameter.
    """
    return svc.get_my_submission(current_user.id, assignment_id)


@router.get("/{assignment_id}/submissions/{submission_id}")
async def get_submission(
    assignment_id: str,
    submission_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    """Return the full submission (with AI draft fields) to the owning teacher,
    or the AI-free view to the owning student.

    No static response_model here on purpose — the two roles get structurally
    different shapes (SubmissionResponse vs MySubmissionResponse), so the model
    to validate against is chosen per-request instead of fixed at declaration
    time. Each branch still goes through its own Pydantic model, so the shape
    returned to the client is exactly as strict as any other endpoint here.
    """
    submission = svc.submissions.get_by_id(submission_id)
    if not submission or submission.assignment_id != assignment_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    is_owning_student = submission.user_id == current_user.id
    is_owning_teacher = False
    if current_user.role == "teacher":
        assignment = svc.get_assignment(assignment_id)
        is_owning_teacher = bool(assignment and assignment.user_id == current_user.id)

    if not (is_owning_student or is_owning_teacher):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this submission",
        )

    if is_owning_teacher:
        return SubmissionResponse.model_validate(submission)
    return MySubmissionResponse.model_validate(submission)


@router.post(
    "/{assignment_id}/submissions/{submission_id}/ai-grade",
    response_model=SubmissionResponse,
)
async def ai_grade_submission(
    assignment_id: str,
    submission_id: str,
    data: AiGradeRequest,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    try:
        return await svc.request_ai_grade(
            current_user.id, assignment_id, submission_id, data.model
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


@router.put(
    "/{assignment_id}/submissions/{submission_id}/finalize",
    response_model=SubmissionResponse,
)
async def finalize_submission(
    assignment_id: str,
    submission_id: str,
    data: FinalizeGradeRequest,
    current_user: User = Depends(get_current_user),
    svc: AssignmentService = Depends(get_assignment_service),
):
    try:
        return svc.finalize_grade(
            current_user.id,
            assignment_id,
            submission_id,
            data.score,
            data.feedback,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)

"""
student_courses.py — UPDATED with progress tracking
Replace: backend/open_tutorai/routers/student_courses.py
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from open_webui.internal.db import engine
from open_tutorai.utils.auth import get_verified_user
from open_tutorai.models.database import (
    Course,
    CourseEnrollment,
    CoursePlan,
    CourseFile,
    CourseProgress,
)
from open_webui.models.users import Users
log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter(prefix="/student/courses", tags=["Student Courses"])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Helpers ───────────────────────────────────────────────────────────────────


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ───────────────────────────────────────────────────────────────────


class EnrollRequest(BaseModel):
    course_id: str


class SectionProgressUpdate(BaseModel):
    chapter_id: str
    section_id: str
    status: str = "completed"  # 'not-started' | 'in-progress' | 'completed'


class ChatIdUpdate(BaseModel):
    chat_id: str


class EnrolledCourseResponse(BaseModel):
    id: str
    title: str
    language: str
    category: Optional[str] = None
    level: str
    teacher_name: str
    teacher_profile_image_url: Optional[str] = None
    enrolled_at: str
    status: str
    progress_percentage: float = 0.0
    chat_id: Optional[str] = None


class SectionDetail(BaseModel):
    id: str
    title: str
    status: str = "not-started"


class ChapterDetail(BaseModel):
    id: str
    title: str
    sections: List[SectionDetail] = []


class CourseFileDetail(BaseModel):
    id: str
    name: str
    size_kb: int = 0
    type: str = "application/pdf"


class CourseDetailResponse(BaseModel):
    id: str
    title: str
    language: str
    category: Optional[str] = None
    level: str
    teacher_name: str
    teacher_profile_image_url: Optional[str] = None
    objectives: Optional[str] = None
    welcome_message: Optional[str] = None
    files: List[CourseFileDetail] = []
    chapters: List[ChapterDetail] = []
    enrolled_at: str
    status: str
    progress_percentage: float = 0.0
    chat_id: Optional[str] = None


class SectionProgressResponse(BaseModel):
    chapter_id: str
    section_id: str
    status: str
    completed_at: Optional[str] = None


class ProgressSummaryResponse(BaseModel):
    total_sections: int
    completed_sections: int
    progress_percentage: float
    sections: List[SectionProgressResponse]
    chat_id: Optional[str] = None


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_teacher_name(teacher_id: str) -> str:
    teacher_name = "Professeur"
    try:
        teacher = Users.get_user_by_id(teacher_id)
        if teacher:
            teacher_name = getattr(teacher, "name", None) or getattr(
                teacher, "email", "Professeur"
            )
    except Exception:
        pass
    return teacher_name


def _get_teacher_info(teacher_id: str) -> tuple:
    """Get teacher name and profile image URL."""
    teacher_name = "Professeur"
    teacher_image = None
    try:
        teacher = Users.get_user_by_id(teacher_id)
        if teacher:
            teacher_name = getattr(teacher, "name", None) or getattr(
                teacher, "email", "Professeur"
            )
            teacher_image = getattr(teacher, "profile_image_url", None)
    except Exception:
        pass
    return teacher_name, teacher_image


def _calculate_progress(enrollment: CourseEnrollment, plan_json: dict, db) -> float:
    """Calculate progress percentage for an enrollment."""
    if not plan_json:
        return 0.0

    total_sections = sum(
        len(ch.get("sections", [])) for ch in plan_json.get("chapters", [])
    )
    if total_sections == 0:
        return 0.0

    completed = (
        db.query(CourseProgress)
        .filter(
            CourseProgress.enrollment_id == enrollment.id,
            CourseProgress.status == "completed",
        )
        .count()
    )
    return round((completed / total_sections) * 100, 1)


def _get_section_statuses(enrollment_id: str, db) -> dict:
    """Return dict of section_id -> status for an enrollment."""
    progress_rows = (
        db.query(CourseProgress)
        .filter(CourseProgress.enrollment_id == enrollment_id)
        .all()
    )
    return {row.section_id: row.status for row in progress_rows}


def _build_enrolled_response(
    course: Course, enrollment: CourseEnrollment, db, plan_json: dict = None
) -> EnrolledCourseResponse:
    progress_pct = 0.0
    if plan_json:
        progress_pct = _calculate_progress(enrollment, plan_json, db)

    teacher_name, teacher_image = _get_teacher_info(course.teacher_id)

    return EnrolledCourseResponse(
        id=course.id,
        title=course.title,
        language=course.language,
        category=course.category,
        level=course.level,
        teacher_name=teacher_name,
        teacher_profile_image_url=teacher_image,
        enrolled_at=(
            enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else ""
        ),
        status=(enrollment.status if hasattr(enrollment, "status") else "active"),
        progress_percentage=progress_pct,
        chat_id=getattr(enrollment, "chat_id", None),
    )


# ── ROUTE 1: GET / — Liste des cours rejoints ─────────────────────────────────


@router.get("/", response_model=List[EnrolledCourseResponse])
async def list_enrolled_courses(
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    enrollments = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.is_hidden == False,
        )
        .order_by(CourseEnrollment.enrolled_at.desc())
        .all()
    )

    result = []
    for enr in enrollments:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        if not course:
            continue

        course_plan = (
            db.query(CoursePlan).filter(CoursePlan.course_id == course.id).first()
        )
        plan_json = course_plan.plan_json if course_plan else None
        result.append(_build_enrolled_response(course, enr, db, plan_json))

    return result


# ── ROUTE 2: POST /enroll — Rejoindre un cours ────────────────────────────────


@router.post("/enroll", response_model=EnrolledCourseResponse, status_code=201)
async def enroll_in_course(
    body: EnrollRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    course_id = body.course_id.strip()

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404, detail="Code invalide ou cours introuvable"
        )

    existing = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Vous êtes déjà inscrit à ce cours")

    enrollment = CourseEnrollment(
        course_id=course_id,
        student_id=user.id,
        enrolled_at=datetime.utcnow(),
        status="active",
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    log.info("Student %s enrolled in course %s", user.id, course_id)
    return _build_enrolled_response(course, enrollment, db)


# ── ROUTE 3: GET /{course_id} — Détail d'un cours ────────────────────────────


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course_detail(
    course_id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.is_hidden == False,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=404, detail="Cours introuvable ou accès non autorisé"
        )

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")

    # Get section statuses for this enrollment
    section_statuses = _get_section_statuses(enrollment.id, db)

    # Build chapters with real progress status
    chapters_data: List[ChapterDetail] = []
    course_plan = db.query(CoursePlan).filter(CoursePlan.course_id == course_id).first()
    plan_json = None

    if course_plan and course_plan.plan_json:
        plan_json = course_plan.plan_json
        for ch in plan_json.get("chapters", []):
            sections = [
                SectionDetail(
                    id=s.get("id", ""),
                    title=s.get("title", ""),
                    status=section_statuses.get(s.get("id", ""), "not-started"),
                )
                for s in ch.get("sections", [])
            ]
            chapters_data.append(
                ChapterDetail(
                    id=ch.get("id", ""),
                    title=ch.get("title", ""),
                    sections=sections,
                )
            )

    # Files
    db_files = db.query(CourseFile).filter(CourseFile.course_id == course_id).all()
    files_data = [
        CourseFileDetail(
            id=f.id,
            name=f.filename,
            size_kb=int((f.file_size or 0) / 1024),
            type=f.file_type or "application/pdf",
        )
        for f in db_files
    ]

    progress_pct = _calculate_progress(enrollment, plan_json or {}, db)

    teacher_name, teacher_image = _get_teacher_info(course.teacher_id)

    return CourseDetailResponse(
        id=course.id,
        title=course.title,
        language=course.language,
        category=course.category,
        level=course.level,
        teacher_name=teacher_name,
        teacher_profile_image_url=teacher_image,
        objectives=course.objectives,
        welcome_message=None,
        files=files_data,
        chapters=chapters_data,
        enrolled_at=(
            enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else ""
        ),
        status=enrollment.status or "active",
        progress_percentage=progress_pct,
        chat_id=getattr(enrollment, "chat_id", None),
    )


# ── ROUTE 4: DELETE /{course_id} — Se désinscrire ────────────────────────────


@router.delete("/{course_id}", status_code=204)
async def unenroll_from_course(
    course_id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.is_hidden == False,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Inscription introuvable")

    # Delete progress records first
    db.query(CourseProgress).filter(
        CourseProgress.enrollment_id == enrollment.id
    ).delete(synchronize_session=False)

    db.delete(enrollment)
    db.commit()
    log.info("Student %s unenrolled from course %s", user.id, course_id)


# ── ROUTE 5: GET /{course_id}/progress — Résumé du progrès ───────────────────


@router.get("/{course_id}/progress", response_model=ProgressSummaryResponse)
async def get_course_progress(
    course_id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.is_hidden == False,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Inscription introuvable")

    course_plan = db.query(CoursePlan).filter(CoursePlan.course_id == course_id).first()
    plan_json = course_plan.plan_json if course_plan else {}

    total_sections = sum(
        len(ch.get("sections", [])) for ch in plan_json.get("chapters", [])
    )

    progress_rows = (
        db.query(CourseProgress)
        .filter(CourseProgress.enrollment_id == enrollment.id)
        .all()
    )

    completed = sum(1 for r in progress_rows if r.status == "completed")
    pct = round((completed / total_sections) * 100, 1) if total_sections > 0 else 0.0

    return ProgressSummaryResponse(
        total_sections=total_sections,
        completed_sections=completed,
        progress_percentage=pct,
        sections=[
            SectionProgressResponse(
                chapter_id=r.chapter_id,
                section_id=r.section_id,
                status=r.status,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
            )
            for r in progress_rows
        ],
        chat_id=getattr(enrollment, "chat_id", None),
    )


# ── ROUTE 6: PUT /{course_id}/progress — Mettre à jour le progrès ─────────────


@router.put("/{course_id}/progress", response_model=ProgressSummaryResponse)
async def update_section_progress(
    course_id: str,
    body: SectionProgressUpdate,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.is_hidden == False,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Inscription introuvable")

    # Upsert progress record
    existing = (
        db.query(CourseProgress)
        .filter(
            CourseProgress.enrollment_id == enrollment.id,
            CourseProgress.chapter_id == body.chapter_id,
            CourseProgress.section_id == body.section_id,
        )
        .first()
    )

    if existing:
        existing.status = body.status
        if body.status == "completed" and not existing.completed_at:
            existing.completed_at = datetime.utcnow()
    else:
        new_progress = CourseProgress(
            enrollment_id=enrollment.id,
            course_id=course_id,
            student_id=user.id,
            chapter_id=body.chapter_id,
            section_id=body.section_id,
            status=body.status,
            completed_at=datetime.utcnow() if body.status == "completed" else None,
        )
        db.add(new_progress)

    db.commit()

    # Return updated summary
    return await get_course_progress(course_id, user, db)


# ── ROUTE 7: PUT /{course_id}/chat — Sauvegarder le chat_id ──────────────────


@router.put("/{course_id}/chat", status_code=200)
async def save_course_chat_id(
    course_id: str,
    body: ChatIdUpdate,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """
    Store the AI chat session ID in the enrollment so the student
    can resume the same conversation next time.
    """
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.is_hidden == False,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Inscription introuvable")

    enrollment.chat_id = body.chat_id
    db.commit()
    log.info("Saved chat_id %s for enrollment of course %s", body.chat_id, course_id)
    return {"status": "ok", "chat_id": body.chat_id}

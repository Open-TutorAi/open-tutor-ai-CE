"""
Student courses API — /api/v1/student/courses/
Endpoints:
  GET    /student/courses/              → liste des cours rejoints
  POST   /student/courses/enroll        → rejoindre un cours via code (course_id)
  GET    /student/courses/{id}          → détail d'un cours
  DELETE /student/courses/{id}          → se désinscrire d'un cours
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
)

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


class EnrolledCourseResponse(BaseModel):
    id: str
    title: str
    language: str
    category: Optional[str] = None
    level: str
    teacher_name: str
    enrolled_at: str
    status: str


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
    objectives: Optional[str] = None
    welcome_message: Optional[str] = None
    files: List[CourseFileDetail] = []
    chapters: List[ChapterDetail] = []
    enrolled_at: str
    status: str


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_teacher_name(teacher_id: str) -> str:
    teacher_name = "Professeur"
    try:
        from open_webui.models.users import Users

        teacher = Users.get_user_by_id(teacher_id)
        if teacher:
            teacher_name = getattr(teacher, "name", None) or getattr(
                teacher, "email", "Professeur"
            )
    except Exception:
        pass
    return teacher_name


def _build_enrolled_response(
    course: Course, enrollment: CourseEnrollment, db
) -> EnrolledCourseResponse:
    return EnrolledCourseResponse(
        id=course.id,
        title=course.title,
        language=course.language,
        category=course.category,
        level=course.level,
        teacher_name=_get_teacher_name(course.teacher_id),
        enrolled_at=(
            enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else ""
        ),
        status=(enrollment.status if hasattr(enrollment, "status") else "active"),
    )


# ── ROUTE 1: GET / — Liste des cours rejoints ─────────────────────────────────


@router.get("/", response_model=List[EnrolledCourseResponse])
async def list_enrolled_courses(
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """Return all courses the authenticated student has enrolled in."""
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.student_id == user.id)
        .order_by(CourseEnrollment.enrolled_at.desc())
        .all()
    )

    result = []
    for enr in enrollments:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        if not course:
            continue
        result.append(_build_enrolled_response(course, enr, db))

    return result


# ── ROUTE 2: POST /enroll — Rejoindre un cours ────────────────────────────────


@router.post("/enroll", response_model=EnrolledCourseResponse, status_code=201)
async def enroll_in_course(
    body: EnrollRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """
    Enroll the authenticated student in a course using its ID.
    Returns 404 if the course does not exist.
    Returns 409 if the student is already enrolled.
    """
    course_id = body.course_id.strip()

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Code invalide ou cours introuvable",
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
    """
    Return full detail of a course the student is enrolled in.
    Includes: course info + chapters + sections + files.
    """
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
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

    # Chapitres + sections
    chapters_data: List[ChapterDetail] = []
    course_plan = db.query(CoursePlan).filter(CoursePlan.course_id == course_id).first()

    if course_plan and course_plan.plan_json:
        plan = course_plan.plan_json
        for ch in plan.get("chapters", []):
            sections = [
                SectionDetail(
                    id=s.get("id", ""),
                    title=s.get("title", ""),
                    status="not-started",
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

    # Fichiers
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

    return CourseDetailResponse(
        id=course.id,
        title=course.title,
        language=course.language,
        category=course.category,
        level=course.level,
        teacher_name=_get_teacher_name(course.teacher_id),
        objectives=course.objectives,
        welcome_message=None,
        files=files_data,
        chapters=chapters_data,
        enrolled_at=(
            enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else ""
        ),
        status=enrollment.status or "active",
    )


# ── ROUTE 4: DELETE /{course_id} — Se désinscrire d'un cours ─────────────────


@router.delete("/{course_id}", status_code=204)
async def unenroll_from_course(
    course_id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """
    Unenroll the authenticated student from a course.
    Returns 404 if enrollment not found.
    """
    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == user.id,
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Inscription introuvable")

    db.delete(enrollment)
    db.commit()
    log.info("Student %s unenrolled from course %s", user.id, course_id)

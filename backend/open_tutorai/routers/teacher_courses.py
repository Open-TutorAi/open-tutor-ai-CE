import uuid
import json
import logging
import os

from datetime import datetime
from typing import Optional, List
from open_tutorai.models.database import Course, CourseEnrollment
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import sessionmaker

from open_webui.internal.db import engine
from open_tutorai.utils.auth import get_verified_user
from open_webui.models.models import Models
from open_tutorai.models.database import Course, CoursePlan, CourseFile
from open_tutorai.models.database import (
    Course,
    CourseEnrollment,
    CourseProgress,
    CoursePlan,
    Quiz,
    QuizSubmission,
)
from open_webui.models.users import Users

# ---------------------------------------------------------------
# Logging
# ---------------------------------------------------------------
log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter(prefix="/teacher/courses", tags=["Teacher Courses"])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------
# System Prompt for course plan generation
# ---------------------------------------------------------------
COURSE_PLAN_SYSTEM_PROMPT = """You are an expert instructional designer. Given course details, generate a structured course plan WITH pedagogical objectives.
Return ONLY a valid JSON object with this exact format, no extra text:
{
  "objectives": "\n\n1. ...\n2. ...\n3. ...",
  "chapters": [
    {
      "id": "ch1",
      "title": "Chapter title",
      "sections": [
        { "id": "sec1-1", "title": "Section title" },
        ...
      ]
    },
    ...
  ]
}
Rules:
- Generate 5-7 well-written pedagogical objectives (numbered list format)
- Create 3-7 chapters, each with 2-4 sections
- Output ONLY the JSON object, nothing else
- IMPORTANT: ALL The JSON output must respect the course language
"""

# ---------------------------------------------------------------
# Pydantic Models (mirroring SupportCreateRequest / SupportResponse)
# ---------------------------------------------------------------


class CourseCreateRequest(BaseModel):
    title: str
    language: str
    category: Optional[str] = None
    custom_category: Optional[str] = None
    level: str
    objectives: Optional[str] = None
    short_description: Optional[str] = None
    estimated_duration: Optional[str] = None
    access_type: Optional[str] = "Private"
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    avatar_id: Optional[str] = None
    chat_id: Optional[str] = None
    model: Optional[str] = None


class CourseUpdateRequest(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    custom_category: Optional[str] = None
    level: Optional[str] = None
    objectives: Optional[str] = None
    short_description: Optional[str] = None
    estimated_duration: Optional[str] = None
    access_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    avatar_id: Optional[str] = None
    chat_id: Optional[str] = None


class CourseResponse(BaseModel):
    id: str
    teacher_id: str
    title: str
    language: str
    category: Optional[str] = None
    custom_category: Optional[str] = None
    level: str
    objectives: Optional[str] = None
    short_description: Optional[str] = None
    estimated_duration: Optional[str] = None
    access_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    avatar_id: Optional[str] = None
    status: str
    model_used: Optional[str] = None
    chat_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class PlanRequest(BaseModel):
    chapters: List[dict]
    objectives: Optional[str] = None


class PlanResponse(BaseModel):
    course_id: str
    plan: dict


class PlanWithObjectives(BaseModel):
    course_id: str
    plan: dict
    objectives: str


class PlanGenerationRequest(BaseModel):
    model: str
    title: str
    language: str
    category: Optional[str] = None
    level: str
    objectives: Optional[str] = None


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _course_meta(course: Course) -> dict:
    meta_data = getattr(course, "meta_data", None)
    return meta_data if isinstance(meta_data, dict) else {}


def _to_response(course: Course) -> CourseResponse:
    meta_data = _course_meta(course)
    raw_keywords = getattr(course, "keywords", None) or meta_data.get("keywords")

    def pick(name: str):
        return getattr(course, name, None) or meta_data.get(name)

    if isinstance(raw_keywords, list):
        keywords_list = raw_keywords
    elif raw_keywords:
        keywords_list = [
            item.strip() for item in str(raw_keywords).split(",") if item.strip()
        ]
    else:
        keywords_list = None
    return CourseResponse(
        id=course.id,
        teacher_id=course.teacher_id,
        title=course.title,
        language=course.language,
        category=course.category,
        custom_category=course.custom_category,
        level=course.level,
        objectives=course.objectives,
        short_description=pick("short_description"),
        estimated_duration=pick("estimated_duration"),
        access_type=pick("access_type"),
        keywords=keywords_list,
        start_date=pick("start_date"),
        end_date=pick("end_date"),
        avatar_id=pick("avatar_id"),
        status=course.status,
        model_used=course.model_used,
        chat_id=course.chat_id,
        created_at=course.created_at.isoformat() if course.created_at else "",
        updated_at=course.updated_at.isoformat() if course.updated_at else None,
    )


def _get_course_or_404(db, course_id: str, teacher_id: str) -> Course:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.teacher_id == teacher_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    return course


# ---------------------------------------------------------------
# 1. POST /teacher/courses – Créer un nouveau cours
# ---------------------------------------------------------------
@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreateRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """Créer un nouveau cours (équivalent à POST /supports/create)"""
    new_id = str(uuid.uuid4())
    keywords_str = ",".join(course_data.keywords) if course_data.keywords else None
    meta_data = {
        key: value
        for key, value in {
            "short_description": course_data.short_description,
            "estimated_duration": course_data.estimated_duration,
            "access_type": course_data.access_type,
            "keywords": keywords_str,
            "start_date": course_data.start_date,
            "end_date": course_data.end_date,
            "avatar_id": course_data.avatar_id,
        }.items()
        if value is not None
    }

    course = Course(
        id=new_id,
        teacher_id=user.id,
        title=course_data.title,
        language=course_data.language,
        category=course_data.category,
        custom_category=course_data.custom_category,
        level=course_data.level,
        objectives=course_data.objectives,
        short_description=course_data.short_description,
        estimated_duration=course_data.estimated_duration,
        access_type=course_data.access_type,
        meta_data=meta_data or None,
        start_date=course_data.start_date,
        end_date=course_data.end_date,
        avatar_id=course_data.avatar_id,
        chat_id=course_data.chat_id,
        model_used=course_data.model,
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    log.info(f"Cours créé : {course.id} par {user.id}")
    return _to_response(course)


# ---------------------------------------------------------------
# 1b. POST /courses/generate – Génération complète du cours (create + upload + generate plan)
# ---------------------------------------------------------------
@router.post("/generate", response_model=dict)
async def generate_course_full(
    request: Request,
    title: str = Form(...),
    language: str = Form(...),
    category: str = Form(...),
    level: str = Form(...),
    objectives: str = Form(...),
    model: str = Form(...),
    files: List[UploadFile] = File(...),
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """
    Comprehensive endpoint for course generation:
    1. Creates the course record
    2. Uploads and stores the files
    3. Generates the course plan using the specified model
    """

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if not model:
        raise HTTPException(status_code=400, detail="No model specified")

    # Step 1: Create the course
    course_id = str(uuid.uuid4())
    course = Course(
        id=course_id,
        teacher_id=user.id,
        title=title,
        language=language,
        category=category,
        level=level,
        objectives=objectives,
        model_used=model,
        status="creating",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    log.info(f"Cours créé : {course_id} par {user.id}")

    # Step 2: Handle file uploads (store metadata, not actual files yet)
    upload_dir = os.path.join("/tmp", "course_uploads", course_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_contents = []
    file_metadata = []

    for uploaded_file in files:
        try:
            contents = await uploaded_file.read()
            file_path = os.path.join(upload_dir, uploaded_file.filename or "unknown")

            # Save file to disk
            with open(file_path, "wb") as f:
                f.write(contents)

            # Create CourseFile record
            course_file = CourseFile(
                id=str(uuid.uuid4()),
                course_id=course_id,
                filename=uploaded_file.filename or "unknown",
                file_path=file_path,
                file_type=uploaded_file.content_type,
                file_size=len(contents),
            )
            db.add(course_file)

            file_metadata.append(
                {"filename": uploaded_file.filename, "size": len(contents)}
            )

            log.info(f"Fichier sauvegardé : {file_path}")
        except Exception as e:
            log.error(
                f"Erreur lors du traitement du fichier {uploaded_file.filename}: {e}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Error processing file {uploaded_file.filename}",
            )

    db.commit()

    # Step 3: Generate course plan using the selected model
    auth_header = request.headers.get("authorization", "")
    port = int(os.environ.get("PORT", "8080"))

    user_message = json.dumps(
        {
            "title": title,
            "language": language,
            "category": category,
            "level": level,
            "objectives": objectives,
            "files": file_metadata,
        }
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": COURSE_PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(
                f"http://localhost:{port}/api/chat/completions",
                json=payload,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
            )
        r.raise_for_status()
    except httpx.TimeoutException as e:
        log.error(f"LLM call timed out after 300 seconds: {e}")
        course.status = "error"
        db.commit()
        raise HTTPException(
            status_code=500, detail="LLM generation timed out (exceeded 5 minutes)"
        )
    except httpx.HTTPStatusError as e:
        log.error(f"LLM call failed: {e.response.status_code} {e.response.text}")
        course.status = "error"
        db.commit()
        raise HTTPException(
            status_code=500, detail=f"LLM returned error: {e.response.status_code}"
        )
    except Exception as e:
        log.error(f"LLM call error: {e}")
        course.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to reach LLM backend")

    try:
        content = r.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if model wrapped the JSON
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        plan = json.loads(content)
        data = json.loads(content.strip())

        if "chapters" not in data:
            raise ValueError("missing 'chapters' key in plan")

        plan = {"chapters": data.get("chapters", [])}
        ai_objectives = data.get("objectives", objectives)

    except json.JSONDecodeError as je:
        log.error(f"JSON parsing error: {je}. Raw content: {content[:500]}")
        course.status = "error"
        db.commit()
        raise HTTPException(
            status_code=500, detail="LLM returned invalid JSON structure"
        )
    except Exception as e:
        log.error(f"Failed to parse LLM response: {e}")
        course.status = "error"
        db.commit()
        raise HTTPException(
            status_code=500, detail="Could not parse course plan from LLM response"
        )
    # Step 4: Save the generated plan
    plan_id = str(uuid.uuid4())
    course_plan = CoursePlan(
        id=plan_id,
        course_id=course_id,
        plan_json=plan,
        generated_at=datetime.utcnow(),
    )
    db.add(course_plan)

    course.status = "plan_generated"
    course.objectives = ai_objectives
    course.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(course)

    log.info(f"Plan généré pour le cours {course_id} avec le modèle {model}")

    return {
        "course_id": course_id,
        "course": _to_response(course),
        "plan": plan,
        "objectives": ai_objectives,
        "files_count": len(files),
    }


# ---------------------------------------------------------------
# 2. GET /teacher/courses – Liste des cours de l'enseignant
# ---------------------------------------------------------------
@router.get("/", response_model=List[CourseResponse])
async def list_teacher_courses(
    status: Optional[str] = None, user=Depends(get_verified_user), db=Depends(get_db)
):
    """Liste tous les cours créés par cet enseignant."""
    query = db.query(Course).filter(Course.teacher_id == user.id)
    if status:
        query = query.filter(Course.status == status)
    courses = query.order_by(Course.created_at.desc()).all()
    return [_to_response(c) for c in courses]


# ---------------------------------------------------------------
# 3. GET /teacher/courses/{course_id} – Détail d'un cours
# ---------------------------------------------------------------
@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str, user=Depends(get_verified_user), db=Depends(get_db)
):
    """Obtenir les informations d'un cours."""
    course = _get_course_or_404(db, course_id, user.id)
    return _to_response(course)


# ---------------------------------------------------------------
# 4. PUT /teacher/courses/{course_id} – Mettre à jour un cours
# ---------------------------------------------------------------
@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    update_data: CourseUpdateRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """Mettre à jour les informations d'un cours (enseignant uniquement)."""
    course = _get_course_or_404(db, course_id, user.id)

    # Appliquer les modifications uniquement si le champ est fourni (non None)
    update_dict = update_data.dict(exclude_unset=True)
    if "keywords" in update_dict and update_dict["keywords"] is not None:
        keywords_str = ",".join(update_dict["keywords"])
        existing_meta_data = _course_meta(course).copy()
        existing_meta_data["keywords"] = keywords_str
        course.meta_data = existing_meta_data
        update_dict.pop("keywords")

    meta_updates = {}
    for meta_key in (
        "short_description",
        "estimated_duration",
        "access_type",
        "start_date",
        "end_date",
        "avatar_id",
    ):
        if meta_key in update_dict:
            meta_updates[meta_key] = update_dict.pop(meta_key)

    if meta_updates:
        existing_meta_data = _course_meta(course).copy()
        for key, value in meta_updates.items():
            if value is not None:
                existing_meta_data[key] = value
        course.meta_data = existing_meta_data

    for key, value in update_dict.items():
        setattr(course, key, value)

    course.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(course)
    return _to_response(course)


# ---------------------------------------------------------------
# 5. DELETE /teacher/courses/{course_id} – Supprimer un cours
# ---------------------------------------------------------------
@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: str, user=Depends(get_verified_user), db=Depends(get_db)
):
    """
    Supprimer un cours et TOUT ce qui lui est lié :
    - Enrollments des étudiants (CourseEnrollment)
    - Fichiers physiques + enregistrements (CourseFile)
    - Plans du cours (CoursePlan)
    - Le cours lui-même
    """

    course = _get_course_or_404(db, course_id, user.id)

    # ── 1. Supprimer les enrollments des étudiants ──────────────
    enrollments_deleted = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.course_id == course_id)
        .delete(synchronize_session=False)
    )
    log.info(f"Cours {course_id} : {enrollments_deleted} enrollment(s) supprimé(s)")

    # ── 2. Supprimer les fichiers physiques + DB ─────────────────
    files = db.query(CourseFile).filter(CourseFile.course_id == course_id).all()
    for f in files:
        try:
            if f.file_path and os.path.exists(f.file_path):
                os.remove(f.file_path)
                log.info(f"Fichier supprimé : {f.file_path}")
        except Exception as e:
            log.warning(f"Erreur suppression fichier {f.file_path}: {e}")

    db.query(CourseFile).filter(CourseFile.course_id == course_id).delete(
        synchronize_session=False
    )

    # ── 3. Supprimer les plans ───────────────────────────────────
    db.query(CoursePlan).filter(CoursePlan.course_id == course_id).delete(
        synchronize_session=False
    )

    # ── 4. Supprimer le cours lui-même ───────────────────────────
    db.delete(course)
    db.commit()

    log.info(f"Cours {course_id} supprimé définitivement par teacher {user.id}")


# ---------------------------------------------------------------
# 6. POST /teacher/courses/{course_id}/generate-plan – Génération du plan
# ---------------------------------------------------------------
@router.post("/{course_id}/generate-plan", response_model=PlanWithObjectives)
async def generate_course_plan(
    course_id: str,
    request: Request,
    body: PlanGenerationRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """
    Génère un plan de cours via le LLM local.
    1. Vérifie que le cours existe et appartient à l'enseignant.
    2. Appelle l'API de chat locale avec le prompt système + les détails du cours.
    3. Parse la réponse JSON, la sauvegarde dans CoursePlan.
    """
    course = _get_course_or_404(db, course_id, user.id)

    auth_header = request.headers.get("authorization", "")
    port = int(os.environ.get("PORT", "8080"))

    user_message = json.dumps(
        {
            "title": body.title,
            "language": body.language,
            "category": body.category,
            "level": body.level,
            "objectives": body.objectives,
        }
    )

    payload = {
        "model": body.model,
        "messages": [
            {"role": "system", "content": COURSE_PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            r = await client.post(
                f"http://localhost:{port}/api/chat/completions",
                json=payload,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
            )
        r.raise_for_status()
    except httpx.TimeoutException as e:
        log.error(f"LLM call timed out after 300 seconds: {e}")
        raise HTTPException(
            status_code=500, detail="LLM generation timed out (exceeded 5 minutes)"
        )
    except httpx.HTTPStatusError as e:
        log.error(f"LLM call failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(
            status_code=500, detail=f"LLM returned error: {e.response.status_code}"
        )
    except Exception as e:
        log.error(f"LLM call error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reach LLM backend")

    try:
        content = r.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if model wrapped the JSON
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        plan = json.loads(content)

        if "chapters" not in plan:
            raise ValueError("missing 'chapters' key in plan")

        ai_objectives = plan.get("objectives", body.objectives)
    except json.JSONDecodeError as je:
        log.error(f"JSON parsing error: {je}. Raw content: {content[:500]}")
        raise HTTPException(
            status_code=500, detail="LLM returned invalid JSON structure"
        )
    except Exception as e:
        log.error(f"Failed to parse LLM response: {e}")
        raise HTTPException(status_code=500, detail="Could not parse response")

    plan_id = str(uuid.uuid4())
    new_plan = CoursePlan(
        id=plan_id,
        course_id=course_id,
        plan_json=plan,
        generated_at=datetime.utcnow(),
    )
    db.add(new_plan)
    course.status = "plan_generated"
    course.model_used = body.model
    course.objectives = ai_objectives
    course.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(new_plan)
    log.info(f"Plan généré pour le cours {course_id} avec le modèle {body.model}")
    return PlanWithObjectives(course_id=course_id, plan=plan, objectives=ai_objectives)


# ---------------------------------------------------------------
# 7. GET /teacher/courses/{course_id}/plan – Récupérer le plan actuel
# ---------------------------------------------------------------
@router.get("/{course_id}/plan", response_model=PlanResponse)
async def get_course_plan(
    course_id: str, user=Depends(get_verified_user), db=Depends(get_db)
):
    """Récupérer le plan de cours existant."""
    course = _get_course_or_404(db, course_id, user.id)
    existing_plan = (
        db.query(CoursePlan).filter(CoursePlan.course_id == course_id).first()
    )
    if not existing_plan:
        raise HTTPException(status_code=404, detail="Aucun plan trouvé pour ce cours")
    return PlanResponse(course_id=course_id, plan=existing_plan.plan_json)


# ---------------------------------------------------------------
# 8. PUT /teacher/courses/{course_id}/plan – Sauvegarder/modifier le plan
# ---------------------------------------------------------------
@router.put("/{course_id}/plan", response_model=PlanResponse)
async def save_course_plan(
    course_id: str,
    plan_data: PlanRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    """Sauvegarde le plan modifié par l'enseignant (ou le crée)."""
    course = _get_course_or_404(db, course_id, user.id)

    # Mise à jour des objectifs si fournis
    if plan_data.objectives is not None:
        course.objectives = plan_data.objectives

    # Création ou mise à jour du plan
    existing_plan = (
        db.query(CoursePlan).filter(CoursePlan.course_id == course_id).first()
    )
    plan_json = {"chapters": plan_data.chapters}

    if existing_plan:
        existing_plan.plan_json = plan_json
        existing_plan.updated_at = datetime.utcnow()
        plan = existing_plan
    else:
        new_plan = CoursePlan(
            id=str(uuid.uuid4()),
            course_id=course_id,
            plan_json=plan_json,
            generated_at=datetime.utcnow(),
        )
        db.add(new_plan)
        plan = new_plan

    course.status = "plan_updated"
    db.commit()
    db.refresh(plan)

    return PlanResponse(course_id=course_id, plan=plan.plan_json)


# ---------------------------------------------------------------
# Models endpoint - returns available AI models
# ---------------------------------------------------------------
@router.get("/models/available")
async def get_available_models(user=Depends(get_verified_user)):
    """Get list of available AI models."""
    try:
        all_models = Models.get_all_models()

        # Filter to only public models or models created by the user
        available_models = []
        if all_models:
            for model in all_models:
                model_data = {
                    "id": getattr(model, "id", str(model)),
                    "name": getattr(model, "name", None)
                    or getattr(model, "title", None)
                    or str(getattr(model, "id", model)),
                    "is_public": getattr(model, "is_public", None),
                }

                # Include model if it has a valid ID
                if model_data["id"]:
                    available_models.append(model_data)

        return {
            "status": "ok",
            "data": available_models,
            "message": f"Found {len(available_models)} available models",
        }
    except Exception as e:
        log.error(f"Error fetching models: {str(e)}")
        return {
            "status": "error",
            "data": [],
            "message": f"Failed to fetch models: {str(e)}",
        }


# ── GET /teacher/courses/{course_id}/students/count ────────────
@router.get("/{course_id}/students/count")
async def get_students_count(
    course_id: str, user=Depends(get_verified_user), db=Depends(get_db)
):
    _get_course_or_404(db, course_id, user.id)
    # pyrefly: ignore [missing-import]

    count = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.course_id == course_id)
        .count()
    )
    return {"count": count}


# ── APIROUTER FOR TEACHER ANALYTICS ────────────────────────────
analytics_router = APIRouter(prefix="/teacher/analytics", tags=["Teacher Analytics"])


@analytics_router.get("/reports")
async def get_teacher_reports(
    course_id: Optional[str] = None,
    status: Optional[str] = None,
    date: Optional[str] = None,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):

    # 1. Get all courses owned by this teacher
    teacher_courses = db.query(Course).filter(Course.teacher_id == user.id).all()
    teacher_course_ids = [c.id for c in teacher_courses]

    if not teacher_course_ids:
        return {
            "completion_rate": "0.0%",
            "enrolled_students": "0",
            "students": [],
        }

    # 2. Filter courses if specific course_id is provided
    target_course_ids = teacher_course_ids
    if course_id and course_id != "all":
        if course_id in teacher_course_ids:
            target_course_ids = [course_id]
        else:
            return {
                "completion_rate": "0.0%",
                "enrolled_students": "0",
                "students": [],
            }

    # 3. Fetch all enrollments for target courses
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.course_id.in_(target_course_ids))
        .all()
    )

    # Filter by date if provided (format YYYY-MM-DD)
    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            enrollments = [
                e
                for e in enrollments
                if e.enrolled_at and e.enrolled_at.date() == filter_date
            ]
        except Exception as de:
            log.error(f"Error parsing date filter: {de}")

    students_list = []
    progress_sum = 0
    enrolled_student_ids = set()

    for enrollment in enrollments:
        student_id = enrollment.student_id
        enrolled_student_ids.add(student_id)

        # Get student user details
        student_user = Users.get_user_by_id(student_id)
        student_name = student_user.name if student_user else "Étudiant anonyme"

        # Calculate progress
        progress_percentage = 0
        plan_record = (
            db.query(CoursePlan)
            .filter(CoursePlan.course_id == enrollment.course_id)
            .first()
        )
        if plan_record and plan_record.plan_json:
            total_sections = 0
            plan_data = plan_record.plan_json
            if isinstance(plan_data, dict) and "chapters" in plan_data:
                for chap in plan_data["chapters"]:
                    if isinstance(chap, dict) and "sections" in chap:
                        total_sections += len(chap["sections"])

            if total_sections > 0:
                completed_count = (
                    db.query(CourseProgress)
                    .filter(
                        CourseProgress.enrollment_id == enrollment.id,
                        CourseProgress.status == "completed",
                    )
                    .count()
                )
                progress_percentage = int((completed_count / total_sections) * 100)

        progress_sum += progress_percentage

        # Last Quiz Grade
        quizzes = db.query(Quiz).filter(Quiz.course_id == enrollment.course_id).all()
        quiz_ids = [q.id for q in quizzes]

        grade_str = "-/20"
        last_score_pct = None
        if quiz_ids:
            latest_submission = (
                db.query(QuizSubmission)
                .filter(
                    QuizSubmission.quiz_id.in_(quiz_ids),
                    QuizSubmission.student_id == student_id,
                )
                .order_by(QuizSubmission.submitted_at.desc())
                .first()
            )
            if latest_submission:
                q_record = (
                    db.query(Quiz).filter(Quiz.id == latest_submission.quiz_id).first()
                )
                total_q = (
                    q_record.total_questions
                    if (q_record and q_record.total_questions)
                    else 20
                )
                if total_q > 0:
                    grade_str = f"{latest_submission.score}/{total_q}"
                    last_score_pct = latest_submission.score / total_q
                else:
                    grade_str = f"{latest_submission.score}/20"
                    last_score_pct = latest_submission.score / 20

        # Dynamic Status Tag
        if progress_percentage < 10:
            student_status = "Inactive"
        elif last_score_pct is not None and last_score_pct < 0.5:
            student_status = "Struggling"
        else:
            student_status = "Active"

        # Apply status filter
        if status and status != "all":
            if status == "completed" and progress_percentage < 100:
                continue
            if status == "in_progress" and student_status != "Active":
                continue
            if status == "failed" and student_status != "Struggling":
                continue

        enrollment_date = (
            enrollment.enrolled_at.strftime("%d %b %Y")
            if enrollment.enrolled_at
            else ""
        )

        students_list.append(
            {
                "id": student_id,
                "name": student_name,
                "date": enrollment_date,
                "progress": progress_percentage,
                "note": grade_str,
                "status": student_status,
            }
        )

    # Calculations for KPIs
    total_enrollments_count = len(students_list)
    average_completion_rate = "0.0%"
    if total_enrollments_count > 0:
        avg_pct = progress_sum / total_enrollments_count
        average_completion_rate = f"{avg_pct:.1f}%"

    return {
        "completion_rate": average_completion_rate,
        "enrolled_students": str(len(enrolled_student_ids)),
        "students": students_list,
    }


# ── APIROUTER FOR TEACHER STUDENTS (Visibility / Hide lesson) ──
students_router = APIRouter(prefix="/teacher/students", tags=["Teacher Students"])


class StudentCourseVisibilityResponse(BaseModel):
    course_id: str
    title: str
    is_hidden: bool


class HideCoursesRequest(BaseModel):
    student_id: str
    hidden_course_ids: List[str]


@students_router.get(
    "/{student_id}/courses", response_model=List[StudentCourseVisibilityResponse]
)
async def get_student_courses(
    student_id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    # Retrieve all courses owned by this teacher where this student is enrolled
    enrollments = (
        db.query(CourseEnrollment)
        .join(Course, CourseEnrollment.course_id == Course.id)
        .filter(CourseEnrollment.student_id == student_id, Course.teacher_id == user.id)
        .all()
    )

    return [
        StudentCourseVisibilityResponse(
            course_id=e.course_id,
            title=e.course.title,
            is_hidden=getattr(e, "is_hidden", False),
        )
        for e in enrollments
    ]


@students_router.post("/hide-courses")
async def hide_student_courses(
    body: HideCoursesRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):

    # Fetch all enrollments for this student for courses owned by the current teacher
    enrollments = (
        db.query(CourseEnrollment)
        .join(Course, CourseEnrollment.course_id == Course.id)
        .filter(
            CourseEnrollment.student_id == body.student_id,
            Course.teacher_id == user.id,
        )
        .all()
    )

    # For each enrollment, set is_hidden based on whether the course_id is in hidden_course_ids
    for e in enrollments:
        e.is_hidden = e.course_id in body.hidden_course_ids

    db.commit()
    return {"status": "success", "message": "Course visibility updated successfully"}


class StudentCourseDetail(BaseModel):
    course_id: str
    title: str
    progress: float
    completed_sections: int
    total_sections: int


class StudentQuizGrade(BaseModel):
    quiz_title: str
    score: float
    total_questions: int
    graded_at: str


class StudentProfileResponse(BaseModel):
    student_id: str
    name: str
    email: str
    enrolled_courses: List[StudentCourseDetail]
    quiz_grades: List[StudentQuizGrade]
    study_footprints_count: int


@students_router.get("/{student_id}/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    student_id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):

    # 1. Fetch user details
    student = Users.get_user_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student_name = getattr(student, "name", "Student")
    student_email = getattr(student, "email", "")

    # 2. Fetch all courses the student is enrolled in that are owned by the current teacher
    enrollments = (
        db.query(CourseEnrollment)
        .join(Course, CourseEnrollment.course_id == Course.id)
        .filter(CourseEnrollment.student_id == student_id, Course.teacher_id == user.id)
        .all()
    )

    enrolled_courses_data = []
    total_footprints = 0

    for enr in enrollments:
        course = enr.course
        course_plan = (
            db.query(CoursePlan).filter(CoursePlan.course_id == course.id).first()
        )
        plan_json = course_plan.plan_json if course_plan else {}

        total_sections = sum(
            len(ch.get("sections", [])) for ch in plan_json.get("chapters", [])
        )

        completed_sections = (
            db.query(CourseProgress)
            .filter(
                CourseProgress.enrollment_id == enr.id,
                CourseProgress.status == "completed",
            )
            .count()
        )

        progress_pct = 0.0
        if total_sections > 0:
            progress_pct = round((completed_sections / total_sections) * 100, 1)

        enrolled_courses_data.append(
            StudentCourseDetail(
                course_id=course.id,
                title=course.title,
                progress=progress_pct,
                completed_sections=completed_sections,
                total_sections=total_sections,
            )
        )

        # Add study footprints (total progresses logged)
        progress_count = (
            db.query(CourseProgress)
            .filter(CourseProgress.enrollment_id == enr.id)
            .count()
        )
        total_footprints += progress_count

    # 3. Fetch all quiz grades for courses owned by the current teacher
    quiz_submissions = (
        db.query(QuizSubmission)
        .join(Quiz, QuizSubmission.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(QuizSubmission.student_id == student_id, Course.teacher_id == user.id)
        .order_by(QuizSubmission.created_at.desc())
        .all()
    )

    quiz_grades_data = []
    for sub in quiz_submissions:
        quiz_grades_data.append(
            StudentQuizGrade(
                quiz_title=sub.quiz.title if sub.quiz else "Quiz",
                score=sub.score,
                total_questions=(
                    sub.quiz.total_questions
                    if (sub.quiz and sub.quiz.total_questions)
                    else 20
                ),
                graded_at=(
                    sub.created_at.strftime("%Y-%m-%d %H:%M") if sub.created_at else ""
                ),
            )
        )

    return StudentProfileResponse(
        student_id=student_id,
        name=student_name,
        email=student_email,
        enrolled_courses=enrolled_courses_data,
        quiz_grades=quiz_grades_data,
        study_footprints_count=total_footprints,
    )

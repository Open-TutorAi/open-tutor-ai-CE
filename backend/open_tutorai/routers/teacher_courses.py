import uuid
import json
import logging
import os
from datetime import datetime
from typing import Optional, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import sessionmaker

from open_webui.internal.db import engine
from open_tutorai.utils.auth import get_verified_user
from open_webui.models.models import Models
from open_tutorai.models.database import Course, CoursePlan, CourseFile

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
  "objectives": "À la fin de ce cours, l'étudiant sera capable de:\n\n1. ...\n2. ...\n3. ...",
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
- Create 3‑7 chapters, each with 2‑4 sections
- Use the course language
- Output ONLY the JSON object, nothing else."""

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
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"http://localhost:{port}/api/chat/completions",
                json=payload,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
            )
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        log.error(f"LLM call failed: {e.response.status_code} {e.response.text}")
        course.status = "error"
        db.commit()
        raise HTTPException(status_code=502, detail="Failed to generate course plan")
    except Exception as e:
        log.error(f"LLM call error: {e}")
        course.status = "error"
        db.commit()
        raise HTTPException(status_code=502, detail="Could not reach LLM")

    try:
        content = r.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if model wrapped the JSON
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        data = json.loads(content.strip())

        if "chapters" not in data:
            raise ValueError("missing 'chapters' key in plan")

        plan = {"chapters": data.get("chapters", [])}
        ai_objectives = data.get("objectives", objectives)
        
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
    from open_tutorai.models.database import CourseEnrollment

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
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"http://localhost:{port}/api/chat/completions",
                json=payload,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
            )
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        log.error(f"LLM call failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(status_code=502, detail="LLM call failed")
    except Exception as e:
        log.error(f"LLM call error: {e}")
        raise HTTPException(status_code=502, detail="Could not reach LLM")


    try:
        content = r.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown code fences
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        data = json.loads(content.strip())

        plan = {
            "chapters": data.get("chapters", [])
        }
        ai_objectives = data.get("objectives", body.objectives)  # NEW

        if "chapters" not in data:
            raise ValueError("missing 'chapters' key")
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
    return PlanWithObjectives(
        course_id=course_id,
        plan=plan,
        objectives=ai_objectives
    )



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
    from open_tutorai.models.database import CourseEnrollment

    count = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.course_id == course_id)
        .count()
    )
    return {"count": count}
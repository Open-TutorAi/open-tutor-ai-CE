import uuid
import json
import logging
import os
import random
import string
import traceback
from datetime import datetime
from typing import Optional, List
from open_webui.models.models import Models
from open_webui.models.users import Users
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from open_webui.internal.db import engine
from open_tutorai.utils.auth import get_verified_user
from open_tutorai.models.database import (
    Quiz,
    QuizQuestion,
    QuizSubmission,
    Course,
    CoursePlan,
    CourseEnrollment,
    StudentQuizAccess,
)

# ---------------------------------------------------------------
# Logging & Session Setup
# ---------------------------------------------------------------
log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter(tags=["Quizzes"])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------
class QuizGenerateRequest(BaseModel):
    title: str
    topic: str
    question_types: List[str]  # e.g., ["QCM", "True/False", "Short Answer"]
    total_questions: int = 5
    model: Optional[str] = "gpt-4o-mini"
    time_limit: Optional[int] = None
    limit_date: Optional[str] = None
    course_id: Optional[str] = None


class QuizSubmitRequest(BaseModel):
    answers: dict  # mapping question_id -> student_answer


class QuestionSaveItem(BaseModel):
    id: Optional[str] = None
    question_type: str
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: str


class QuizPublishRequest(BaseModel):
    questions: Optional[List[QuestionSaveItem]] = None


# ---------------------------------------------------------------
# Helper function to dictify Quiz
# ---------------------------------------------------------------
def _quiz_to_dict(quiz: Quiz) -> dict:
    questions_list = []
    for q in quiz.questions:
        questions_list.append(
            {
                "id": q.id,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
            }
        )
    return {
        "id": quiz.id,
        "teacher_id": quiz.teacher_id,
        "course_id": quiz.course_id,
        "title": quiz.title,
        "time_limit": quiz.time_limit,
        "total_questions": quiz.total_questions,
        "limit_date": quiz.limit_date,
        "model_used": quiz.model_used,
        "quiz_code": quiz.quiz_code,
        "status": quiz.status,
        "created_at": quiz.created_at.isoformat() if quiz.created_at else "",
        "updated_at": quiz.updated_at.isoformat() if quiz.updated_at else None,
        "questions": questions_list,
    }


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------


# 0. GET /teacher - list all quizzes created by teacher
@router.get("/teacher")
async def list_teacher_quizzes(
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    quizzes = db.query(Quiz).filter(Quiz.teacher_id == user.id).all()
    results = []
    for q in quizzes:
        qd = _quiz_to_dict(q)
        participants_count = (
            db.query(func.count(QuizSubmission.id))
            .filter(QuizSubmission.quiz_id == q.id)
            .scalar()
            or 0
        )
        qd["participants_count"] = participants_count
        results.append(qd)
    return results


# 0b. GET /student/dashboard - list quizzes submitted by the student
@router.get("/student/dashboard")
async def get_student_quiz_dashboard(
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    results = (
        db.query(QuizSubmission, Quiz)
        .join(Quiz, QuizSubmission.quiz_id == Quiz.id)
        .filter(QuizSubmission.student_id == user.id)
        .order_by(QuizSubmission.submitted_at.desc())
        .all()
    )
    return [
        {
            "quiz_id": q.id,
            "title": q.title,
            "total_questions": q.total_questions,
            "score": sub.score,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else "",
        }
        for sub, q in results
    ]


# 1. POST /generate - teacher configures and generates quiz draft via LLM
@router.post("/generate")
async def generate_quiz(
    body: QuizGenerateRequest,
    request: Request,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    # ── Step 1: Verify course ownership and extract course context (RAG) ──────────
    course_context = ""
    course_meta = ""

    if body.course_id:
        course = (
            db.query(Course)
            .filter(Course.id == body.course_id, Course.teacher_id == user.id)
            .first()
        )
        if not course:
            raise HTTPException(status_code=404, detail="Cours introuvable")

        # Build a structured metadata string from the Course record
        course_meta_parts = [
            f"Course Title: {course.title}",
            f"Level: {course.level}",
            f"Language: {course.language}",
        ]
        if course.category:
            course_meta_parts.append(f"Category: {course.category}")
        if course.objectives:
            course_meta_parts.append(f"Learning Objectives:\n{course.objectives}")
        course_meta = "\n".join(course_meta_parts)

        # Fetch the CoursePlan and flatten chapters + sections into a readable outline
        course_plan = (
            db.query(CoursePlan)
            .filter(CoursePlan.course_id == body.course_id)
            .order_by(CoursePlan.generated_at.desc())
            .first()
        )

        if course_plan and course_plan.plan_json:
            plan = course_plan.plan_json
            outline_lines = ["Course Outline (Chapters & Sections):"]
            for ch_idx, ch in enumerate(plan.get("chapters", []), start=1):
                ch_title = ch.get("title", f"Chapter {ch_idx}")
                outline_lines.append(f"  Chapter {ch_idx}: {ch_title}")
                for sec_idx, sec in enumerate(ch.get("sections", []), start=1):
                    sec_title = sec.get("title", f"Section {sec_idx}")
                    outline_lines.append(f"    {ch_idx}.{sec_idx} {sec_title}")
            course_context = "\n".join(outline_lines)
            log.info(
                f"Course context built: {len(plan.get('chapters', []))} chapters, "
                f"context length={len(course_context)} chars"
            )
        else:
            log.warning(
                f"No CoursePlan found for course {body.course_id}. "
                "Falling back to topic-only prompt."
            )
    else:
        log.info("No course_id provided — generating quiz from topic prompt only.")

    # ── Step 2: Select LLM with safety fallback ───────────────────────────────────
    model_to_use = body.model
    available_ids = []
    auth_header = request.headers.get("authorization", "")
    port = int(os.environ.get("PORT", "8080"))

    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(
                f"http://localhost:{port}/api/models",
                headers={"Authorization": auth_header},
            )
            if res.ok:
                models_data = res.json().get("data", [])
                available_ids = (
                    [getattr(m, "id", str(m)) for m in models_data]
                    if models_data
                    else []
                )
                log.info(f"Available models from API: {available_ids}")
    except Exception as e:
        log.error(f"Failed to fetch models from API: {e}")

    if not available_ids:
        try:
            all_models = Models.get_all_models()
            available_ids = (
                [getattr(m, "id", str(m)) for m in all_models] if all_models else []
            )
            log.info(f"Available models from Models class: {available_ids}")
        except Exception as e:
            log.error(f"Failed to fetch models from Models class: {e}")

    if not model_to_use and available_ids:
        model_to_use = available_ids[0]
        log.info(f"No model specified. Fallback to: {model_to_use}")

    if not model_to_use:
        raise HTTPException(
            status_code=503,
            detail="Aucun modèle LLM disponible. Veuillez vérifier que l'assistant IA est bien démarré.",
        )

    log.info(f"Generating quiz using model: {model_to_use}")

    # ── Step 3: Build context-aware system prompt ─────────────────────────────────
    # When a course is linked, bind its full outline into the prompt so the LLM
    # CANNOT generate questions outside of the actual course content.
    if course_context:
        system_prompt = f"""You are a strict expert examiner creating an assessment for a specific course.
Your ONLY source of truth for generating questions is the [COURSE CONTEXT] below.
Do NOT create general or hallucinated questions outside of this course content.
All questions MUST be directly derived from the course chapters, sections, and learning objectives listed.

[COURSE METADATA]
{course_meta}

[COURSE CONTEXT]
{course_context}

[TEACHER TOPIC FOCUS]
"{body.topic}"

Generate exactly {body.total_questions} questions that test knowledge from the course above.
Question types to use: {body.question_types}.
Return ONLY a valid JSON array of question objects — no markdown fences, no wrapper object, no extra text.

Each object in the array must follow this exact schema:
{{
  "question_type": "QCM" or "True/False" or "Short Answer",
  "question_text": "The question text (must be directly tied to a chapter/section from the course)",
  "options": ["Option A", "Option B", "Option C", "Option D"] (only for QCM, otherwise an empty array []),
  "correct_answer": "The correct answer (for QCM: must match one option EXACTLY. For True/False: EXACTLY 'Vrai' or 'Faux'. For Short Answer: short and precise)"
}}
Output ONLY the JSON array."""
    else:
        # No course context — fall back to topic-only prompt
        system_prompt = f"""You are an expert assessment designer.
Generate a quiz containing exactly {body.total_questions} questions about the topic: "{body.topic}".
The questions must cover the following question types: {body.question_types}.
Return ONLY a valid JSON array of question objects. Do not include markdown code blocks or text outside the JSON.

Each object in the array must follow this exact schema:
{{
  "question_type": "QCM" or "True/False" or "Short Answer",
  "question_text": "The text of the question",
  "options": ["Option A", "Option B", "Option C", "Option D"] (only for QCM, otherwise an empty array []),
  "correct_answer": "The correct answer (for QCM: must match one option EXACTLY. For True/False: EXACTLY 'Vrai' or 'Faux'. For Short Answer: short and precise)"
}}
Output ONLY the JSON array."""

    user_message = (
        f"Generate {body.total_questions} quiz questions on: '{body.topic}'."
        + (
            f" Focus on the course chapters and sections listed in the course context."
            if course_context
            else ""
        )
    )

    payload = {
        "model": model_to_use,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }

    # Prepare fallback candidate models
    candidate_models = [model_to_use]

    # 1. Stripped version (e.g. "qwen2.5-coder:7b" -> "qwen2.5-coder")
    if model_to_use and ":" in model_to_use:
        stripped = model_to_use.split(":")[0]
        if stripped not in candidate_models:
            candidate_models.append(stripped)

    # 2. Add other available models
    for m in available_ids:
        if m not in candidate_models:
            candidate_models.append(m)

    # 3. Add typical local Ollama default model tags
    for d in ["qwen2.5-coder", "llama3", "llama2", "mistral"]:
        if d not in candidate_models:
            candidate_models.append(d)

    r = None
    last_error_msg = ""
    success = False

    for attempt_model in candidate_models:
        log.info(f"Attempting quiz generation with model: {attempt_model}")
        payload["model"] = attempt_model
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
                log.info(f"LLM response status for {attempt_model}: {r.status_code}")
                r.raise_for_status()
                model_to_use = attempt_model
                success = True
                break
        except httpx.HTTPStatusError as e:
            error_body = r.text if r else ""
            log.error(
                f"LLM HTTP Status Error {e.response.status_code} for model {attempt_model}: {error_body}"
            )
            last_error_msg = f"HTTP {e.response.status_code}: {error_body}"
            if e.response.status_code == 400 or "model not found" in error_body.lower():
                log.warning(
                    f"Model {attempt_model} not found or failed. Trying next candidate..."
                )
                continue
            else:
                log.warning(
                    f"HTTP error {e.response.status_code} on model {attempt_model}. Trying next candidate..."
                )
                continue
            last_error_msg = f"HTTP {e.response.status_code}: {error_body}"
            if e.response.status_code == 400 or "model not found" in error_body.lower():
                log.warning(
                    f"Model {attempt_model} not found or failed. Trying next candidate..."
                )
                continue
            else:
                log.warning(
                    f"HTTP error {e.response.status_code} on model {attempt_model}. Trying next candidate..."
                )
                continue
        except Exception as e:
            log.error(f"LLM call failed for model {attempt_model}: {e}")
            last_error_msg = str(e)
            log.warning(
                f"Connection error on model {attempt_model}. Trying next candidate..."
            )
            continue

    if not success:
        raise HTTPException(
            status_code=502,
            detail=f"Le modèle LLM a retourné une erreur. Tous les modèles candidats ont échoué. Dernière erreur: {last_error_msg[:300]}",
        )

    # Parse LLM response - keep content in outer scope so except can log it
    content = ""
    try:
        raw_json = r.json()
        log.info(f"LLM raw response keys: {list(raw_json.keys())}")
        content = raw_json["choices"][0]["message"]["content"].strip()
        log.info(f"LLM content preview (first 200 chars): {content[:200]}")

        # Strip markdown code fences if model wrapped the JSON
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        questions_data = json.loads(content)

        if not isinstance(questions_data, list):
            raise ValueError(
                f"LLM did not return a JSON array, got: {type(questions_data).__name__}"
            )

        log.info(f"Parsed {len(questions_data)} questions from LLM response")
    except HTTPException:
        raise
    except Exception as e:
        log.error(
            f"Failed to parse LLM response for quiz: {e}. Content (first 500): {content[:500]}"
        )
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"L'assistant IA a renvoyé des données invalides: {str(e)[:200]}. Veuillez réessayer.",
        )

    # Save Quiz as "draft"
    try:
        quiz_id = str(uuid.uuid4())
        quiz = Quiz(
            id=quiz_id,
            teacher_id=user.id,
            course_id=body.course_id,
            title=body.title,
            time_limit=body.time_limit,
            total_questions=len(questions_data),
            limit_date=body.limit_date,
            model_used=model_to_use,
            status="draft",
        )
        db.add(quiz)

        # Save Questions
        for idx, q_data in enumerate(questions_data):
            question = QuizQuestion(
                id=str(uuid.uuid4()),
                quiz_id=quiz_id,
                question_type=q_data.get("question_type", "QCM"),
                question_text=q_data.get("question_text", ""),
                options=q_data.get("options", []),
                correct_answer=str(q_data.get("correct_answer", "")),
            )
            db.add(question)

        db.commit()
        db.refresh(quiz)
        log.info(f"Quiz draft {quiz_id} created by teacher {user.id}")
    except Exception as e:
        db.rollback()
        log.error(f"Database error saving quiz draft: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Erreur de base de données: {str(e)[:200]}"
        )

    return _quiz_to_dict(quiz)


# 2. POST /publish/{id} - Teacher validates draft and receives 6-char unique code
@router.post("/publish/{id}")
async def publish_quiz(
    id: str,
    body: Optional[QuizPublishRequest] = None,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == id, Quiz.teacher_id == user.id).first()
    if not quiz:
        raise HTTPException(
            status_code=404, detail="Quiz introuvable ou accès non autorisé"
        )

    if body and body.questions is not None:
        # Delete existing questions
        db.query(QuizQuestion).filter(QuizQuestion.quiz_id == id).delete()
        # Add the updated/manual questions
        for q_data in body.questions:
            q_id = q_data.id if q_data.id and not q_data.id.startswith("manual_") else str(uuid.uuid4())
            question = QuizQuestion(
                id=q_id,
                quiz_id=id,
                question_type=q_data.question_type,
                question_text=q_data.question_text,
                options=q_data.options or [],
                correct_answer=q_data.correct_answer,
            )
            db.add(question)
        quiz.total_questions = len(body.questions)

    if quiz.status == "published":
        return {
            "status": "success",
            "quiz_code": quiz.quiz_code,
            "quiz": _quiz_to_dict(quiz),
        }

    # Generate a unique 6-character uppercase alphanumeric code
    quiz_code = None
    for _ in range(100):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        exists = db.query(Quiz).filter(Quiz.quiz_code == code).first()
        if not exists:
            quiz_code = code
            break

    if not quiz_code:
        raise HTTPException(
            status_code=500,
            detail="Impossible de générer un code unique. Veuillez réessayer.",
        )

    quiz.quiz_code = quiz_code
    quiz.status = "published"
    quiz.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(quiz)

    log.info(f"Quiz {id} published with code {quiz_code} by teacher {user.id}")
    return {"status": "success", "quiz_code": quiz_code, "quiz": _quiz_to_dict(quiz)}


# 3. GET /join/{code} - Student retrieves quiz questions (excludes correct answers)
@router.get("/join/{code}")
async def join_quiz(
    code: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    quiz = db.query(Quiz).filter(func.upper(Quiz.quiz_code) == code.upper()).first()
    if not quiz:
        raise HTTPException(
            status_code=404, detail="Code de quiz invalide ou quiz introuvable"
        )

    if quiz.status != "published":
        raise HTTPException(
            status_code=400, detail="Ce quiz n'est pas encore publié par l'enseignant"
        )

    # Create or retrieve student quiz access record to unlock the quiz
    access = (
        db.query(StudentQuizAccess)
        .filter(
            StudentQuizAccess.student_id == user.id,
            StudentQuizAccess.quiz_id == quiz.id,
        )
        .first()
    )
    if not access:
        access = StudentQuizAccess(
            student_id=user.id,
            quiz_id=quiz.id,
            unlocked_at=datetime.utcnow(),
        )
        db.add(access)
        db.commit()

    # Exclude correct_answer from the payload!
    questions_payload = []
    for q in quiz.questions:
        questions_payload.append(
            {
                "id": q.id,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "options": q.options,
            }
        )

    return {
        "id": quiz.id,
        "title": quiz.title,
        "time_limit": quiz.time_limit,
        "total_questions": quiz.total_questions,
        "limit_date": quiz.limit_date,
        "questions": questions_payload,
    }


# 4. POST /submit/{id} - Student submits quiz answers and gets scored instantly
@router.post("/submit/{id}")
async def submit_quiz(
    id: str,
    body: QuizSubmitRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable")

    if quiz.status != "published":
        raise HTTPException(status_code=400, detail="Ce quiz n'est pas actif")

    # Verify that the student has unlocked the quiz
    access = (
        db.query(StudentQuizAccess)
        .filter(
            StudentQuizAccess.student_id == user.id,
            StudentQuizAccess.quiz_id == id,
        )
        .first()
    )
    if not access:
        raise HTTPException(
            status_code=403,
            detail="Accès interdit. Vous devez d'abord valider le code d'accès pour ce quiz.",
        )

    # Prevent multiple submissions by the same student for the same quiz
    existing_submission = (
        db.query(QuizSubmission)
        .filter(
            QuizSubmission.quiz_id == id,
            QuizSubmission.student_id == user.id,
        )
        .first()
    )
    if existing_submission:
        raise HTTPException(status_code=400, detail="Vous avez déjà soumis ce quiz.")

    score = 0
    total = len(quiz.questions)

    # Compute score instantly
    for q in quiz.questions:
        student_ans = str(body.answers.get(q.id, "")).strip().lower()
        correct_ans = str(q.correct_answer).strip().lower()

        # Soft comparison for True/False translations
        if q.question_type == "True/False":
            true_vals = ["vrai", "true", "yes", "oui"]
            false_vals = ["faux", "false", "no", "non"]
            if student_ans in true_vals and correct_ans in true_vals:
                score += 1
            elif student_ans in false_vals and correct_ans in false_vals:
                score += 1
        elif student_ans == correct_ans:
            score += 1

    submission = QuizSubmission(
        id=str(uuid.uuid4()),
        quiz_id=id,
        student_id=user.id,
        answers=body.answers,
        score=score,
        submitted_at=datetime.utcnow(),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    log.info(f"Student {user.id} submitted quiz {id}. Score: {score}/{total}")
    return {
        "submission_id": submission.id,
        "score": score,
        "total": total,
        "submitted_at": submission.submitted_at.isoformat(),
    }


# 5. GET /teacher/analytics/{id} - Teacher views dashboard analytics and distributions
@router.get("/teacher/analytics/{id}")
async def get_teacher_analytics(
    id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == id, Quiz.teacher_id == user.id).first()
    if not quiz:
        raise HTTPException(
            status_code=404, detail="Quiz introuvable ou accès non autorisé"
        )

    submissions = quiz.submissions
    total_participants = len(submissions)

    if total_participants == 0:
        return {
            "quiz_title": quiz.title,
            "quiz_code": quiz.quiz_code,
            "total_participants": 0,
            "average_score": 0.0,
            "high_score": 0.0,
            "low_score": 0.0,
            "submissions": [],
            "distribution": {},
        }

    scores = [s.score for s in submissions]
    average_score = sum(scores) / total_participants
    high_score = max(scores)
    low_score = min(scores)

    # Score distribution calculations
    distribution = {}
    for s in scores:
        distribution[s] = distribution.get(s, 0) + 1

    # Format student submissions with names/emails
    submissions_formatted = []
    for s in submissions:
        student_name = "Étudiant anonyme"
        try:
            student = Users.get_user_by_id(s.student_id)
            if student:
                student_name = getattr(student, "name", None) or getattr(
                    student, "email", "Étudiant anonyme"
                )
        except Exception:
            pass

        submissions_formatted.append(
            {
                "id": s.id,
                "student_name": student_name,
                "score": s.score,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else "",
            }
        )

    return {
        "quiz_title": quiz.title,
        "quiz_code": quiz.quiz_code,
        "total_participants": total_participants,
        "average_score": round(average_score, 2),
        "high_score": high_score,
        "low_score": low_score,
        "submissions": submissions_formatted,
        "distribution": distribution,
    }


# ---------------------------------------------------------------
# Student Assignments Router
# ---------------------------------------------------------------
class JoinByCodeRequest(BaseModel):
    code: str


student_assignments_router = APIRouter(
    prefix="/student/assignments", tags=["Student Assignments"]
)


@student_assignments_router.post("/join-by-code")
async def join_assignment_by_code(
    body: JoinByCodeRequest,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    code = body.code.strip().upper()
    quiz = db.query(Quiz).filter(func.upper(Quiz.quiz_code) == code).first()
    if not quiz:
        raise HTTPException(
            status_code=404, detail="Code de quiz invalide ou quiz introuvable"
        )
    if quiz.status != "published":
        raise HTTPException(
            status_code=400, detail="Ce quiz n'est pas encore publié par l'enseignant"
        )

    # Create or retrieve student quiz access record to unlock the quiz
    access = (
        db.query(StudentQuizAccess)
        .filter(
            StudentQuizAccess.student_id == user.id,
            StudentQuizAccess.quiz_id == quiz.id,
        )
        .first()
    )
    if not access:
        access = StudentQuizAccess(
            student_id=user.id,
            quiz_id=quiz.id,
            unlocked_at=datetime.utcnow(),
        )
        db.add(access)
        db.commit()

    course_title = "Quiz"
    if quiz.course_id:
        course = db.query(Course).filter(Course.id == quiz.course_id).first()
        if course:
            course_title = course.title

    # Check if student already submitted a response
    submission = (
        db.query(QuizSubmission)
        .filter(QuizSubmission.quiz_id == quiz.id, QuizSubmission.student_id == user.id)
        .first()
    )
    status = "completed" if submission else "pending"

    return {
        "id": quiz.id,
        "course": course_title,
        "points": quiz.total_questions * 10,
        "title": quiz.title,
        "description": f"Quiz d'évaluation - {quiz.total_questions} questions.",
        "status": status,
        "due": quiz.limit_date if quiz.limit_date else "Pas de date limite",
        "quiz_code": quiz.quiz_code,
    }


@student_assignments_router.get("")
async def list_student_assignments(
    codes: Optional[str] = None,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    # 1. Fetch enrolled course IDs
    enrollments = (
        db.query(CourseEnrollment).filter(CourseEnrollment.student_id == user.id).all()
    )
    course_ids = [e.course_id for e in enrollments]

    # Fetch unlocked quiz IDs for the current student
    unlocked_accesses = (
        db.query(StudentQuizAccess.quiz_id)
        .filter(StudentQuizAccess.student_id == user.id)
        .all()
    )
    unlocked_quiz_ids = {a.quiz_id for a in unlocked_accesses}

    # 2. Fetch quizzes associated with enrolled courses and unlocked by student
    quizzes = (
        db.query(Quiz)
        .filter(
            Quiz.course_id.in_(course_ids),
            Quiz.status == "published",
            Quiz.id.in_(unlocked_quiz_ids),
        )
        .all()
        if course_ids
        else []
    )

    # 3. Handle additional standalone quiz codes from the query parameter
    standalone_codes = []
    if codes:
        standalone_codes = [c.strip().upper() for c in codes.split(",") if c.strip()]

    if standalone_codes:
        standalone_quizzes = (
            db.query(Quiz)
            .filter(
                func.upper(Quiz.quiz_code).in_(standalone_codes),
                Quiz.status == "published",
                Quiz.id.in_(unlocked_quiz_ids),
            )
            .all()
        )
        # Merge, avoiding duplicates
        existing_quiz_ids = {q.id for q in quizzes}
        for sq in standalone_quizzes:
            if sq.id not in existing_quiz_ids:
                quizzes.append(sq)

    # 4. Map each quiz to assignment format
    assignments_list = []
    for quiz in quizzes:
        course_title = "Quiz"
        if quiz.course_id:
            course_obj = db.query(Course).filter(Course.id == quiz.course_id).first()
            if course_obj:
                course_title = course_obj.title

        # Query submission for this student
        submission = (
            db.query(QuizSubmission)
            .filter(
                QuizSubmission.quiz_id == quiz.id, QuizSubmission.student_id == user.id
            )
            .first()
        )

        status = "completed" if submission else "pending"
        # Optional: Check if deadline has passed to set overdue
        if status == "pending" and quiz.limit_date:
            try:
                # Expect limit_date in format YYYY-MM-DD
                limit_dt = datetime.strptime(quiz.limit_date, "%Y-%m-%d")
                if datetime.utcnow().date() > limit_dt.date():
                    status = "overdue"
            except Exception:
                try:
                    limit_dt = datetime.fromisoformat(
                        quiz.limit_date.replace("Z", "+00:00")
                    )
                    if datetime.utcnow() > limit_dt:
                        status = "overdue"
                except Exception:
                    pass

        # Extract score, submitted_at, time_spent
        score = None
        total = quiz.total_questions
        submitted_at = None
        time_spent = None

        if submission:
            score = submission.score
            submitted_at = (
                submission.submitted_at.isoformat() if submission.submitted_at else None
            )
            # Retrieve time_spent from answers under __time_spent__ key
            if isinstance(submission.answers, dict):
                time_spent = submission.answers.get("__time_spent__")

        assignments_list.append(
            {
                "id": quiz.id,
                "course": course_title,
                "points": quiz.total_questions * 10,
                "title": quiz.title,
                "description": f"Quiz d'évaluation - {quiz.total_questions} questions.",
                "status": status,
                "due": quiz.limit_date if quiz.limit_date else "Pas de date limite",
                "quiz_code": quiz.quiz_code,
                # Completed details
                "score": score,
                "total": total,
                "submitted_at": submitted_at,
                "time_spent": time_spent,
                "limit_date": quiz.limit_date,
            }
        )

    return assignments_list

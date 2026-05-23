import uuid
import json
import logging
import os
import random
import string
from datetime import datetime
from typing import Optional, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from open_webui.internal.db import engine
from open_tutorai.utils.auth import get_verified_user
from open_tutorai.models.database import Quiz, QuizQuestion, QuizSubmission, Course

# ---------------------------------------------------------------
# Logging & Session Setup
# ---------------------------------------------------------------
log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])
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

# ---------------------------------------------------------------
# Helper function to dictify Quiz
# ---------------------------------------------------------------
def _quiz_to_dict(quiz: Quiz) -> dict:
    questions_list = []
    for q in quiz.questions:
        questions_list.append({
            "id": q.id,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "options": q.options,
            "correct_answer": q.correct_answer
        })
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
        "questions": questions_list
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
    return [_quiz_to_dict(q) for q in quizzes]


# 1. POST /generate - teacher configures and generates quiz draft via LLM
@router.post("/generate")
async def generate_quiz(
    body: QuizGenerateRequest,
    request: Request,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    # Verify course if provided
    if body.course_id:
        course = db.query(Course).filter(Course.id == body.course_id, Course.teacher_id == user.id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Cours introuvable")

    # Select LLM with safety fallback
    model_to_use = body.model
    try:
        from open_webui.models.models import Models
        all_models = Models.get_all_models()
        available_ids = [getattr(m, "id", str(m)) for m in all_models] if all_models else []
    except Exception:
        available_ids = []

    if available_ids:
        if not model_to_use or model_to_use not in available_ids:
            # Fallback to the first available model if gpt-4o-mini is not loaded
            model_to_use = available_ids[0]

    log.info(f"Generating quiz using model: {model_to_use}")

    # Build Assessment Generation System Prompt
    system_prompt = f"""You are an expert assessment designer.
Generate a quiz containing exactly {body.total_questions} questions about the topic: "{body.topic}".
The questions must cover the following question types: {body.question_types}.
Return ONLY a valid JSON array of question objects. Do not wrap in a parent object. Do not include markdown code blocks or text outside the JSON.

Each object in the array must follow this exact schema:
{{
  "question_type": "QCM" or "True/False" or "Short Answer",
  "question_text": "The text of the question",
  "options": ["Option A", "Option B", "Option C", "Option D"] (only for QCM, otherwise an empty array []),
  "correct_answer": "The correct answer (for QCM, must match one of the options EXACTLY. For True/False, must be EXACTLY 'Vrai' or 'Faux'. For Short Answer, keep it short and precise)"
}}
Ensure the correct_answer matches the options exactly for QCM. If True/False, use 'Vrai' or 'Faux'.
Output ONLY the JSON array."""

    auth_header = request.headers.get("authorization", "")
    port = int(os.environ.get("PORT", "8080"))

    payload = {
        "model": model_to_use,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a quiz of {body.total_questions} questions on '{body.topic}' now."}
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
    except Exception as e:
        log.error(f"LLM call failed for quiz generation: {e}")
        raise HTTPException(status_code=500, detail=f"LLM backend error: {str(e)}")

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
        questions_data = json.loads(content)
        
        if not isinstance(questions_data, list):
            raise ValueError("LLM did not return a JSON array")
    except Exception as e:
        log.error(f"Failed to parse LLM response for quiz: {e}. Content: {content[:500]}")
        raise HTTPException(status_code=500, detail="L'assistant IA a renvoyé des données invalides. Veuillez réessayer.")

    # Save Quiz as "draft"
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
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
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
    return _quiz_to_dict(quiz)


# 2. POST /publish/{id} - Teacher validates draft and receives 6-char unique code
@router.post("/publish/{id}")
async def publish_quiz(
    id: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == id, Quiz.teacher_id == user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz introuvable ou accès non autorisé")

    if quiz.status == "published":
        return {
            "status": "success",
            "quiz_code": quiz.quiz_code,
            "quiz": _quiz_to_dict(quiz)
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
        raise HTTPException(status_code=500, detail="Impossible de générer un code unique. Veuillez réessayer.")

    quiz.quiz_code = quiz_code
    quiz.status = "published"
    quiz.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(quiz)

    log.info(f"Quiz {id} published with code {quiz_code} by teacher {user.id}")
    return {
        "status": "success",
        "quiz_code": quiz_code,
        "quiz": _quiz_to_dict(quiz)
    }


# 3. GET /join/{code} - Student retrieves quiz questions (excludes correct answers)
@router.get("/join/{code}")
async def join_quiz(
    code: str,
    user=Depends(get_verified_user),
    db=Depends(get_db),
):
    quiz = db.query(Quiz).filter(func.upper(Quiz.quiz_code) == code.upper()).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Code de quiz invalide ou quiz introuvable")

    if quiz.status != "published":
        raise HTTPException(status_code=400, detail="Ce quiz n'est pas encore publié par l'enseignant")

    # Exclude correct_answer from the payload!
    questions_payload = []
    for q in quiz.questions:
        questions_payload.append({
            "id": q.id,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "options": q.options,
        })

    return {
        "id": quiz.id,
        "title": quiz.title,
        "time_limit": quiz.time_limit,
        "total_questions": quiz.total_questions,
        "limit_date": quiz.limit_date,
        "questions": questions_payload
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
        submitted_at=datetime.utcnow()
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    log.info(f"Student {user.id} submitted quiz {id}. Score: {score}/{total}")
    return {
        "submission_id": submission.id,
        "score": score,
        "total": total,
        "submitted_at": submission.submitted_at.isoformat()
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
        raise HTTPException(status_code=404, detail="Quiz introuvable ou accès non autorisé")

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
            "distribution": {}
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
            from open_webui.models.users import Users
            student = Users.get_user_by_id(s.student_id)
            if student:
                student_name = getattr(student, "name", None) or getattr(student, "email", "Étudiant anonyme")
        except Exception:
            pass

        submissions_formatted.append({
            "id": s.id,
            "student_name": student_name,
            "score": s.score,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else ""
        })

    return {
        "quiz_title": quiz.title,
        "quiz_code": quiz.quiz_code,
        "total_participants": total_participants,
        "average_score": round(average_score, 2),
        "high_score": high_score,
        "low_score": low_score,
        "submissions": submissions_formatted,
        "distribution": distribution
    }

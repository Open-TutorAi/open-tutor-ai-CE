from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from open_webui.internal.db import engine
from sqlalchemy import select
from ..models.database import FAQQuestion
from ..utils.email import send_faq_notification
from typing import Optional

router = APIRouter(tags=["faq-questions"])

class FAQSubmit(BaseModel):
    email: str
    question: str

class FAQReponse(BaseModel):
    reponse: str

class FAQUpdate(BaseModel):
    statut: str

# === ROUTES PUBLIQUES ===
@router.post("/api/faq-question")
async def submit_faq_question(form_data: FAQSubmit):
    try:
        with Session(engine) as session:
            new_q = FAQQuestion(
                email=form_data.email,
                question=form_data.question,
                statut="en_attente"
            )
            session.add(new_q)
            session.commit()
            send_faq_notification(form_data.email, form_data.question)
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ROUTES ADMIN ===
@router.get("/api/admin/faq-questions")
async def get_all_questions():
    try:
        with Session(engine) as session:
            questions = session.execute(select(FAQQuestion)).scalars().all()
            return [
                {
                    "id": q.id,
                    "email": q.email,
                    "question": q.question,
                    "reponse": q.reponse,
                    "statut": q.statut,
                    "created_at": q.created_at.isoformat() if q.created_at else None
                }
                for q in questions
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/admin/faq-questions/{question_id}")
async def update_question_statut(question_id: int, update: FAQUpdate):
    try:
        with Session(engine) as session:
            question = session.get(FAQQuestion, question_id)
            if not question:
                raise HTTPException(status_code=404, detail="Question non trouvée")
            question.statut = update.statut
            session.commit()
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/faq-questions/{question_id}/repondre")
async def repondre_question(question_id: int, data: FAQReponse):
    try:
        with Session(engine) as session:
            question = session.get(FAQQuestion, question_id)
            if not question:
                raise HTTPException(status_code=404, detail="Question non trouvée")
            question.reponse = data.reponse
            question.statut = "repondu"
            session.commit()
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/admin/faq-questions/{question_id}")
async def delete_question(question_id: int):
    try:
        with Session(engine) as session:
            question = session.get(FAQQuestion, question_id)
            if not question:
                raise HTTPException(status_code=404, detail="Question non trouvée")
            session.delete(question)
            session.commit()
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
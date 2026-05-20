from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from open_webui.internal.db import engine
from sqlalchemy import select
from ..models.database import FAQQuestion
from ..utils.email import send_faq_notification

router = APIRouter(tags=["faq-questions"])

class FAQSubmit(BaseModel):
    email: str
    question: str

@router.post("/api/faq-question")
async def submit_faq_question(form_data: FAQSubmit):
    try:
        with Session(engine) as session:
            # 1. Sauvegarder en Base de données
            new_q = FAQQuestion(
                email=form_data.email,
                question=form_data.question,
                statut="en_attente"
            )
            session.add(new_q)
            session.commit()
            
            # 2. Envoyer l'Email
            send_faq_notification(form_data.email, form_data.question)
            
            return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
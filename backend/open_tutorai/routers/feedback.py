from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from open_webui.internal.db import engine, Base
from sqlalchemy import select
from ..models.database import UserFeedback

router = APIRouter(tags=["user-feedback"])

class FeedbackCreate(BaseModel):
    name: str | None = None
    message: str

# Créer la table si elle n'existe pas (sécurité)
Base.metadata.create_all(bind=engine, tables=[UserFeedback.__table__], checkfirst=True)

@router.post("/api/feedback")
async def create_feedback(form_data: FeedbackCreate):
    try:
        # Créer une session manuellement (plus fiable avec async)
        with Session(engine) as session:
            new_feedback = UserFeedback(name=form_data.name, message=form_data.message)
            session.add(new_feedback)
            session.commit()
            session.refresh(new_feedback)
            return {"status": "success", "data": new_feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/feedback")
async def get_feedbacks():
    try:
        with Session(engine) as session:
            # Récupère tous les feedbacks, les plus récents en premier
            stmt = select(UserFeedback).order_by(UserFeedback.created_at.desc())
            feedbacks = session.execute(stmt).scalars().all()
            return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""Flashcard routes for spaced repetition learning."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from data.database import get_db
from data.repositories.flashcard_repository import FlashcardRepository
from ai.llm.flashcard_generator import FlashcardGenerator
from ai.pdf.pdf_extractor import PDFExtractor
from gateway.http.dependencies import get_current_user
import logging

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/flashcards", tags=["flashcards"])


# --- Modèles Pydantic ---
class GenerateRequest(BaseModel):
    content: str
    num_cards: int = 5
    lesson_id: Optional[str] = None
    tag: Optional[str] = None


class ReviewRequest(BaseModel):
    card_id: str
    correct: bool


class FlashcardResponse(BaseModel):
    id: str
    question: str
    answer: str
    tag: Optional[str]
    box: int
    next_review: str
    mastery_percentage: float


# --- Endpoints ---
# ⚠️ IMPORTANT : Les routes STATIQUES doivent être AVANT les routes DYNAMIQUES

@router.post("/generate", response_model=List[FlashcardResponse])
async def generate_flashcards(
    request: GenerateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Génère des flashcards à partir d'un contenu de cours"""
    try:
        log.info(f"Génération de {request.num_cards} flashcards pour user {current_user.id}")
        
        generator = FlashcardGenerator()
        cards_data = await generator.generate_from_content(
            request.content,
            request.num_cards
        )
        
        repo = FlashcardRepository(db)
        saved_cards = repo.create_batch(
            user_id=current_user.id,
            cards=cards_data,
            lesson_id=request.lesson_id,
            tag=request.tag
        )
        
        return [card.to_dict() for card in saved_cards]
        
    except Exception as e:
        log.error(f"❌ Erreur génération: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-pdf", response_model=List[FlashcardResponse])
async def generate_from_pdf(
    file: UploadFile = File(...),
    num_cards: int = 5,
    tag: Optional[str] = None,
    lesson_id: Optional[str] = None,
    model: str = "qwen2.5:7b",
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Génère des flashcards à partir d'un PDF uploadé"""
    try:
        content = await file.read()
        
        error = PDFExtractor.validate_file(file.filename, file.content_type, len(content))
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        log.info(f"📄 Upload PDF: {file.filename} ({len(content)} bytes)")
        
        extracted_text = await PDFExtractor.extract_text(content, file.filename)
        
        if not extracted_text or len(extracted_text) < 100:
            raise HTTPException(
                status_code=400, 
                detail="Impossible d'extraire suffisamment de texte du PDF."
            )
        
        generator = FlashcardGenerator(model_name=model)
        cards_data = await generator.generate_from_content(extracted_text, num_cards)
        
        repo = FlashcardRepository(db)
        saved_cards = repo.create_batch(
            user_id=current_user.id,
            cards=cards_data,
            lesson_id=lesson_id,
            tag=tag or file.filename.replace('.pdf', '')
        )
        
        return [card.to_dict() for card in saved_cards]
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"❌ Erreur génération depuis PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/due", response_model=List[FlashcardResponse])
async def get_due_cards(
    limit: int = 20,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les cartes à réviser aujourd'hui"""
    repo = FlashcardRepository(db)
    cards = repo.get_due_cards(user_id=current_user.id, limit=limit)
    return [card.to_dict() for card in cards]


@router.get("/tags")
async def get_tags(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les tags de l'utilisateur"""
    repo = FlashcardRepository(db)
    tags = repo.get_tags(user_id=current_user.id)
    return {"tags": tags}


@router.get("/stats")
async def get_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Statistiques de maîtrise"""
    repo = FlashcardRepository(db)
    stats = repo.get_stats(user_id=current_user.id)
    stats_by_tag = repo.get_stats_by_tag(user_id=current_user.id)
    return {**stats, "by_tag": stats_by_tag}


# ⚠️ ROUTE STATIQUE : doit être AVANT /due/{tag}
@router.delete("/delete-all")
async def delete_all_cards(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime TOUTES les flashcards de l'utilisateur"""
    from data.models.flashcard import Flashcard
    
    count = db.query(Flashcard).filter(Flashcard.user_id == current_user.id).count()
    db.query(Flashcard).filter(Flashcard.user_id == current_user.id).delete()
    db.commit()
    
    log.info(f"🗑️ {count} cartes supprimées pour user {current_user.id}")
    
    return {"success": True, "deleted_count": count}


# ⚠️ ROUTE DYNAMIQUE : doit être APRÈS /delete-all
@router.get("/due/{tag}", response_model=List[FlashcardResponse])
async def get_due_cards_by_tag(
    tag: str,
    limit: int = 20,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les cartes à réviser filtrées par tag"""
    repo = FlashcardRepository(db)
    cards = repo.get_due_cards_by_tag(user_id=current_user.id, tag=tag, limit=limit)
    return [card.to_dict() for card in cards]


@router.post("/review")
async def review_card(
    request: ReviewRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enregistre une révision (correct/incorrect)"""
    repo = FlashcardRepository(db)
    card = repo.update_review(
        card_id=request.card_id,
        user_id=current_user.id,
        correct=request.correct
    )
    
    if not card:
        raise HTTPException(status_code=404, detail="Carte non trouvée")
    
    return {"success": True, "card": card.to_dict()}


# ⚠️ ROUTE DYNAMIQUE : doit être EN DERNIER
@router.delete("/{card_id}")
async def delete_card(
    card_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime une flashcard spécifique"""
    repo = FlashcardRepository(db)
    success = repo.delete(card_id=card_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Carte non trouvée")
    
    return {"success": True}

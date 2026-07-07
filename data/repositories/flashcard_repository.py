"""Flashcard repository for database operations."""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from data.models.flashcard import Flashcard


class FlashcardRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, question: str, answer: str, lesson_id: Optional[str] = None, tag: Optional[str] = None) -> Flashcard:
        """Crée une nouvelle flashcard"""
        flashcard = Flashcard(
            user_id=user_id,
            question=question,
            answer=answer,
            lesson_id=lesson_id,
            tag=tag,
            next_review=datetime.utcnow() - timedelta(minutes=1)
        )
        self.db.add(flashcard)
        self.db.commit()
        self.db.refresh(flashcard)
        return flashcard

    def create_batch(self, user_id: str, cards: List[dict], lesson_id: Optional[str] = None, tag: Optional[str] = None) -> List[Flashcard]:
        """Crée plusieurs flashcards en batch"""
        flashcards = []
        now_minus_1min = datetime.utcnow() - timedelta(minutes=1)
        
        for card_data in cards:
            flashcard = Flashcard(
                user_id=user_id,
                question=card_data["question"],
                answer=card_data["answer"],
                lesson_id=lesson_id,
                tag=tag,
                next_review=now_minus_1min
            )
            self.db.add(flashcard)
            flashcards.append(flashcard)
        
        self.db.commit()
        for fc in flashcards:
            self.db.refresh(fc)
        return flashcards

    def get_due_cards(self, user_id: str, limit: int = 20) -> List[Flashcard]:
        """Retourne les cartes à réviser (next_review <= now)"""
        now = datetime.utcnow()
        return (
            self.db.query(Flashcard)
            .filter(Flashcard.user_id == user_id)
            .filter(Flashcard.next_review <= now)
            .order_by(Flashcard.box.asc(), Flashcard.next_review.asc())
            .limit(limit)
            .all()
        )

    def get_due_cards_by_tag(self, user_id: str, tag: str, limit: int = 20) -> List[Flashcard]:
        """Retourne les cartes à réviser filtrées par tag"""
        now = datetime.utcnow()
        return (
            self.db.query(Flashcard)
            .filter(Flashcard.user_id == user_id)
            .filter(Flashcard.tag == tag)
            .filter(Flashcard.next_review <= now)
            .order_by(Flashcard.box.asc(), Flashcard.next_review.asc())
            .limit(limit)
            .all()
        )

    def get_by_id(self, card_id: str, user_id: str) -> Optional[Flashcard]:
        """Récupère une carte par son ID"""
        return (
            self.db.query(Flashcard)
            .filter(Flashcard.id == card_id, Flashcard.user_id == user_id)
            .first()
        )

    def update_review(self, card_id: str, user_id: str, correct: bool) -> Optional[Flashcard]:
        """Enregistre une révision et met à jour la carte"""
        card = self.get_by_id(card_id, user_id)
        if card:
            card.review(correct)
            self.db.commit()
            self.db.refresh(card)
        return card

    def get_tags(self, user_id: str) -> List[str]:
        """Retourne la liste des tags utilisés par l'utilisateur"""
        results = (
            self.db.query(Flashcard.tag)
            .filter(Flashcard.user_id == user_id, Flashcard.tag.isnot(None))
            .distinct()
            .all()
        )
        return [r[0] for r in results if r[0]]

    def get_stats(self, user_id: str) -> dict:
        """Statistiques de maîtrise pour un utilisateur"""
        now = datetime.utcnow()
        
        total = self.db.query(Flashcard).filter(Flashcard.user_id == user_id).count()
        mastered = (
            self.db.query(Flashcard)
            .filter(Flashcard.user_id == user_id, Flashcard.box == 5)
            .count()
        )
        to_review = (
            self.db.query(Flashcard)
            .filter(Flashcard.user_id == user_id, Flashcard.next_review <= now)
            .count()
        )
        learning = total - mastered
        
        return {
            "total": total,
            "mastered": mastered,
            "to_review": to_review,
            "learning": learning
        }

    def get_stats_by_tag(self, user_id: str) -> dict:
        """Statistiques par tag"""
        now = datetime.utcnow()
        tags = self.get_tags(user_id)
        stats_by_tag = {}
        
        for tag in tags:
            total = (
                self.db.query(Flashcard)
                .filter(Flashcard.user_id == user_id, Flashcard.tag == tag)
                .count()
            )
            mastered = (
                self.db.query(Flashcard)
                .filter(Flashcard.user_id == user_id, Flashcard.tag == tag, Flashcard.box == 5)
                .count()
            )
            to_review = (
                self.db.query(Flashcard)
                .filter(Flashcard.user_id == user_id, Flashcard.tag == tag, Flashcard.next_review <= now)
                .count()
            )
            
            stats_by_tag[tag] = {
                "total": total,
                "mastered": mastered,
                "to_review": to_review
            }
        
        return stats_by_tag

    def delete(self, card_id: str, user_id: str) -> bool:
        """Supprime une carte"""
        card = self.get_by_id(card_id, user_id)
        if card:
            self.db.delete(card)
            self.db.commit()
            return True
        return False

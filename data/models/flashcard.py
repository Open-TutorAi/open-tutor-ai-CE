"""Flashcard models for spaced repetition learning."""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, DateTime, Integer, String, Text
from data.database import Base


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    lesson_id = Column(String(36), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tag = Column(String(100), nullable=True, index=True)
    
    # Algorithme de Leitner (boîte 1 à 5)
    box = Column(Integer, default=1, nullable=False)
    next_review = Column(DateTime, default=datetime.utcnow, nullable=False)
    times_reviewed = Column(Integer, default=0, nullable=False)
    times_correct = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Intervalle de révision par boîte (en jours)
    BOX_INTERVALS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 30}

    def review(self, correct: bool):
        """Met à jour la carte selon l'algorithme de Leitner"""
        self.times_reviewed += 1
        if correct:
            self.times_correct += 1
            self.box = min(5, self.box + 1)
        else:
            self.box = 1
        
        # Calcule la prochaine révision
        interval = self.BOX_INTERVALS[self.box]
        self.next_review = datetime.utcnow() + timedelta(days=interval)

    @property
    def mastery_percentage(self) -> float:
        if self.times_reviewed == 0:
            return 0.0
        return (self.times_correct / self.times_reviewed) * 100

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lesson_id": self.lesson_id,
            "question": self.question,
            "answer": self.answer,
            "tag": self.tag,
            "box": self.box,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "times_reviewed": self.times_reviewed,
            "times_correct": self.times_correct,
            "mastery_percentage": self.mastery_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

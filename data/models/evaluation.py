"""Modèle Evaluation — QCM générés par l'IA depuis les sessions."""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from data.database import Base


class Evaluation(Base):
    """QCM généré par l'IA basé sur une session de chat."""

    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Qui a créé l'éval (le parent)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    # L'étudiant concerné
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    # Le soutien et le chat source
    support_id = Column(String(36), ForeignKey("supports.id"), nullable=True)
    chat_id = Column(String(36), nullable=True)
    # Métadonnées
    title = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=True)
    # Questions générées par l'IA — JSON :
    # [{"id": 1, "question": "...", "choices": ["A","B","C","D"], "correct": "A", "explanation": "..."}]
    questions = Column(JSON, nullable=False, default=list)
    # Réponses de l'étudiant — JSON : {"1": "A", "2": "C", ...}
    student_answers = Column(JSON, nullable=True)
    # Résultats calculés
    score = Column(Float, nullable=True)          # 0-100
    nb_correct = Column(Integer, nullable=True)
    nb_total = Column(Integer, nullable=True)
    # Statut : pending | completed
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_by": self.created_by,
            "student_id": self.student_id,
            "support_id": self.support_id,
            "chat_id": self.chat_id,
            "title": self.title,
            "subject": self.subject,
            "questions": self.questions,
            "student_answers": self.student_answers,
            "score": self.score,
            "nb_correct": self.nb_correct,
            "nb_total": self.nb_total,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
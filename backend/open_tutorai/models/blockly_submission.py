# backend/open_tutorai/models/blockly_submission.py
"""
Modèles SQLAlchemy pour le module Blockly.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import types

# UUID compatible SQLite et PostgreSQL
class UUID(types.TypeDecorator):
    impl = types.String
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
    def process_result_value(self, value, dialect):
        if value is not None:
            return value

from open_tutorai.models.database import Base


class BlocklySubmission(Base):
    """
    Enregistre chaque soumission officielle d'un exercice Blockly.
    """
    __tablename__ = "blockly_submissions"

    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False, index=True)
    assignment_id = Column(String, nullable=False, index=True)

    # Le workspace Blockly sérialisé en XML
    blocks_json = Column(Text, nullable=True)

    # Le code Python généré
    python_code = Column(Text, nullable=False)

    # Résultats d'exécution
    execution_stdout = Column(Text, default="")
    execution_error = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0)

    # Résultats des cas de test (JSON sérialisé)
    test_results_json = Column(Text, nullable=True)

    # Évaluation
    score = Column(Integer, nullable=True)  # 0-100
    ai_feedback = Column(Text, nullable=True)

    # Métadonnées
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_final = Column(Boolean, default=True)


class BlocklyWorkspaceDraft(Base):
    """
    Sauvegarde automatique du workspace Blockly en cours d'édition.
    Un seul brouillon par (étudiant, exercice).
    """
    __tablename__ = "blockly_workspace_drafts"

    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False)
    assignment_id = Column(String, nullable=False)

    # XML du workspace Blockly
    blocks_json = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('student_id', 'assignment_id', name='uq_blockly_draft'),
    )
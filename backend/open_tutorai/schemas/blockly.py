# backend/schemas/blockly.py
"""
Schémas Pydantic pour le module Blockly.
Validation stricte des données entrantes et sortantes.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID


# ─── Requêtes (Input) ────────────────────────────────────────────────────────

class BlocklySubmitRequest(BaseModel):
    """Corps de requête pour la soumission d'un exercice Blockly."""
    assignment_id: str = Field(..., description="ID de l'exercice")
    python_code: str = Field(..., min_length=1, description="Code Python généré par Blockly")
    blocks_json: Optional[str] = Field(None, description="XML du workspace Blockly")

    @validator('python_code')
    def validate_python_code(cls, v):
        # Longueur max pour éviter les abus
        if len(v) > 50_000:
            raise ValueError("Code trop long (max 50 000 caractères)")
        return v.strip()

    @validator('blocks_json')
    def validate_blocks_json(cls, v):
        if v and len(v) > 200_000:
            raise ValueError("Workspace trop volumineux")
        return v


class BlocklyTestRequest(BaseModel):
    """Corps de requête pour tester du code sans soumission officielle."""
    python_code: str = Field(..., min_length=1, max_length=50_000)
    assignment_id: str
    blocks_json: Optional[str] = None


class BlocklySaveWorkspaceRequest(BaseModel):
    """Corps de requête pour sauvegarder un brouillon de workspace."""
    assignment_id: str
    blocks_json: str = Field(..., max_length=200_000)


# ─── Modèles internes ────────────────────────────────────────────────────────

class TestCase(BaseModel):
    """Définition d'un cas de test pour un exercice."""
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected_output: str
    description: Optional[str] = None


class TestCaseResult(BaseModel):
    """Résultat d'un cas de test individuel."""
    index: int
    passed: bool
    expected: str
    got: str
    description: Optional[str] = None


class ExecutionResult(BaseModel):
    """Résultat de l'exécution du code Python en sandbox."""
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0
    timed_out: bool = False


# ─── Réponses (Output) ───────────────────────────────────────────────────────

class BlocklyTestResponse(BaseModel):
    """Réponse au test de code (sans soumission officielle)."""
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    test_results: Optional[List[TestCaseResult]] = None
    execution_time_ms: float = 0

    class Config:
        from_attributes = True


class BlocklySubmissionResponse(BaseModel):
    """Données d'une soumission dans l'historique."""
    id: UUID
    assignment_id: str
    assignment_title: Optional[str] = None
    python_code: str
    blocks_json: Optional[str] = None
    score: Optional[int] = None
    ai_feedback: Optional[str] = None
    submitted_at: datetime
    test_results: Optional[List[TestCaseResult]] = None

    class Config:
        from_attributes = True


class BlocklyAssignmentResponse(BaseModel):
    """Détails d'un exercice Blockly."""
    id: str
    title: str
    description: str
    allowed_blocks: Optional[List[str]] = None  # None = tous les blocs
    test_cases: List[TestCase] = []
    max_score: int = 100
    hints: List[str] = []
    course_id: Optional[str] = None
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class BlocklyProgressStats(BaseModel):
    """Statistiques de progression pour le dashboard."""
    total_submissions: int
    best_score: int
    average_score: float
    completed_assignments: int
    total_assignments: int
    last_activity: Optional[datetime] = None
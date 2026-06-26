"""
Schémas Pydantic — Module Blockly.
Validation stricte des entrées (sécurité : §3.2 du guide).
"""
from pydantic import BaseModel, Field
from typing import Optional

# Niveaux acceptés — liste blanche (allowlist)
VALID_LEVELS = {"beginner", "intermediate", "advanced"}


class ExecutionRequest(BaseModel):
    """Requête POST /execute et /submit."""
    python_code:   str           = Field(..., min_length=1, max_length=10_000)
    assignment_id: Optional[str] = Field(None, max_length=36)
    level:         Optional[str] = Field("beginner", max_length=20)


class GenerateRequest(BaseModel):
    """Requête POST /generate/stream."""
    level:         Optional[str] = Field("beginner", max_length=20)
    course:        Optional[str] = Field("",         max_length=255)
    objectives:    Optional[str] = Field("",         max_length=500)
    prerequisites: Optional[str] = Field("",         max_length=500)


class WorkspaceSaveRequest(BaseModel):
    """Requête POST /workspace/save."""
    assignment_id: Optional[str] = Field(None, max_length=36)
    workspace_xml: Optional[str] = Field(None, max_length=100_000)
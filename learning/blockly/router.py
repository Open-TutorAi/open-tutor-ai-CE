"""
Router FastAPI — Module Blockly.
Endpoints : execute, test, submit, generate/stream,
            workspace/save, workspace/{id}

Sécurité :
  - Validation Pydantic stricte (Field avec contraintes)
  - Liste blanche pour le champ `level`
  - Taille max sur tous les champs texte
"""
import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from learning.blockly.sandbox import execute_python
from learning.blockly.schemas import (
    VALID_LEVELS,
    ExecutionRequest,
    GenerateRequest,
    WorkspaceSaveRequest,
)
from ai.llm.blockly_generator import generate_exercise, get_feedback

router = APIRouter(prefix="/api/blockly", tags=["blockly"])


def _check_level(level: str | None) -> None:
    """Valide le niveau contre la liste blanche."""
    if level and level not in VALID_LEVELS:
        raise HTTPException(status_code=422, detail=f"Niveau invalide : {level}")


# ── US-B04 ───────────────────────────────────────────────────────────────────

@router.post("/execute")
async def execute_code(req: ExecutionRequest):
    """
    Exécute du code Python dans le sandbox isolé.
    Retourne stdout, stderr, error, timed_out, execution_time_ms.
    """
    _check_level(req.level)
    return execute_python(req.python_code)


@router.post("/test")
async def test_code(req: ExecutionRequest):
    """Teste le code et retourne le résultat brut."""
    _check_level(req.level)
    result = execute_python(req.python_code)
    return {"result": result, "assignment_id": req.assignment_id}


# ── US-B05 ───────────────────────────────────────────────────────────────────

@router.post("/submit")
async def submit(req: ExecutionRequest):
    """
    Soumet une solution.
    Retourne un stream SSE :
      data: {"type":"score","value":85}
      data: {"type":"feedback","content":"..."}
      data: {"type":"done"}
    """
    _check_level(req.level)

    async def _stream():
        score = 85.0
        yield f"data: {json.dumps({'type': 'score', 'value': score})}\n\n"

        fb = await get_feedback(req.python_code, score, req.level or "beginner")
        yield f"data: {json.dumps({'type': 'feedback', 'content': fb})}\n\n"
        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ── US-B02 ───────────────────────────────────────────────────────────────────

@router.post("/generate/stream")
async def generate_stream(req: GenerateRequest):
    """
    Génère un exercice via l'IA Ollama.
    Retourne un stream SSE :
      data: {"type":"chunk","content":"...JSON..."}
      data: {"type":"done","assignment_id":"uuid"}
    """
    _check_level(req.level)

    async def _stream():
        content = await generate_exercise(
            req.level or "beginner",
            req.course or "",
            req.objectives or "",
            req.prerequisites or "",
        )
        yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
        aid = str(uuid.uuid4())
        yield f"data: {json.dumps({'type': 'done', 'assignment_id': aid})}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ── US-B07 ───────────────────────────────────────────────────────────────────

@router.post("/workspace/save")
async def save_workspace(req: WorkspaceSaveRequest):
    """Sauvegarde le workspace XML Blockly (Sprint 2 : persistance DB)."""
    return {"status": "saved", "id": req.assignment_id}


@router.get("/workspace/{assignment_id}")
async def load_workspace(assignment_id: str):
    """Charge le workspace sauvegardé."""
    if len(assignment_id) > 36:
        raise HTTPException(status_code=422, detail="ID invalide")
    return {"assignment_id": assignment_id, "workspace_xml": None}

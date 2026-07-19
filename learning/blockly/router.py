"""
Router FastAPI — Module Blockly.
Endpoints : execute, test, submit, generate/stream,
            workspace/save, workspace/{id}

Corrections apportées :
  - Prefix /api/v1/blockly (conforme MIGRATION.md)
  - Auth JWT via get_current_user sur tous les endpoints
  - Score réel calculé via BlocklyService (suppression du hardcode 85.0)
  - Génération exercice en vrai streaming token par token
  - Workspace save/load avec persistance DB réelle
"""
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from learning.blockly.sandbox import execute_python
from learning.blockly.service import BlocklyService
from learning.blockly.schemas import (
    VALID_LEVELS,
    ExecutionRequest,
    GenerateRequest,
    WorkspaceSaveRequest,
)
from ai.llm.blockly_generator import generate_exercise_stream, get_feedback_stream

# FIX #2 : prefix /api/v1/blockly au lieu de /api/blockly
router = APIRouter(prefix="/api/v1/blockly", tags=["blockly"])


def _check_level(level: str | None) -> None:
    if level and level not in VALID_LEVELS:
        raise HTTPException(status_code=422, detail=f"Niveau invalide : {level}")


def get_blockly_service(db: Session = Depends(get_db)) -> BlocklyService:
    return BlocklyService(db)


# ── US-B04 : Exécution ───────────────────────────────────────────────────────

@router.post("/execute")
async def execute_code(
    req: ExecutionRequest,
    # FIX #3 : auth JWT requise
    current_user: User = Depends(get_current_user),
):
    """Exécute du code Python dans le sandbox isolé (Piston)."""
    _check_level(req.level)
    return execute_python(req.python_code)


@router.post("/test")
async def test_code(
    req: ExecutionRequest,
    current_user: User = Depends(get_current_user),
):
    """Teste le code et retourne le résultat brut."""
    _check_level(req.level)
    result = execute_python(req.python_code)
    return {"result": result, "assignment_id": req.assignment_id}


# ── US-B05 : Soumission ──────────────────────────────────────────────────────

@router.post("/submit")
async def submit(
    req: ExecutionRequest,
    current_user: User = Depends(get_current_user),
    service: BlocklyService = Depends(get_blockly_service),
):
    """
    Soumet une solution.
    FIX #1 : score réel calculé via BlocklyService.
    FIX #5 : feedback streamé token par token.

    SSE events :
      data: {"type":"score",    "value": 85}
      data: {"type":"feedback", "content":"..."}
      data: {"type":"done"}
    """
    _check_level(req.level)

    async def _stream():
        # Exécuter le code dans le sandbox
        exec_result = execute_python(req.python_code)

        # FIX #1 : calculer le vrai score
        # Récupérer l'exercice depuis DB — sécurisé par student_id
        exercise = service.get_exercise(
        req.assignment_id or "", current_user.id
        )
        test_cases = exercise.get("test_cases", []) if exercise else []
        test_results = await service.run_test_cases(req.python_code, test_cases)
        score = service.calculate_score(test_cases, test_results)

        yield f"data: {json.dumps({'type': 'score', 'value': score})}\n\n"

        # FIX #5 : stream le feedback token par token
        async for chunk in get_feedback_stream(
            req.python_code, score, req.level or "beginner"
        ):
            yield f"data: {json.dumps({'type': 'feedback', 'content': chunk})}\n\n"

        # Sauvegarder la soumission
        try:
            service.save_submission(
                student_id=current_user.id,
                assignment_id=req.assignment_id or str(uuid.uuid4()),
                python_code=req.python_code,
                score=score,
                level=req.level or "beginner",
            )
        except Exception:
            pass

        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ── US-B02 : Génération exercice ─────────────────────────────────────────────

@router.post("/generate/stream")
async def generate_stream(
    req: GenerateRequest,
    current_user: User = Depends(get_current_user),
    service: BlocklyService = Depends(get_blockly_service),
):
    """
    Génère un exercice via l'IA Ollama.
    FIX #5 : vrai streaming token par token au lieu d'un seul chunk.

    SSE events :
      data: {"type":"chunk","content":"...token..."}
      data: {"type":"done","assignment_id":"uuid"}
    """
    _check_level(req.level)

    async def _stream():
       try:
          full_json = ""
          async for token in generate_exercise_stream(
              req.level or "beginner",
              req.course or "",
              req.objectives or "",
              req.prerequisites or "",
          ):
              full_json += token
              yield f"data: {json.dumps({'type': 'chunk', 'content': token})}\n\n"

        # Nettoyer et parser le JSON
          clean = full_json.replace("```json", "").replace("```", "").strip()
          exercise = json.loads(clean)

        # Sauvegarder l'exercice en DB — retourner l'ID sécurisé
          aid = service.save_exercise(
              student_id=current_user.id,
              level=req.level or "beginner",
              exercise=exercise,
          )

          yield f"data: {json.dumps({'type': 'done', 'assignment_id': aid})}\n\n"

       except Exception as e:
           yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


# ── US-B07 : Workspace ───────────────────────────────────────────────────────

@router.post("/workspace/save")
async def save_workspace(
    req: WorkspaceSaveRequest,
    current_user: User = Depends(get_current_user),
    service: BlocklyService = Depends(get_blockly_service),
):
    """
    Sauvegarde le workspace XML Blockly en base de données.
    FIX #6 : persistance DB réelle via BlocklyService.
    """
    assignment_id = req.assignment_id or str(uuid.uuid4())
    service.save_workspace_draft(
        student_id=current_user.id,
        assignment_id=assignment_id,
        blocks_json=req.workspace_xml or "",
    )
    return {"status": "saved", "id": assignment_id}


@router.get("/workspace/{assignment_id}")
async def load_workspace(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    service: BlocklyService = Depends(get_blockly_service),
):
    """
    Charge le workspace sauvegardé depuis la base de données.
    FIX #6 : lecture DB réelle au lieu de retourner None.
    """
    if len(assignment_id) > 36:
        raise HTTPException(status_code=422, detail="ID invalide")

    draft = service.get_workspace_draft(current_user.id, assignment_id)
    return {
        "assignment_id": assignment_id,
        "workspace_xml": draft.get("blocks_json") if draft else None,
    }
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import requests

from open_tutorai.models.database import get_db
from open_tutorai.services.blockly_service import BlocklyService

router = APIRouter()


# ── Modèles de requête ────────────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    python_code: str

class TestRequest(BaseModel):
    python_code: str
    assignment_id: str
    blocks_json: Optional[str] = None

class SubmitRequest(BaseModel):
    assignment_id: str
    python_code: str
    blocks_json: Optional[str] = None

class GenerateRequest(BaseModel):
    theme: str
    level: str
    objective: str
    num_test_cases: int = 3


# ── Route 1 : exécution libre ─────────────────────────────────────────────────

@router.post("/execute")
async def execute_code(request: ExecuteRequest, db: Session = Depends(get_db)):
    """Exécute le code librement via Piston (bouton Tester sans cas de test)."""
    service = BlocklyService(db)
    result = await service.execute_code(request.python_code)
    return result


# ── Route 2 : tester avec cas de test ────────────────────────────────────────

@router.post("/test")
async def test_code(request: TestRequest, db: Session = Depends(get_db)):
    """Exécute le code et vérifie les cas de test de l'exercice."""
    service = BlocklyService(db)
    result = await service.test_code(
        python_code=request.python_code,
        assignment_id=request.assignment_id,
        student_id="anonymous",
    )
    return result


# ── Route 3 : soumettre pour évaluation (streaming) ──────────────────────────

@router.post("/submit")
async def submit_code(request: SubmitRequest, db: Session = Depends(get_db)):
    """
    Soumet le code étudiant, calcule le score, génère un feedback IA en streaming.
    Le frontend lit les événements SSE :
      data: {"type": "score",    "value": 80}
      data: {"type": "feedback", "content": "Bien joué..."}
    """
    service = BlocklyService(db)

    # 1. Récupérer l'exercice
    assignment = service.get_assignment(request.assignment_id, "anonymous")
    if not assignment:
        async def error_stream():
            yield f'data: {json.dumps({"type": "error", "message": "Exercice introuvable"})}\n\n'
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    # 2. Exécuter le code et lancer les tests
    exec_result = await service.execute_code(request.python_code)
    test_results = await service.run_test_cases(
        request.python_code, assignment.get("test_cases", [])
    )

    # 3. Calculer le score
    score = service.calculate_score(test_results, assignment.get("max_score", 100))

    async def event_stream():
        # Envoyer le score en premier
        yield f'data: {json.dumps({"type": "score", "value": score})}\n\n'

        # Streamer le feedback IA mot par mot
        async for chunk in service.generate_feedback_stream(
            python_code=request.python_code,
            execution_result=exec_result,
            test_results=test_results,
            score=score,
            assignment=assignment,
        ):
            yield f'data: {json.dumps({"type": "feedback", "content": chunk})}\n\n'

        # Sauvegarder la soumission en base
        try:
            service.save_submission(
                student_id="anonymous",
                assignment_id=request.assignment_id,
                blocks_json=request.blocks_json,
                python_code=request.python_code,
                execution_result=exec_result,
                test_results=test_results,
                score=score,
            )
        except Exception:
            pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Route 4 : générer un exercice via l'IA (streaming) ───────────────────────

@router.post("/generate/stream")
async def generate_exercise_stream(request: GenerateRequest, db: Session = Depends(get_db)):
    """
    Génère un exercice Blockly via Ollama en streaming SSE.
    Le frontend lit :
      data: {"type": "chunk",  "content": "...JSON partiel..."}
      data: {"type": "done",   "assignment_id": "xxx"}
      data: {"type": "error",  "message": "..."}
    """

    prompt = f"""Tu es un générateur d'exercices Python pour étudiants.
Génère UN exercice de niveau "{request.level}" sur le thème "{request.theme}".
L'objectif est de : {request.objective}.

Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après, avec cette structure exacte :
{{
  "title": "Titre court de l'exercice",
  "description": "Description claire en 2-3 phrases de ce que l'étudiant doit faire",
  "difficulty": "{request.level}",
  "allowed_blocks": ["print", "variables", "math_arithmetic"],
  "test_cases": [
    {{"description": "Description du test", "inputs": {{}}, "expected_output": "valeur attendue"}}
  ],
  "hints": ["Indice 1", "Indice 2"]
}}

Génère exactement {request.num_test_cases} cas de test. Réponds en français."""

    async def event_stream():
        full_json = ""
        assignment_id = None

        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "qwen2.5:0.5b",
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": 0.7, "num_predict": 600},
                },
                stream=True,
                timeout=120,
            )

            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        chunk = data['response']
                        full_json += chunk
                        yield f'data: {json.dumps({"type": "chunk", "content": chunk})}\n\n'
                    if data.get('done'):
                        break
                except Exception:
                    continue

            # Sauvegarder l'exercice généré en base et récupérer son ID
            try:
                import uuid
                assignment_id = str(uuid.uuid4())
                # Optionnel : sauvegarder en DB ici si nécessaire
            except Exception:
                assignment_id = "generated"

            yield f'data: {json.dumps({"type": "done", "assignment_id": assignment_id})}\n\n'

        except Exception as e:
            yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
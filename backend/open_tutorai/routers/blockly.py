# backend/open_tutorai/routers/blockly.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from open_tutorai.models.database import get_db
from open_tutorai.schemas.blockly import (
    BlocklySubmitRequest,
    BlocklyTestRequest,
    BlocklyTestResponse,
    BlocklySaveWorkspaceRequest,
    BlocklyAssignmentResponse,
    BlocklySubmissionResponse,
)
from open_tutorai.services.blockly_service import BlocklyService
from open_webui.utils.auth import get_verified_user

router = APIRouter(prefix="/api/blockly", tags=["Blockly"])


@router.get("/assignment/{assignment_id}", response_model=BlocklyAssignmentResponse)
async def get_blockly_assignment(
    assignment_id: str,
    current_user = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    service = BlocklyService(db)
    assignment = service.get_assignment(assignment_id, current_user.id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Exercice Blockly introuvable")
    return assignment


@router.post("/test", response_model=BlocklyTestResponse)
async def test_blockly_code(
    payload: BlocklyTestRequest,
    current_user = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    service = BlocklyService(db)
    result = await service.test_code(
        python_code=payload.python_code,
        assignment_id=payload.assignment_id,
        student_id=current_user.id,
    )
    return result


@router.post("/submit")
async def submit_blockly_exercise(
    payload: BlocklySubmitRequest,
    current_user = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    service = BlocklyService(db)
    assignment = service.get_assignment(payload.assignment_id, current_user.id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Exercice introuvable")

    # Pré-calculer tout avant le streaming
    execution_result = await service.execute_code(payload.python_code)
    test_results = await service.run_test_cases(
        payload.python_code, assignment["test_cases"]
    )
    score = service.calculate_score(test_results, assignment["max_score"])

    # Sauvegarder avant le streaming
    try:
        submission_id = service.save_submission(
            student_id=current_user.id,
            assignment_id=payload.assignment_id,
            blocks_json=payload.blocks_json,
            python_code=payload.python_code,
            execution_result=execution_result,
            test_results=test_results,
            score=score,
        )
    except Exception:
        submission_id = "temp"

    async def event_stream():
        try:
            # 1. Envoyer le score
            yield f"data: {json.dumps({'type': 'score', 'value': score})}\n\n"

            # 2. Streamer le feedback IA
            async for feedback_chunk in service.generate_feedback_stream(
                python_code=payload.python_code,
                execution_result=execution_result,
                test_results=test_results,
                score=score,
                assignment=assignment,
                student_level="débutant",
            ):
                yield f"data: {json.dumps({'type': 'feedback', 'content': feedback_chunk})}\n\n"

            # 3. Signal de fin
            yield f"data: {json.dumps({'type': 'done', 'submission_id': str(submission_id)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/history/{student_id}", response_model=list[BlocklySubmissionResponse])
async def get_submission_history(
    student_id: str,
    assignment_id: str | None = None,
    limit: int = 20,
    current_user = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    if current_user.id != student_id and current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    service = BlocklyService(db)
    return service.get_history(
        student_id=student_id,
        assignment_id=assignment_id,
        limit=limit
    )


@router.post("/workspace/save")
async def save_workspace(
    payload: BlocklySaveWorkspaceRequest,
    current_user = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    service = BlocklyService(db)
    service.save_workspace_draft(
        student_id=current_user.id,
        assignment_id=payload.assignment_id,
        blocks_json=payload.blocks_json,
    )
    return {"status": "saved"}


@router.get("/workspace/{assignment_id}")
async def load_workspace(
    assignment_id: str,
    current_user = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    service = BlocklyService(db)
    draft = service.get_workspace_draft(
        student_id=current_user.id,
        assignment_id=assignment_id,
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Aucun brouillon trouvé")
    return draft
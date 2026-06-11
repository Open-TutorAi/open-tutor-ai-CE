from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from learning.blockly.service import BlocklyService
from learning.blockly.schemas import ExecutionRequest
import json, uuid

router = APIRouter(prefix="/api/blockly", tags=["blockly"])
service = BlocklyService()

@router.post("/execute")
async def execute_code(req: ExecutionRequest):
    return await service.execute_code(req.python_code)

@router.post("/test")
async def test_code(req: ExecutionRequest):
    result = await service.execute_code(req.python_code)
    return {"result": result, "assignment_id": req.assignment_id}

@router.post("/submit")
async def submit(req: ExecutionRequest):
    async def event_stream():
        result = await service.execute_code(req.python_code)
        score = 85.0
        yield f"data: {json.dumps({'type': 'score', 'value': score})}\n\n"
        async for chunk in service.generator.stream_feedback(
                req.python_code, score, req.level or "beginner"):
            yield f"data: {json.dumps({'type': 'feedback', 'content': chunk})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/generate/stream")
async def generate_exercise(body: dict = {}):
    level = body.get("level", "beginner")
    course = body.get("course", "")
    objectives = body.get("objectives", "")
    prerequisites = body.get("prerequisites", "")

    async def event_stream():
        async for chunk in service.generator.stream_exercise(
                level, course, objectives, prerequisites):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        assignment_id = str(uuid.uuid4())
        yield f"data: {json.dumps({'type': 'done', 'assignment_id': assignment_id})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/workspace/save")
async def save_workspace(body: dict):
    return {"status": "saved", "id": body.get("assignment_id")}

@router.get("/workspace/{assignment_id}")
async def load_workspace(assignment_id: str):
    return {"assignment_id": assignment_id, "workspace_xml": None}

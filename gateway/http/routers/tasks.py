"""Tasks router — /api/v1/tasks/* matching index.ts UI client (LLM task helpers)."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/config")
def get_tasks_config(user: User = Depends(get_current_user)):
    return {
        "title_generation_prompt_template": "",
        "tags_generation_prompt_template": "",
        "emoji_generation_prompt_template": "",
        "query_generation_prompt_template": "",
        "autocomplete_generation_prompt_template": "",
        "image_prompt_generation_prompt_template": "",
    }


@router.post("/config/update")
def update_tasks_config(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return body


@router.post("/title/completions")
async def generate_title(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {"choices": [{"message": {"content": ""}}]}


@router.post("/tags/completions")
async def generate_tags(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {"choices": [{"message": {"content": "[]"}}]}


@router.post("/emoji/completions")
async def generate_emoji(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {"choices": [{"message": {"content": ""}}]}


@router.post("/queries/completions")
async def generate_queries(
    body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {"choices": [{"message": {"content": "[]"}}]}


@router.post("/auto/completions")
async def auto_completions(
    body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {"choices": [{"message": {"content": ""}}]}


@router.post("/moa/completions")
async def moa_completions(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {"choices": [{"message": {"content": ""}}]}

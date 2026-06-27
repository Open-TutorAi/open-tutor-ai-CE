"""Prompts router — /api/v1/prompts/* matching prompts/index.ts UI client."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/")
def list_prompts(user: User = Depends(get_current_user)):
    return []


@router.get("/list")
def list_prompts_public(user: User = Depends(get_current_user)):
    return []


@router.post("/create")
def create_prompt(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {**body, "user_id": user.id}


@router.get("/command/{command}")
def get_prompt_by_command(command: str, user: User = Depends(get_current_user)):
    return None


@router.post("/command/{command}/update")
def update_prompt(
    command: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "command": command}


@router.delete("/command/{command}/delete")
def delete_prompt(command: str, user: User = Depends(get_current_user)):
    return {"command": command}

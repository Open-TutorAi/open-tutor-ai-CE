"""Memories router — /api/v1/memories/* matching memories/index.ts UI client."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("/")
def list_memories(user: User = Depends(get_current_user)):
    return []


@router.post("/add")
def add_memory(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {**body, "id": "", "user_id": user.id}


@router.post("/query")
def query_memories(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {"documents": [], "metadatas": [], "distances": []}


@router.post("/delete/user")
def delete_user_memories(user: User = Depends(get_current_user)):
    return {"status": True}


@router.post("/{memory_id}/update")
def update_memory(
    memory_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "id": memory_id}


@router.delete("/{memory_id}")
def delete_memory(memory_id: str, user: User = Depends(get_current_user)):
    return {"id": memory_id}

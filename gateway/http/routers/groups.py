"""Groups router — /api/v1/groups/* matching groups/index.ts UI client."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/")
def list_groups(user: User = Depends(get_current_user)):
    return []


@router.post("/create")
def create_group(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {**body, "id": "", "user_id": user.id}


@router.get("/id/{group_id}")
def get_group(group_id: str, user: User = Depends(get_current_user)):
    return None


@router.post("/id/{group_id}/update")
def update_group(
    group_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "id": group_id}


@router.delete("/id/{group_id}/delete")
def delete_group(group_id: str, user: User = Depends(get_current_user)):
    return {"id": group_id}

"""Folders router — /api/v1/folders/* matching folders/index.ts UI client."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("/")
def list_folders(user: User = Depends(get_current_user)):
    return []


@router.get("/{folder_id}")
def get_folder(folder_id: str, user: User = Depends(get_current_user)):
    return None


@router.post("/{folder_id}/update")
def update_folder(
    folder_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "id": folder_id}


@router.post("/{folder_id}/update/expanded")
def update_folder_expanded(
    folder_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return body


@router.post("/{folder_id}/update/items")
def update_folder_items(
    folder_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return body


@router.post("/{folder_id}/update/parent")
def update_folder_parent(
    folder_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return body

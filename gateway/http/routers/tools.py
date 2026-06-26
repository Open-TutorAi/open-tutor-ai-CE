"""Tools router — /api/v1/tools/* matching tools/index.ts UI client."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/")
def list_tools(user: User = Depends(get_current_user)):
    return []


@router.get("/list")
def list_tools_public(user: User = Depends(get_current_user)):
    return []


@router.get("/export")
def export_tools(user: User = Depends(get_current_user)):
    return []


@router.post("/create")
def create_tool(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {**body, "id": body.get("id", ""), "user_id": user.id}


@router.get("/id/{tool_id}")
def get_tool(tool_id: str, user: User = Depends(get_current_user)):
    return None


@router.post("/id/{tool_id}/update")
def update_tool(
    tool_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "id": tool_id}


@router.delete("/id/{tool_id}/delete")
def delete_tool(tool_id: str, user: User = Depends(get_current_user)):
    return {"id": tool_id}


@router.get("/id/{tool_id}/valves")
def get_valves(tool_id: str, user: User = Depends(get_current_user)):
    return {}


@router.get("/id/{tool_id}/valves/spec")
def get_valves_spec(tool_id: str, user: User = Depends(get_current_user)):
    return {}


@router.post("/id/{tool_id}/valves/update")
def update_valves(
    tool_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return body


@router.get("/id/{tool_id}/valves/user")
def get_user_valves(tool_id: str, user: User = Depends(get_current_user)):
    return {}


@router.get("/id/{tool_id}/valves/user/spec")
def get_user_valves_spec(tool_id: str, user: User = Depends(get_current_user)):
    return {}


@router.post("/id/{tool_id}/valves/user/update")
def update_user_valves(
    tool_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return body

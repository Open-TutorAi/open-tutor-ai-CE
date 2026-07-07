"""Functions router — /api/v1/functions/* matching functions/index.ts UI client."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/functions", tags=["functions"])


@router.get("/")
def list_functions(user: User = Depends(get_current_user)):
    return []


@router.get("/export")
def export_functions(user: User = Depends(get_current_user)):
    return []


@router.post("/create")
def create_function(body: Dict[str, Any], user: User = Depends(get_current_user)):
    return {**body, "id": body.get("id", ""), "user_id": user.id}


@router.get("/id/{function_id}")
def get_function(function_id: str, user: User = Depends(get_current_user)):
    return None


@router.post("/id/{function_id}/update")
def update_function(
    function_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return {**body, "id": function_id}


@router.delete("/id/{function_id}/delete")
def delete_function(function_id: str, user: User = Depends(get_current_user)):
    return {"id": function_id}


@router.post("/id/{function_id}/toggle")
def toggle_function(function_id: str, user: User = Depends(get_current_user)):
    return {"id": function_id}


@router.post("/id/{function_id}/toggle/global")
def toggle_function_global(function_id: str, user: User = Depends(get_current_user)):
    return {"id": function_id}


@router.get("/id/{function_id}/valves")
def get_valves(function_id: str, user: User = Depends(get_current_user)):
    return {}


@router.get("/id/{function_id}/valves/spec")
def get_valves_spec(function_id: str, user: User = Depends(get_current_user)):
    return {}


@router.post("/id/{function_id}/valves/update")
def update_valves(
    function_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return body


@router.get("/id/{function_id}/valves/user")
def get_user_valves(function_id: str, user: User = Depends(get_current_user)):
    return {}


@router.get("/id/{function_id}/valves/user/spec")
def get_user_valves_spec(function_id: str, user: User = Depends(get_current_user)):
    return {}


@router.post("/id/{function_id}/valves/user/update")
def update_user_valves(
    function_id: str, body: Dict[str, Any], user: User = Depends(get_current_user)
):
    return body

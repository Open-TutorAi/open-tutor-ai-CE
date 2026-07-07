"""Configs router — /api/v1/configs/*"""

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from system.configs.service import ConfigsService

router = APIRouter(prefix="/configs", tags=["configs"])


def get_configs_service(db: Session = Depends(get_db)) -> ConfigsService:
    return ConfigsService(db)


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.get("/models")
async def get_models_config(
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    return svc.get("models")


@router.post("/models")
async def update_models_config(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    return svc.set("models", body)


@router.get("/banners")
async def get_banners(
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    return svc.get("banners")


@router.post("/banners")
async def update_banners(
    body: List[Any] = Body(...),
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    return svc.set("banners", body)


@router.get("/suggestions")
async def get_suggestions(
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    return svc.get("suggestions")


@router.post("/suggestions")
async def update_suggestions(
    body: List[Any] = Body(...),
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    return svc.set("suggestions", body)


@router.get("/code_execution")
async def get_code_execution(
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    return svc.get("code_execution")


@router.post("/code_execution")
async def update_code_execution(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    return svc.set("code_execution", body)


@router.get("/direct_connections")
async def get_direct_connections(
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    return svc.get("direct_connections")


@router.post("/direct_connections")
async def update_direct_connections(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    return svc.set("direct_connections", body)


@router.get("/tutor_system_prompt")
async def get_tutor_system_prompt(
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    return {"content": svc.get("tutor_system_prompt")}


@router.post("/tutor_system_prompt")
async def update_tutor_system_prompt(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    content = body.get("content", "")
    svc.set("tutor_system_prompt", content)
    return {"content": content}


@router.get("/export")
async def export_config(
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    return svc.export_all()


@router.post("/import")
async def import_config(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ConfigsService = Depends(get_configs_service),
):
    _require_admin(current_user)
    svc.import_all(body)
    return svc.export_all()

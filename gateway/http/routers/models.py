"""Models router — /api/v1/models/*."""

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ai.model_catalog.service import ModelsService
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/models", tags=["models"])


def get_models_service(db: Session = Depends(get_db)) -> ModelsService:
    return ModelsService(db)


@router.get("/")
async def get_models(
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    return [m.to_dict() for m in svc.list_active()]


@router.get("/base")
async def get_base_models(
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    return svc.list_base()


@router.post("/create")
async def create_model(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    try:
        return svc.create(current_user.id, body).to_dict()
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)


@router.get("/model")
async def get_model(
    id: str = Query(...),
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    model = svc.get(id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    return model.to_dict()


@router.post("/model/update")
async def update_model(
    id: str = Query(...),
    body: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    try:
        return svc.update(
            id, current_user.id, body, is_admin=current_user.is_admin
        ).to_dict()
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.post("/model/toggle")
async def toggle_model(
    id: str = Query(...),
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    try:
        return svc.toggle(id, current_user.id, is_admin=current_user.is_admin).to_dict()
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.delete("/model/delete")
async def delete_model(
    id: str = Query(...),
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    try:
        ok = svc.delete(id, current_user.id, is_admin=current_user.is_admin)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )
    return {"id": id}


@router.delete("/delete/all")
async def delete_all_models(
    current_user: User = Depends(get_current_user),
    svc: ModelsService = Depends(get_models_service),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    count = svc.delete_all()
    return {"count": count}

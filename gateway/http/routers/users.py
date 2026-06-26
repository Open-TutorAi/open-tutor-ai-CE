from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from accounts.users.service import AccountService
from data.models import User
from gateway.http.dependencies import get_account_service, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


class RoleUpdateRequest(BaseModel):
    id: str
    role: str


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def get_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return [u.to_dict() for u in svc.list_users(skip=skip, limit=limit)]


@router.get("/all")
async def get_all_users(
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return [u.to_dict() for u in svc.list_users(limit=10000)]


@router.get("/groups")
async def get_user_groups(current_user: User = Depends(get_current_user)):
    return []


@router.get("/user/settings")
async def get_settings(
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    return svc.get_user_settings(current_user.id)


@router.post("/user/settings/update")
async def update_settings(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    return svc.update_user_settings(current_user.id, body)


@router.get("/user/info")
async def get_info(
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    return svc.get_user_info(current_user.id)


@router.post("/user/info/update")
async def update_info(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    return svc.update_user_info(current_user.id, body)


@router.get("/default/permissions")
async def get_default_permissions(current_user: User = Depends(get_current_user)):
    return {
        "chat": {"deletion": True, "edit": True, "export": True},
        "workspace": {
            "models": False,
            "knowledge": False,
            "prompts": False,
            "tools": False,
        },
        "features": {
            "web_search": False,
            "image_generation": False,
            "code_interpreter": False,
        },
    }


@router.post("/default/permissions")
async def update_default_permissions(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    # TODO: persist to AppConfig once the configs domain is wired in (Task 4).
    # For now this echoes the body without storing it.
    return body


@router.post("/update/role")
async def update_user_role(
    body: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    user = svc.update_role(body.id, body.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user.to_dict()


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    user = svc.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user.to_dict()


@router.post("/{user_id}/update")
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    user = svc.update_user(user_id, **updates)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user.to_dict()


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself"
        )
    ok = svc.delete_user(user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"id": user_id}

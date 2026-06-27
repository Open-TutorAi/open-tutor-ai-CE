"""Images router — /images/* matching images/index.ts UI client.

Admin-only: config read/write, URL verify, image config, models.
Verified user: generations.
"""

from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.media.images import ImagesService
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/images", tags=["images"])


def _svc(db: Session = Depends(get_db)) -> ImagesService:
    return ImagesService(db)


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


class ImagesConfigUpdate(BaseModel):
    engine: Optional[str] = None
    enabled: Optional[bool] = None
    url: Optional[str] = None
    key: Optional[str] = None


class ImageConfigUpdate(BaseModel):
    model: Optional[str] = None
    size: Optional[str] = None
    n: Optional[int] = None


# ── Admin-only: config, verify, image config, models ─────────────────────────


@router.get("/config")
def get_config(
    user: User = Depends(get_current_user), svc: ImagesService = Depends(_svc)
):
    _require_admin(user)
    return svc.get_config()


@router.post("/config/update")
def update_config(
    body: ImagesConfigUpdate,
    user: User = Depends(get_current_user),
    svc: ImagesService = Depends(_svc),
):
    _require_admin(user)
    return svc.update_config(body.model_dump(exclude_none=True))


@router.get("/config/url/verify")
def verify_url(user: User = Depends(get_current_user)):
    _require_admin(user)
    return {"ok": True}


@router.get("/image/config")
def get_image_config(
    user: User = Depends(get_current_user), svc: ImagesService = Depends(_svc)
):
    _require_admin(user)
    return svc.get_image_config()


@router.post("/image/config/update")
def update_image_config(
    body: ImageConfigUpdate,
    user: User = Depends(get_current_user),
    svc: ImagesService = Depends(_svc),
):
    _require_admin(user)
    return svc.update_image_config(body.model_dump(exclude_none=True))


@router.get("/models")
def get_models(
    user: User = Depends(get_current_user), svc: ImagesService = Depends(_svc)
):
    _require_admin(user)
    return svc.get_models()


# ── Verified user: generations ────────────────────────────────────────────────


@router.post("/generations")
async def generate_image(
    body: dict,
    user: User = Depends(get_current_user),
    svc: ImagesService = Depends(_svc),
) -> List[dict]:
    """Return list of {url: str} objects — matches UI's res.map((image) => image.url)."""
    cfg = svc.get_config()
    if not cfg.get("enabled"):
        return []
    url = (cfg.get("url") or "").rstrip("/")
    key = cfg.get("key") or ""
    if not url:
        return []
    img_cfg = cfg.get("image", {})
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{url}/v1/images/generations",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": body.get("model") or img_cfg.get("model", "dall-e-3"),
                "prompt": body.get("prompt", ""),
                "size": body.get("size") or img_cfg.get("size", "1024x1024"),
                "n": body.get("n") or img_cfg.get("n", 1),
            },
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json().get("data", [])

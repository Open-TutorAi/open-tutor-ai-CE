"""
Settings router for user profile, password, and preferences management.
Handles profile updates, password changes, and user preferences (language, theme).
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from open_webui.internal.db import get_db, SessionLocal
from open_webui.models.users import Users
from open_webui.utils.auth import get_current_user, get_password_hash, verify_password
from open_tutorai.models.database import UserPreference

router = APIRouter(prefix="/settings", tags=["settings"])

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("MAIN", "INFO"))

# backend/open_tutorai/routers/settings.py -> parents[2] == backend/
BASE_DIR = Path(__file__).resolve().parents[2]
AVATAR_DIR = BASE_DIR / "static" / "avatars"


# --- Database dependency wrapper ---
def get_session_local():
    """Get a SQLAlchemy session using SessionLocal directly."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# --- Pydantic Models ---

class ProfileUpdateRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    avatar: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    oldPassword: str
    newPassword: str


class PreferencesUpdateRequest(BaseModel):
    language: str
    theme: str


class UserProfileResponse(BaseModel):
    id: str
    firstName: str
    lastName: str
    email: str
    avatar: Optional[str] = None
    role: str


class UserPreferencesResponse(BaseModel):
    language: str
    theme: str


# --- Helper Functions ---

def get_user_full_name(name: str) -> tuple[str, str]:
    parts = (name or "").strip().split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        return parts[0], ""
    return "", ""


def get_user_preferences(db: Session, user_id: str) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        pref = UserPreference(user_id=user_id, language="en-US", theme="system")
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


# --- Endpoints ---

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(user=Depends(get_current_user)):
    try:
        first_name, last_name = get_user_full_name(user.name)
        return {
            "id": user.id,
            "firstName": first_name,
            "lastName": last_name,
            "email": user.email,
            "avatar": user.profile_image_url,
            "role": user.role,
        }
    except Exception as err:
        log.error(f"Error getting profile: {err}")
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    user=Depends(get_current_user),
):
    try:
        from open_webui.utils.misc import validate_email_format

        if not validate_email_format(request.email.lower()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT,
            )

        existing_user = Users.get_user_by_email(request.email.lower())
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.EMAIL_TAKEN,
            )

        full_name = f"{request.firstName} {request.lastName}".strip()
        update_payload = {
            "name": full_name,
            "email": request.email.lower(),
        }

        if request.avatar is not None and request.avatar.strip() != "":
            update_payload["profile_image_url"] = request.avatar.strip()

        updated_user = Users.update_user_by_id(user.id, update_payload)
        if not updated_user:
            raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT("Failed to update profile"))

        return {
            "id": updated_user.id,
            "firstName": request.firstName,
            "lastName": request.lastName,
            "email": updated_user.email,
            "avatar": updated_user.profile_image_url,
            "role": updated_user.role,
        }

    except HTTPException:
        raise
    except Exception as err:
        log.error(f"Error updating profile: {err}")
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


@router.put("/password")
async def change_password(
    request: PasswordChangeRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_session_local),
):
    try:
        # Get password hash from auth table (where passwords are stored)
        result = db.execute(
            text("SELECT password FROM auth WHERE email = :email"),
            {"email": user.email}
        ).first()
        
        if not result or not result[0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found",
            )

        password_hash = result[0]

        # Verify the old password
        if not verify_password(request.oldPassword, password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid old password",
            )

        if len(request.newPassword) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long",
            )

        hashed_password = get_password_hash(request.newPassword)
        
        # Update password in auth table
        db.execute(
            text("UPDATE auth SET password = :password WHERE email = :email"),
            {"password": hashed_password, "email": user.email}
        )
        db.commit()

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as err:
        log.error(f"Error changing password: {err}")
        db.rollback()
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    user=Depends(get_current_user),
    db: Session = Depends(get_session_local),
):
    try:
        preferences = get_user_preferences(db, user.id)
        return {
            "language": preferences.language,
            "theme": preferences.theme,
        }
    except Exception as err:
        log.error(f"Error getting preferences: {err}")
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    request: PreferencesUpdateRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_session_local),
):
    try:
        valid_themes = ["light", "dark", "system"]
        if request.theme not in valid_themes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Theme must be one of: {', '.join(valid_themes)}",
            )

        preferences = get_user_preferences(db, user.id)
        preferences.language = request.language
        preferences.theme = request.theme

        db.add(preferences)
        db.commit()
        db.refresh(preferences)

        return {
            "language": preferences.language,
            "theme": preferences.theme,
        }

    except HTTPException:
        raise
    except Exception as err:
        log.error(f"Error updating preferences: {err}")
        db.rollback()
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    try:
        AVATAR_DIR.mkdir(parents=True, exist_ok=True)

        if not file.filename:
            raise HTTPException(400, detail="No file selected")

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
            raise HTTPException(400, detail="Unsupported format")

        filename = f"{user.id}.{ext}"
        file_path = AVATAR_DIR / filename

        content = await file.read()
        file_path.write_bytes(content)

        import time
        avatar_url = f"/api/v1/settings/avatar/{filename}?t={int(time.time())}"

        Users.update_user_by_id(user.id, {"profile_image_url": avatar_url})

        return {"avatar_url": avatar_url}

    except HTTPException:
        raise
    except Exception as err:
        log.error(f"Error uploading avatar: {err}")
        raise HTTPException(500, detail=str(err))


@router.get("/avatar/{filename}")
async def get_avatar(filename: str):
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(400, detail="Invalid filename")

    file_path = AVATAR_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(404, detail=f"Avatar not found: {safe_name}")

    return FileResponse(file_path)
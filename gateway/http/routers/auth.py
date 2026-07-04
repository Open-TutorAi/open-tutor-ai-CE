"""Authentication router — /auths/* routes matching UI calls."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from jwt import encode
from pydantic import BaseModel, EmailStr

from accounts.users.service import AccountService
from config import settings
from data.models import User
from gateway.http.dependencies import get_account_service, get_current_user

router = APIRouter(prefix="/auths", tags=["auth"])


class SignInRequest(BaseModel):
    email: str
    password: str


class SignUpRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    profile_image_url: Optional[str] = None
    role: Optional[str] = None


class AddUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"
    profile_image_url: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: str
    profile_image_url: str


class UpdatePasswordRequest(BaseModel):
    password: str
    new_password: str


def _create_token(user_id: str) -> str:
    expires = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    return encode(
        {"sub": user_id, "exp": expires, "iat": datetime.utcnow()},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _set_auth_cookie(response: Response, token: str) -> None:
    """Attach the session JWT as an HttpOnly cookie — the browser auth channel.

    HttpOnly keeps the token out of reach of any script running on the page
    (XSS cannot exfiltrate it); SameSite=Lax stops the browser attaching it to
    cross-site requests. `Secure` is enabled via AUTH_COOKIE_SECURE on TLS
    deployments.
    """
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=settings.JWT_EXPIRATION_HOURS * 3600,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )


def _user_payload(token: str, user: User) -> dict:
    return {
        "token": token,
        "token_type": "Bearer",
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": "admin" if user.is_admin else (user.role or "user"),
        "profile_image_url": user.profile_image_url,
    }


@router.get("/")
async def get_session_user(current_user: User = Depends(get_current_user)):
    """Return current session user — UI getSessionUser."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": "admin" if current_user.is_admin else (current_user.role or "user"),
        "profile_image_url": current_user.profile_image_url,
    }


@router.post("/signin")
async def sign_in(
    request: SignInRequest,
    response: Response,
    svc: AccountService = Depends(get_account_service),
):
    """Sign in — UI calls /auths/signin. Sets the HttpOnly session cookie."""
    user = svc.authenticate(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive"
        )
    token = _create_token(user.id)
    _set_auth_cookie(response, token)
    return _user_payload(token, user)


@router.post("/login")
async def login(
    request: SignInRequest,
    response: Response,
    svc: AccountService = Depends(get_account_service),
):
    """Login alias — kept for internal/tool use."""
    return await sign_in(request, response, svc)


@router.post("/signup")
async def signup(
    request: SignUpRequest,
    response: Response,
    svc: AccountService = Depends(get_account_service),
):
    """Sign up — first user becomes admin. Sets the HttpOnly session cookie."""
    is_admin = svc.count_users() == 0
    try:
        user = svc.create_user(
            email=request.email,
            name=request.name,
            password_plain=request.password,
            profile_image_url=request.profile_image_url,
            is_admin=is_admin,
            role=request.role or "user",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    token = _create_token(user.id)
    _set_auth_cookie(response, token)
    return _user_payload(token, user)


@router.post("/cookie")
async def establish_cookie_session(
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """Exchange a Bearer-authenticated request for an HttpOnly cookie session.

    Used by flows that receive a token out-of-band (e.g. OAuth URL fragments)
    so the browser can continue with cookie auth instead of storing the token.
    """
    _set_auth_cookie(response, _create_token(current_user.id))
    return {"status": "success"}


@router.get("/signout")
async def sign_out(response: Response):
    """Sign out — clears the session cookie."""
    response.delete_cookie(settings.AUTH_COOKIE_NAME, path="/")
    return {"status": "success"}


@router.get("/user-count")
async def get_user_count(svc: AccountService = Depends(get_account_service)):
    return {"count": svc.count_users()}


@router.post("/add")
async def add_user(
    request: AddUserRequest,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    """Admin creates a new user with a specified role."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    try:
        user = svc.create_user(
            email=request.email,
            name=request.name,
            password_plain=request.password,
            profile_image_url=request.profile_image_url,
            is_admin=(request.role == "admin"),
            role=request.role or "user",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    token = _create_token(user.id)
    return _user_payload(token, user)


@router.post("/update/profile")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    user = svc.update_user(
        current_user.id,
        name=request.name,
        profile_image_url=request.profile_image_url,
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": "admin" if user.is_admin else (user.role or "user"),
        "profile_image_url": user.profile_image_url,
    }


@router.post("/update/password")
async def update_password(
    request: UpdatePasswordRequest,
    current_user: User = Depends(get_current_user),
    svc: AccountService = Depends(get_account_service),
):
    if not svc.authenticate(current_user.email, request.password):
        raise HTTPException(status_code=400, detail="Invalid current password")
    svc.update_password(current_user.id, request.new_password)
    return {"message": "Password updated successfully"}


# ── Admin config stubs ────────────────────────────────────────────────────────


@router.get("/admin/details")
async def get_admin_details(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/admin/config")
async def get_admin_config(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return {
        "signUpEnabled": True,
        "defaultUserRole": "user",
        "jwtExpiresDuration": settings.JWT_EXPIRATION_HOURS,
        "ldap": {"enabled": False},
    }


@router.post("/admin/config")
async def update_admin_config(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return body


@router.get("/admin/config/ldap")
async def get_ldap_config(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return {"enabled": False}


@router.post("/admin/config/ldap")
async def update_ldap_config(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return body


@router.get("/admin/config/ldap/server")
async def get_ldap_server_config(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return {}


@router.post("/admin/config/ldap/server")
async def update_ldap_server_config(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return body


@router.get("/signup/enabled")
async def get_signup_enabled():
    return True


@router.post("/signup/enabled/toggle")
async def toggle_signup_enabled(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return True


@router.post("/signup/user/role")
async def update_default_user_role(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return body


@router.get("/token/expires")
async def get_token_expires(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return {"duration": settings.JWT_EXPIRATION_HOURS}


@router.post("/token/expires/update")
async def update_token_expires(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return body


@router.get("/api_key")
async def get_api_key(current_user: User = Depends(get_current_user)):
    return {"api_key": ""}


@router.post("/api_key")
async def create_api_key(current_user: User = Depends(get_current_user)):
    return {"api_key": ""}


@router.delete("/api_key")
async def delete_api_key(current_user: User = Depends(get_current_user)):
    return {"api_key": ""}


@router.post("/ldap")
async def ldap_login(
    body: Dict[str, Any],
    svc: AccountService = Depends(get_account_service),
):
    raise HTTPException(status_code=501, detail="LDAP authentication not implemented")

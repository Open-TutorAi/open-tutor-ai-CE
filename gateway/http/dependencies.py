"""FastAPI dependency injection — auth guard + service factories."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, decode
from sqlalchemy.orm import Session

from accounts.users.service import AccountService
from config import settings
from content.files.service import FilesService
from data.database import get_db
from data.models import User
from governance.self_regulation.service import SelfRegulationService
from learning.supports.service import SupportsService

security = HTTPBearer()


# ── Auth guard ────────────────────────────────────────────────────────────────


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Decode JWT and return the authenticated user."""
    try:
        payload = decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = AccountService(db).get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


# ── JWT helper ───────────────────────────────────────────────────────────────


def decode_jwt_token(token: str) -> dict | None:
    """Decode a JWT token string. Returns payload dict or None if invalid."""
    try:
        import jwt

        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except Exception:
        return None


# ── Service factories ─────────────────────────────────────────────────────────


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)


def get_supports_service(db: Session = Depends(get_db)) -> SupportsService:
    return SupportsService(db)


def get_self_regulation_service(db: Session = Depends(get_db)) -> SelfRegulationService:
    return SelfRegulationService(db)


def get_files_service(db: Session = Depends(get_db)) -> FilesService:
    return FilesService(db)

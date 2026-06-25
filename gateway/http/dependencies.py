"""FastAPI dependency injection — auth guard + service factories."""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, decode
from sqlalchemy.orm import Session

from accounts.users.service import AccountService
from assignments.service import AssignmentsService
from classrooms.service import ClassroomsService
from config import settings
from content.files.service import FilesService
from data.database import get_db
from data.models import User
from exams.service import ExamsService
from governance.self_regulation.service import SelfRegulationService
from guardians.service import GuardiansService
from learning.supports.service import SupportsService
from messaging.service import MessagingService
from resources.service import ResourcesService

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


# ── Role guard ─────────────────────────────────────────────────────────────────


async def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    """Authorize a teacher-only route. Caller must be authenticated AND role==teacher."""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role required",
        )
    return current_user


# ── Service factories ─────────────────────────────────────────────────────────


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)


def get_classrooms_service(db: Session = Depends(get_db)) -> ClassroomsService:
    return ClassroomsService(db)


def get_guardians_service(db: Session = Depends(get_db)) -> GuardiansService:
    return GuardiansService(db)


def get_assignments_service(db: Session = Depends(get_db)) -> AssignmentsService:
    return AssignmentsService(db)


def get_resources_service(db: Session = Depends(get_db)) -> ResourcesService:
    return ResourcesService(db)


def get_messaging_service(db: Session = Depends(get_db)) -> MessagingService:
    return MessagingService(db)


def get_exams_service(db: Session = Depends(get_db)) -> ExamsService:
    return ExamsService(db)


def get_supports_service(db: Session = Depends(get_db)) -> SupportsService:
    return SupportsService(db)


def get_self_regulation_service(db: Session = Depends(get_db)) -> SelfRegulationService:
    return SelfRegulationService(db)


def get_files_service(db: Session = Depends(get_db)) -> FilesService:
    return FilesService(db)


@dataclass
class Pagination:
    """Bounded list window. `limit` is hard-capped at 100 (the team's max page size);
    callers that omit the params get the first 100 items, preserving prior behaviour
    for the small collections this app deals with today."""

    limit: int
    offset: int

    def apply(self, items):
        return items[self.offset : self.offset + self.limit]


def pagination(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)

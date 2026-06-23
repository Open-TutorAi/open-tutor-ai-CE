"""FastAPI dependency injection — auth guard + service factories."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import decode, InvalidTokenError
from sqlalchemy.orm import Session

from config import settings
from data.database import get_db
from data.models import User
from content.files.service import FilesService
from accounts.users.service import AccountService
from learning.supports.service import SupportsService
from learning.supports.error_cards.service import ErrorCardsService
from governance.self_regulation.service import SelfRegulationService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
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


def decode_jwt_token(token: str) -> dict | None:
    try:
        import jwt
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except Exception:
        return None


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    return AccountService(db)


def get_supports_service(db: Session = Depends(get_db)) -> SupportsService:
    return SupportsService(db)


def get_error_cards_service(db: Session = Depends(get_db)) -> ErrorCardsService:
    return ErrorCardsService(db)


def get_self_regulation_service(db: Session = Depends(get_db)) -> SelfRegulationService:
    return SelfRegulationService(db)


def get_files_service(db: Session = Depends(get_db)) -> FilesService:
    return FilesService(db)

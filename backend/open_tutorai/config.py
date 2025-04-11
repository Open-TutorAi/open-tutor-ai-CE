from open_tutorai.env import (
    ENABLE_SIGNUP,
    ENABLE_LOGIN_FORM,
    JWT_EXPIRES_IN,
    WEBHOOK_URL,
)
from pydantic import BaseModel
from typing import Optional


class AppConfig(BaseModel):
    ENABLE_SIGNUP: bool = ENABLE_SIGNUP
    ENABLE_LOGIN_FORM: bool = ENABLE_LOGIN_FORM
    JWT_EXPIRES_IN: str = JWT_EXPIRES_IN
    WEBHOOK_URL: Optional[str] = WEBHOOK_URL
    USER_PERMISSIONS: dict = {}

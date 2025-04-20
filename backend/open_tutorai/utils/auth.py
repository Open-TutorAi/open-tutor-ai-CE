import logging
import uuid
import jwt
import base64
import hmac
import hashlib
import requests
import os

from datetime import UTC, datetime, timedelta
from typing import Optional, Union, List, Dict

from open_webui.models.users import Users
from open_webui.utils.auth import get_current_user

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import WEBUI_SECRET_KEY, TRUSTED_SIGNATURE_KEY, STATIC_DIR

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

logging.getLogger("passlib").setLevel(logging.ERROR)


SESSION_SECRET = WEBUI_SECRET_KEY
ALGORITHM = "HS256"

##############
# Auth Utils
##############



def get_verified_teacher_or_admin_user(user=Depends(get_current_user)):
    if user.role not in {"teacher", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return user
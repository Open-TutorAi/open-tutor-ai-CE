import json
import logging
from typing import Optional

from open_webui.models.chats import (
    ChatForm,
    ChatImportForm,
    ChatResponse,
    Chats,
    ChatTitleIdResponse,
)
from open_webui.models.tags import TagModel, Tags
from open_webui.models.folders import Folders

from open_webui.config import ENABLE_ADMIN_CHAT_ACCESS, ENABLE_ADMIN_EXPORT
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_tutorai.utils.auth import get_verified_teacher_or_admin_user

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter(tags=["chats"])

############################
# GetAllChatsInDB
############################

@router.get("/chats/all/db", response_model=list[ChatResponse])
async def get_all_user_chats_in_db(user=Depends(get_verified_teacher_or_admin_user)):
    try:
        return [ChatResponse(**chat.model_dump()) for chat in Chats.get_chats()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
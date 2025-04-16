from fastapi import APIRouter, Depends, HTTPException, status
from open_webui.models.feedbacks import FeedbackModel, FeedbackResponse, Feedbacks
from open_webui.models.users import Users, UserModel
from open_tutorai.utils.auth import get_verified_teacher_or_admin_user
from typing import Optional

router = APIRouter(tags=["feedbacks"])

class FeedbackUserResponse(FeedbackResponse):
    user: Optional[UserModel] = None

@router.get("/evaluations/feedbacks/all", response_model=list[FeedbackUserResponse])
async def get_all_feedbacks(user=Depends(get_verified_teacher_or_admin_user)):
    try:
        feedbacks = Feedbacks.get_all_feedbacks()
        return [
            FeedbackUserResponse(
                **feedback.model_dump(), user=Users.get_user_by_id(feedback.user_id)
            )
            for feedback in feedbacks
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 
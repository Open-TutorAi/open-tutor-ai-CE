from fastapi import APIRouter, Depends, HTTPException
from open_webui.models.feedbacks import FeedbackForm, FeedbackTable
from open_webui.env import GLOBAL_LOG_LEVEL
from open_tutorai.utils.auth import get_verified_teacher_or_admin_user
import logging

log = logging.getLogger(__name__)
log.setLevel(GLOBAL_LOG_LEVEL)

router = APIRouter(tags=["response-feedbacks"])

feedback_table = FeedbackTable()


@router.get("/evaluations/response-feedbacks/all")
async def get_all_response_feedbacks(user=Depends(get_verified_teacher_or_admin_user)):
    try:
        feedbacks = feedback_table.get_feedbacks_by_type("response_comparison")
        return feedbacks
    except Exception as e:
        log.error(f"Error getting response feedbacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluations/response-feedback")
async def create_response_feedback(
    form_data: FeedbackForm, user=Depends(get_verified_teacher_or_admin_user)
):
    try:
        feedback = feedback_table.insert_new_feedback(user.id, form_data)
        if not feedback:
            raise HTTPException(status_code=500, detail="Failed to create feedback")
        return feedback
    except Exception as e:
        log.error(f"Error creating response feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluations/response-feedback/{feedback_id}")
async def get_response_feedback(feedback_id: str, user=Depends(get_verified_teacher_or_admin_user)):
    try:
        feedback = feedback_table.get_feedback_by_id(feedback_id)
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return feedback
    except Exception as e:
        log.error(f"Error getting response feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from open_tutorai.routers.video_engagement import compute_video_score

router = APIRouter()
_video_scores: dict[str, float] = {}
 
class VideoFrameRequest(BaseModel):
    frame: str
    user_id: str = "default"
 
class VideoScoreResponse(BaseModel):
    user_id: str
    video_score: Optional[float]
    status: str
 
@router.post("/api/engagement/video", response_model=VideoScoreResponse)
async def receive_video_frame(payload: VideoFrameRequest):
    score = compute_video_score(payload.frame)
    if score is not None:
        _video_scores[payload.user_id] = score
        try:
            open("/tmp/engagement_video_score.txt", "w").write(str(score))
        except:
            pass
        return VideoScoreResponse(user_id=payload.user_id, video_score=score, status="ok")
    else:
        return VideoScoreResponse(user_id=payload.user_id, video_score=None, status="no_face_detected")
 
def get_video_score(user_id: str = "default") -> Optional[float]:
    return _video_scores.get(user_id)
 
def clear_video_score(user_id: str = "default"):
    _video_scores.pop(user_id, None)
 
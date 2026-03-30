import json
import logging
from datetime import datetime
from typing import Optional, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("engagement")

THRESHOLD_LOW  = 0.50
THRESHOLD_HIGH = 0.70

ADAPTATIONS = {
    "low":    ("IMPORTANT INSTRUCTION: The student seems disengaged. "
               "Simplify your explanation, use ONE concrete example, "
               "keep your response SHORT (max 3-4 sentences), "
               "and end with ONE simple interactive question."),
    "medium": ("IMPORTANT INSTRUCTION: The student is moderately engaged. "
               "Maintain the current level and end with a brief verification question."),
    "high":   ("IMPORTANT INSTRUCTION: The student is highly engaged. "
               "Go deeper, introduce nuances, use technical vocabulary, "
               "and accelerate the pedagogical pace."),
}


def _text_score(message: str) -> float:
    words = message.strip().split()
    n = len(words)
    if n == 0:
        return 0.0
    if   n >= 20: ls = 1.0
    elif n >= 10: ls = 0.75
    elif n >= 5:  ls = 0.50
    elif n >= 2:  ls = 0.25
    else:         ls = 0.05
    ttr = len(set(w.lower() for w in words)) / n
    qb  = min(message.count("?") * 0.05, 0.15)
    return round(max(0.0, min(1.0, 0.50*ls + 0.35*ttr + 0.15*(qb/0.15))), 3)


def compute_engagement(message: str,
                       video_score: Optional[float] = None,
                       audio_score: Optional[float] = None) -> Tuple[float, str]:
    text    = _text_score(message)
    sources = [("text", text, 1.0)]
    if video_score is not None:
        sources.append(("video", video_score, 0.8))
    if audio_score is not None:
        sources.append(("audio", audio_score, 1.2))
    total = sum(w for _, _, w in sources)
    fused = round(sum(v*w for _, v, w in sources) / total, 3)
    level = "low" if fused < THRESHOLD_LOW else "high" if fused >= THRESHOLD_HIGH else "medium"
    print(f"[Engagement] {level.upper()} fused={fused} text={text} video={video_score}", flush=True)
    return fused, level


class EngagementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "POST" and request.url.path == "/api/chat/completions":
            try:
                body_bytes = await request.body()
                body       = json.loads(body_bytes)
                messages   = body.get("messages", [])

                user_message = ""
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        c = msg.get("content", "")
                        user_message = c if isinstance(c, str) else str(c)
                        break

                if user_message:
                    # video score
                    video_score = None
                    try:
                        from open_tutorai.routers.video_router import get_video_score, clear_video_score
                        video_score = get_video_score("default")
                        if video_score is not None:
                            clear_video_score("default")
                    except Exception:
                        pass

                    score, level = compute_engagement(user_message, video_score=video_score)
                    _save_record(user_message, score, level, video_score)

                    modalities = "text" + ("+video" if video_score else "")
                    sys_msg = f"[ENGAGEMENT: {level.upper()} | score={score} | {modalities}]\n{ADAPTATIONS[level]}"

                    has_system = False
                    for msg in messages:
                        if msg.get("role") == "system":
                            msg["content"] += "\n\n" + sys_msg
                            has_system = True
                            break
                    if not has_system:
                        messages.insert(0, {"role": "system", "content": sys_msg})
                    body["messages"] = messages

                # Fix : reconstruire receive correctement
                new_body = json.dumps(body).encode("utf-8")

                async def new_receive():
                    return {"type": "http.request", "body": new_body, "more_body": False}

                request = Request(request.scope, new_receive)

            except Exception as e:
                logger.error(f"[Engagement] error: {e}", exc_info=True)

        return await call_next(request)


def _save_record(message, score, level, video_score=None):
    import os
    path  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "engagement_dataset.jsonl")
    words = message.strip().split()
    rec   = {
        "timestamp": datetime.now().isoformat(),
        "engagement_score": score, "engagement_level": level,
        "message_length": len(words),
        "word_diversity": round(len(set(w.lower() for w in words)) / max(len(words),1), 3),
        "question_marks": message.count("?"),
        "video_score": video_score,
        "modalities": ["text"] + (["video"] if video_score else []),
        "preview": message[:80],
    }
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        logger.warning(f"[Engagement] dataset error: {e}")
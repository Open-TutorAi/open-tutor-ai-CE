import cv2
import numpy as np
import base64
import logging
from typing import Optional

logger = logging.getLogger("video_engagement")

# ── Détection MediaPipe disponible ────────────────────────────────────────────
MP_AVAILABLE = False
try:
    import mediapipe as mp
    if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_mesh'):
        MP_AVAILABLE = True
        print("[Video] MediaPipe FaceMesh disponible")
    else:
        print("[Video] MediaPipe sans solutions — fallback OpenCV")
except ImportError:
    print("[Video] MediaPipe absent — fallback OpenCV")

# ── Landmarks indices ─────────────────────────────────────────────────────────
LEFT_EYE     = [362, 385, 387, 263, 373, 380]
RIGHT_EYE    = [33,  160, 158, 133, 153, 144]
MOUTH_LEFT   = 61
MOUTH_RIGHT  = 291
MOUTH_TOP    = 13
MOUTH_BOTTOM = 14
LEFT_IRIS    = [474, 475, 476, 477]
RIGHT_IRIS   = [469, 470, 471, 472]


def _ear(lm, indices, w, h):
    pts = [(lm[i].x * w, lm[i].y * h) for i in indices]
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C + 1e-6)


def _smile_score(lm, w, h):
    width  = abs(lm[MOUTH_RIGHT].x - lm[MOUTH_LEFT].x) * w
    height = abs(lm[MOUTH_BOTTOM].y - lm[MOUTH_TOP].y) * h
    return min(1.0, max(0.0, (width / (height + 1e-6) - 2.0) / 8.0))


# ── Score principal ───────────────────────────────────────────────────────────

def compute_video_score(frame_base64: str) -> Optional[float]:
    """
    Reçoit une frame JPEG en base64.
    Retourne un video_score entre 0.0 et 1.0.
    """
    try:
        img_data = base64.b64decode(frame_base64)
        np_arr   = np.frombuffer(img_data, np.uint8)
        frame    = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return None
    except Exception as e:
        logger.error(f"[Video] Frame decode error: {e}")
        return None

    if MP_AVAILABLE:
        return _mediapipe_score(frame)
    else:
        return _opencv_score(frame)


def _mediapipe_score(frame: np.ndarray) -> Optional[float]:
    """Score précis via MediaPipe FaceMesh."""
    try:
        h, w = frame.shape[:2]
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        with mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        ) as fm:
            results = fm.process(rgb)

        if not results.multi_face_landmarks:
            print("[Video] No face detected → score=0.1")
            return 0.1

        lm = results.multi_face_landmarks[0].landmark

        # EAR — yeux ouverts
        ear_avg   = (_ear(lm, LEFT_EYE, w, h) + _ear(lm, RIGHT_EYE, w, h)) / 2.0
        eye_score = min(1.0, max(0.0, (ear_avg - 0.15) / 0.20))

        # Gaze — iris centré
        deviation  = (abs(np.mean([lm[i].x for i in LEFT_IRIS])  - np.mean([lm[i].x for i in LEFT_EYE])) +
                      abs(np.mean([lm[i].x for i in RIGHT_IRIS]) - np.mean([lm[i].x for i in RIGHT_EYE])))
        gaze_score = min(1.0, max(0.0, 1.0 - deviation * 20.0))

        # Smile
        smile = _smile_score(lm, w, h)

        score = round(0.40 * eye_score + 0.35 * gaze_score + 0.25 * smile, 3)
        print(f"[Video] 👁 eye={eye_score:.2f} gaze={gaze_score:.2f} smile={smile:.2f} → video_score={score}")
        return score

    except Exception as e:
        logger.error(f"[Video] MediaPipe error: {e}")
        return _opencv_score(frame)


def _opencv_score(frame: np.ndarray) -> float:
    """Fallback OpenCV — détecte juste la présence du visage."""
    try:
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, 1.1, 4)
        score = 0.5 if len(faces) > 0 else 0.1
        print(f"[Video] OpenCV fallback — faces={len(faces)} → score={score}")
        return score
    except Exception as e:
        logger.error(f"[Video] OpenCV error: {e}")
        return 0.1
import base64
import logging
import threading
from typing import Optional

logger = logging.getLogger("video_engagement")


MP_AVAILABLE = False
DEEPFACE_AVAILABLE = False
CV_AVAILABLE = False

try:
    import cv2
    import numpy as np

    CV_AVAILABLE = True
except Exception:
    cv2 = None
    np = None
    logger.debug("opencv/numpy not available — video scoring disabled")

try:
    import mediapipe as mp

    if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
        MP_AVAILABLE = True
    logger.debug("MediaPipe available")
except Exception:
    logger.debug("MediaPipe not available — video scoring disabled")

try:
    from deepface import DeepFace

    DEEPFACE_AVAILABLE = True
    logger.debug("DeepFace available")
except ImportError:
    logger.debug("DeepFace not available — emotion estimation disabled")

# --- Face Mesh Indices ---
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM = 61, 291, 13, 14
NOSE_TIP = 1
CHIN = 152
LEFT_EYE_L = 33
RIGHT_EYE_R = 263

EMOTION_WEIGHTS = {
    "happy": 1.0,
    "surprise": 0.8,
    "neutral": 0.5,
    "sad": 0.2,
    "fear": 0.2,
    "disgust": 0.1,
    "angry": 0.1,
}

# Reuse a single FaceMesh graph across frames — instantiating one per call is
# expensive and caps the real-time frame rate. Guard with a lock because the
# MediaPipe graph is not safe to call concurrently from worker threads.
_FACE_MESH = None
_FACE_MESH_LOCK = threading.Lock()


def _get_face_mesh():
    """Lazily build and cache the shared FaceMesh instance."""
    global _FACE_MESH
    if _FACE_MESH is None and MP_AVAILABLE:
        _FACE_MESH = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )
    return _FACE_MESH


# How sensitive the gaze penalty is: how far off-centre (as a fraction of the
# half eye-width) the iris must drift before the score collapses. ~0.45 means
# the iris reaching ~45% of the way to the eye corner already scores ~0.
_GAZE_SENSITIVITY = 2.2


def _gaze_ratio(lm, iris_indices, eye_indices) -> float:
    """Horizontal gaze score in [0, 1], 1 = looking straight ahead.

    Scale-invariant: the iris offset from the eye centre is normalised by the
    eye's own width, so it no longer depends on how close the face is to the
    camera (the previous absolute-pixel formula could never drop below ~0.6).
    """
    iris_x = np.mean([lm[i].x for i in iris_indices])
    eye_xs = [lm[i].x for i in eye_indices]
    eye_center = np.mean(eye_xs)
    half_width = (max(eye_xs) - min(eye_xs)) / 2.0 + 1e-6
    offset = abs(iris_x - eye_center) / half_width  # 0 = centred, ~1 = at corner
    return max(0.0, 1.0 - offset * _GAZE_SENSITIVITY)


def _ear(lm, indices, w, h):
    pts = [(lm[i].x * w, lm[i].y * h) for i in indices]
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C + 1e-6)


def _head_pose_score(lm, w, h):
    nose = np.array([lm[NOSE_TIP].x * w, lm[NOSE_TIP].y * h])
    chin = np.array([lm[CHIN].x * w, lm[CHIN].y * h])
    l_eye = np.array([lm[LEFT_EYE_L].x * w, lm[LEFT_EYE_L].y * h])
    r_eye = np.array([lm[RIGHT_EYE_R].x * w, lm[RIGHT_EYE_R].y * h])

    eye_center_x = (l_eye[0] + r_eye[0]) / 2
    deviation = abs(nose[0] - eye_center_x) / (abs(r_eye[0] - l_eye[0]) + 1e-6)
    horizontal_score = max(0.0, 1.0 - deviation * 2.0)

    vertical_ok = 1.0 if chin[1] > nose[1] else 0.3
    return round(0.6 * horizontal_score + 0.4 * vertical_ok, 3)


def _vertical_attention(lm, h):
    nose_y = lm[NOSE_TIP].y * h
    eye_y = (lm[LEFT_EYE_L].y + lm[RIGHT_EYE_R].y) / 2 * h
    diff = nose_y - eye_y
    if diff > 40:
        return 0.2
    elif diff > 20:
        return 0.5
    return 1.0


def _emotion_score(frame):
    if not DEEPFACE_AVAILABLE:
        return None
    try:
        result = DeepFace.analyze(
            frame, actions=["emotion"], enforce_detection=False, silent=True
        )
        dominant = (
            result[0]["dominant_emotion"]
            if isinstance(result, list)
            else result["dominant_emotion"]
        )
        return EMOTION_WEIGHTS.get(dominant, 0.3), dominant
    except Exception as e:
        logger.warning(f"[Video] DeepFace error: {e}")
        return None


def compute_video_score(frame_base64: str) -> Optional[float]:
    """
    Analyzes computer vision features from base64 frames to capture engagement.
    Contains ONLY extraction logic.
    """
    if not (MP_AVAILABLE and CV_AVAILABLE):
        logger.debug("[Video] CV stack not available — skipping video scoring.")
        return None

    try:
        img_data = base64.b64decode(frame_base64)
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return None
    except Exception:
        return None

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    try:
        fm = _get_face_mesh()
        if fm is None:
            return None

        with _FACE_MESH_LOCK:
            results = fm.process(rgb)

        if not results.multi_face_landmarks:
            logger.debug("[Video] no face detected in %dx%d frame", w, h)
            return None

        lm = results.multi_face_landmarks[0].landmark

        ear = (_ear(lm, LEFT_EYE, w, h) + _ear(lm, RIGHT_EYE, w, h)) / 2
        eye_score = min(1.0, max(0.0, (ear - 0.15) / 0.20))

        gaze_score = (_gaze_ratio(lm, LEFT_IRIS, LEFT_EYE) + _gaze_ratio(lm, RIGHT_IRIS, RIGHT_EYE)) / 2

        width = abs(lm[MOUTH_RIGHT].x - lm[MOUTH_LEFT].x) * w
        height = abs(lm[MOUTH_BOTTOM].y - lm[MOUTH_TOP].y) * h
        smile_score = min(1.0, max(0.0, (width / (height + 1e-6) - 2.0) / 8.0))

        head_score = _head_pose_score(lm, w, h)
        attention_score = _vertical_attention(lm, h)

    except Exception as e:
        logger.error(f"[Video] Processing error: {e}")
        return None

    emotion_result = _emotion_score(frame)
    emotion_score = emotion_result[0] if emotion_result else 0.5

    video_score = round(
        0.25 * eye_score
        + 0.20 * gaze_score
        + 0.15 * smile_score
        + 0.15 * head_score
        + 0.15 * emotion_score
        + 0.10 * attention_score,
        3,
    )

    if gaze_score < 0.3:
        video_score *= 0.6

    final_score = max(0.0, min(1.0, video_score))

    logger.debug(
        "[Video] face detected — score=%.3f (gaze=%.2f eye=%.2f head=%.2f)",
        final_score,
        gaze_score,
        eye_score,
        head_score,
    )
    return final_score

import cv2
import mediapipe as mp
import numpy as np
import base64
import logging
from typing import Optional

logger = logging.getLogger("video_engagement")

# Flags to enable/disable features depending on installed libs
MP_AVAILABLE = False
DEEPFACE_AVAILABLE = False

# Check MediaPipe
try:
    if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_mesh'):
        MP_AVAILABLE = True
except:
    pass

# Check DeepFace (emotion analysis)
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print("[Video] DeepFace available")
except:
    print("[Video] DeepFace not available")


# Face mesh indices (only what we actually use)
LEFT_EYE   = [362, 385, 387, 263, 373, 380]
RIGHT_EYE  = [33, 160, 158, 133, 153, 144]
LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

MOUTH_LEFT, MOUTH_RIGHT, MOUTH_TOP, MOUTH_BOTTOM = 61, 291, 13, 14

NOSE_TIP = 1
CHIN = 152
LEFT_EYE_L = 33
RIGHT_EYE_R = 263


# Rough mapping: how each emotion contributes to engagement
EMOTION_WEIGHTS = {
    "happy": 1.0,
    "surprise": 0.8,
    "neutral": 0.5,
    "sad": 0.2,
    "fear": 0.2,
    "disgust": 0.1,
    "angry": 0.1,
}


def _ear(lm, indices, w, h):
    """Eye Aspect Ratio: measures how open the eye is."""
    pts = [(lm[i].x * w, lm[i].y * h) for i in indices]
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C + 1e-6)


def _head_pose_score(lm, w, h):
    """Checks if the face is roughly centered and upright."""
    nose = np.array([lm[NOSE_TIP].x * w, lm[NOSE_TIP].y * h])
    chin = np.array([lm[CHIN].x * w, lm[CHIN].y * h])
    l_eye = np.array([lm[LEFT_EYE_L].x * w, lm[LEFT_EYE_L].y * h])
    r_eye = np.array([lm[RIGHT_EYE_R].x * w, lm[RIGHT_EYE_R].y * h])

    # Horizontal alignment (nose vs eye center)
    eye_center_x = (l_eye[0] + r_eye[0]) / 2
    deviation = abs(nose[0] - eye_center_x) / (abs(r_eye[0] - l_eye[0]) + 1e-6)
    horizontal_score = max(0.0, 1.0 - deviation * 2.0)

    # Simple vertical sanity check (chin below nose)
    vertical_ok = 1.0 if chin[1] > nose[1] else 0.3

    return round(0.6 * horizontal_score + 0.4 * vertical_ok, 3)


def _vertical_attention(lm, h):
    """Detects if the user is looking down (e.g. at phone or notes)."""
    nose_y = lm[NOSE_TIP].y * h
    eye_y = (lm[LEFT_EYE_L].y + lm[RIGHT_EYE_R].y) / 2 * h

    diff = nose_y - eye_y

    if diff > 40:
        return 0.2
    elif diff > 20:
        return 0.5
    return 1.0


def _emotion_score(frame):
    """Runs DeepFace and converts emotion → engagement weight."""
    if not DEEPFACE_AVAILABLE:
        return None

    try:
        result = DeepFace.analyze(
            frame,
            actions=['emotion'],
            enforce_detection=False,
            silent=True
        )

        dominant = result[0]['dominant_emotion'] if isinstance(result, list) else result['dominant_emotion']
        score = EMOTION_WEIGHTS.get(dominant, 0.3)

        print(f"[Video] emotion={dominant} → {score}", flush=True)

        return score, dominant

    except Exception as e:
        logger.warning(f"[Video] DeepFace error: {e}")
        return None


def compute_video_score(frame_base64: str) -> Optional[float]:
    """Main entry: returns engagement score from a single frame."""

    # Decode base64 → OpenCV image
    try:
        img_data = base64.b64decode(frame_base64)
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return None
    except:
        return None

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Default fallback values (used if detection fails)
    eye_score = gaze_score = smile_score = head_score = attention_score = 0.3

    if MP_AVAILABLE:
        try:
            # FaceMesh is re-created per frame here (could be optimized later)
            with mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            ) as fm:
                results = fm.process(rgb)

            if not results.multi_face_landmarks:
                print("[Video] No face → LOW", flush=True)
                return 0.1

            lm = results.multi_face_landmarks[0].landmark

            # Eye openness
            ear = (_ear(lm, LEFT_EYE, w, h) + _ear(lm, RIGHT_EYE, w, h)) / 2
            eye_score = min(1.0, max(0.0, (ear - 0.15) / 0.20))

            # Gaze: iris vs eye center alignment
            dev = (
                abs(np.mean([lm[i].x for i in LEFT_IRIS]) - np.mean([lm[i].x for i in LEFT_EYE])) +
                abs(np.mean([lm[i].x for i in RIGHT_IRIS]) - np.mean([lm[i].x for i in RIGHT_EYE]))
            )
            gaze_score = max(0.0, 1.0 - dev * 35)

            # Smile ratio (width vs height of mouth)
            width = abs(lm[MOUTH_RIGHT].x - lm[MOUTH_LEFT].x) * w
            height = abs(lm[MOUTH_BOTTOM].y - lm[MOUTH_TOP].y) * h
            smile_score = min(1.0, max(0.0, (width / (height + 1e-6) - 2.0) / 8.0))

            head_score = _head_pose_score(lm, w, h)
            attention_score = _vertical_attention(lm, h)

        except Exception as e:
            logger.error(f"[Video] MediaPipe error: {e}")

    # Emotion is optional, fallback to neutral-ish if unavailable
    emotion_result = _emotion_score(frame)
    emotion_score = emotion_result[0] if emotion_result else 0.5
    emotion_label = emotion_result[1] if emotion_result else "unknown"

    # Weighted fusion of all signals
    video_score = round(
        0.25 * eye_score +
        0.20 * gaze_score +
        0.15 * smile_score +
        0.15 * head_score +
        0.15 * emotion_score +
        0.10 * attention_score,
        3
    )

    # Strong penalty if user is clearly not looking at screen
    if gaze_score < 0.3:
        video_score *= 0.6

    video_score = max(0.0, min(1.0, video_score))

    print(
        f"[Video] eye={eye_score:.2f} gaze={gaze_score:.2f} "
        f"smile={smile_score:.2f} head={head_score:.2f} "
        f"attention={attention_score:.2f} emotion={emotion_label} "
        f"→ FINAL={video_score}",
        flush=True
    )

    return video_score
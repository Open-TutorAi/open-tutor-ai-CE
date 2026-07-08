"""Local speech-to-text using faster-whisper (CPU).
"""

import io
import os
import logging
import threading
from typing import Optional

logger = logging.getLogger("whisper_stt")

WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel

    WHISPER_AVAILABLE = True
except Exception:
    WhisperModel = None
    logger.debug("faster-whisper not available — local STT disabled")

_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")
_model = None
_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                logger.info(
                    "Loading faster-whisper model '%s' (cpu/int8)…", _MODEL_SIZE
                )
                _model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_bytes(data: Optional[bytes]) -> str:
    """Transcribe raw audio bytes to text.

    Returns an empty string when STT is unavailable or no audio was supplied.
    Safe to call from a thread pool (it is CPU-bound and blocking).
    """
    if not WHISPER_AVAILABLE or not data:
        return ""
    try:
        model = _get_model()
        segments, _info = model.transcribe(io.BytesIO(data), beam_size=1)
        return " ".join(seg.text.strip() for seg in segments).strip()
    except Exception as e:
        logger.warning("Local transcription failed: %s", e)
        return ""

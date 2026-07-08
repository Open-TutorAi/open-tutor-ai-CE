import base64
import logging
import io
from typing import Optional

logger = logging.getLogger("audio_engagement")

# Optional heavy deps — import lazily and tolerate absence so the rest of
# the app can run without audio libraries installed.
NUMPY_AVAILABLE = False
LIBROSA_AVAILABLE = False
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except Exception:
    np = None
    NUMPY_AVAILABLE = False

try:
    import librosa
    import soundfile as sf

    LIBROSA_AVAILABLE = True
    logger.debug("librosa and soundfile loaded successfully.")
except Exception:
    logger.debug("librosa or soundfile missing — audio scoring disabled.")

# Browsers (Chromium) record WebM/Opus by default, which libsndfile/soundfile
# cannot decode. PyAV (already pulled in by faster-whisper) decodes it via
# ffmpeg, so we use it as a fallback when soundfile fails.
AV_AVAILABLE = False
try:
    import av

    AV_AVAILABLE = True
except Exception:
    av = None


def _decode_audio(audio_bytes: bytes, sr: int):
    """Decode arbitrary audio bytes to a mono float32 array at ``sr`` Hz.

    Tries soundfile first (WAV/FLAC/OGG), then falls back to PyAV for formats
    libsndfile cannot read (notably WebM/Opus from browser MediaRecorder).
    """
    # Fast path: soundfile (handles WAV/FLAC/OGG-Vorbis).
    try:
        y, native_sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
        if y.ndim > 1:
            y = librosa.to_mono(y.T)
        if native_sr != sr:
            y = librosa.resample(y, orig_sr=native_sr, target_sr=sr)
        return y
    except Exception:
        pass  # likely WebM/Opus — try PyAV below

    if not AV_AVAILABLE:
        raise RuntimeError("soundfile failed and PyAV not available")

    container = av.open(io.BytesIO(audio_bytes))
    resampler = av.AudioResampler(format="flt", layout="mono", rate=sr)
    chunks = []
    for frame in container.decode(audio=0):
        for rframe in resampler.resample(frame):
            chunks.append(rframe.to_ndarray().reshape(-1))
    container.close()
    if not chunks:
        return np.array([], dtype="float32")
    return np.concatenate(chunks).astype("float32")


def compute_audio_score(audio_base64: str, sr: int = 16000) -> Optional[float]:
    # If required DSP libs are missing, gracefully skip audio scoring.
    if not (LIBROSA_AVAILABLE and NUMPY_AVAILABLE):
        logger.debug("[Audio] Skipping compute: librosa/numpy not available.")
        return None

    try:
        try:
            audio_bytes = base64.b64decode(audio_base64)
            y = _decode_audio(audio_bytes, sr)
        except Exception as e:
            logger.warning(f"[Audio] Decoding error: {e}")
            return None

        rms = librosa.feature.rms(y=y)[0]
        avg_rms = np.mean(rms)

        if len(y) < sr * 0.2 or avg_rms < 0.001:
            return None

        pitches, magnitudes = librosa.piptrack(
            y=y, sr=sr, n_fft=1024, hop_length=256, fmin=80.0, fmax=400.0
        )

        voiced_mask = magnitudes > np.median(magnitudes)
        voiced_pitches = pitches[voiced_mask]
        voiced_pitches = voiced_pitches[voiced_pitches > 0]

        if len(voiced_pitches) > 2:
            pitch_std = np.std(voiced_pitches)
            pitch_score = min(1.0, pitch_std / 60.0)
        else:
            pitch_score = 0.3

        energy_score = min(1.0, max(0.0, avg_rms / 0.04))

        db_rms = librosa.amplitude_to_db(rms, ref=np.max)
        silence_ratio = np.sum(db_rms < -25) / len(db_rms)
        silence_score = 1.0 - silence_ratio

        zcr = librosa.feature.zero_crossing_rate(y)[0]
        speech_rate_score = min(1.0, max(0.0, np.mean(zcr) * 6))

        audio_score = (
            0.35 * pitch_score
            + 0.20 * energy_score
            + 0.30 * silence_score
            + 0.15 * speech_rate_score
        )

        if silence_score < 0.3:
            audio_score *= 0.5

        final_score = max(0.0, min(1.0, round(audio_score, 3)))

        logger.debug(
            "audio score=%s (pitch=%.2f energy=%.2f cadence=%.2f zcr=%.2f)",
            final_score,
            pitch_score,
            energy_score,
            silence_score,
            speech_rate_score,
        )
        return final_score

    except Exception as e:
        logger.error(f"[Audio] Unexpected error: {e}")
        return None

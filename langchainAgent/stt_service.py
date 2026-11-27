import io
from faster_whisper import WhisperModel

# Model configuration: "base.en" is ~145MB, highly accurate and sub-second fast on CPU
MODEL_SIZE = "base.en"
_model_instance = None


def get_stt_model() -> WhisperModel:
    """Lazy-loads and caches the Faster-Whisper model in memory."""
    global _model_instance
    if _model_instance is None:
        print(f"⏳ Loading Faster-Whisper model ({MODEL_SIZE}) on CPU with INT8 quantization...")
        # INT8 compute_type reduces RAM by 50% and speeds up inference 4x on CPU
        _model_instance = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        print("✅ Faster-Whisper model loaded and ready!")
    return _model_instance


def transcribe_audio(audio_data: bytes | str) -> str:
    """
    Transcribes in-memory audio bytes or an audio file path into text.

    Args:
        audio_data: Raw audio bytes (WebM/Opus, WAV, MP3, etc.) or file path.

    Returns:
        Transcribed text string.
    """
    if not audio_data:
        return ""

    model = get_stt_model()

    if isinstance(audio_data, (bytes, bytearray)):
        audio_stream = io.BytesIO(audio_data)
        segments, _ = model.transcribe(audio_stream, beam_size=5)
        return " ".join(seg.text for seg in segments).strip()

    segments, _ = model.transcribe(audio_data, beam_size=5)
    return " ".join(seg.text for seg in segments).strip()

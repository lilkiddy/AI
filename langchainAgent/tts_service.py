import asyncio
import edge_tts

# Voice configuration: Microsoft Edge Neural Voice
# "en-US-GuyNeural" is a natural-sounding male voice.
# Other options: "en-US-AriaNeural" (female), "en-US-JennyNeural" (female)
VOICE = "en-US-GuyNeural"


async def synthesize_speech(text: str) -> bytes:
    """
    Converts text into spoken audio (MP3 bytes) using Microsoft Edge TTS.

    How it works:
        1. edge-tts connects to Microsoft's free Edge Read Aloud service over WebSocket.
        2. The service streams back MP3 audio chunks with natural neural voice prosody.
        3. We collect all chunks into a single bytes buffer and return it.

    Args:
        text: The text string to convert into speech.

    Returns:
        Raw MP3 audio bytes ready to be sent to the browser or saved to a file.
    """
    communicate = edge_tts.Communicate(text, VOICE)
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    return b"".join(audio_chunks)

import asyncio
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from stt_service import transcribe_audio
from tts_service import synthesize_speech
from agent import VoiceAgent, load_user_facts, sanitize_user_id

app = FastAPI(title="Voice Agent - End-to-End Gateway")

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend assets (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the LangChain Agent with persistent memory and lock shared state across worker threads
agent = VoiceAgent(user_id="praveen")
agent_lock = asyncio.Lock()


@app.get("/")
async def serve_ui():
    """Serves the web interface for microphone audio capture and voice playback."""
    return FileResponse("static/index.html")


@app.get("/session-info")
async def session_info_endpoint():
    """Returns the currently active user profile and loaded fact count."""
    async with agent_lock:
        facts = load_user_facts(agent.user_id)
        return JSONResponse(content={
            "user_id": agent.user_id,
            "facts_count": len(facts),
        })


@app.post("/select-user")
async def select_user_endpoint(body: dict):
    """
    Loads an existing user's memory JSON or creates a new one if absent.
    Saves any active unsaved turns before switching users.
    """
    raw_user = (body.get("user_id") or "").strip()
    if not raw_user:
        return JSONResponse(status_code=400, content={"error": "Username cannot be empty"})

    clean_id = sanitize_user_id(raw_user)

    async with agent_lock:
        if clean_id != agent.user_id and len(agent.messages) > 1:
            await asyncio.to_thread(agent.end_session)

        user_id, facts_count, is_new = await asyncio.to_thread(agent.switch_user, clean_id)

    return JSONResponse(content={
        "user_id": user_id,
        "facts_count": facts_count,
        "is_new_user": is_new,
    })


@app.post("/transcribe")
async def transcribe_and_respond(file: UploadFile = File(...)):
    """
    1. Transcribes incoming audio using Faster-Whisper.
    2. Passes recognized text to the LangChain Agent.
    3. Prints both to terminal and returns them to the UI.
    """
    audio_bytes = await file.read()

    # Step 1: Transcribe user audio off the event loop
    user_text = await asyncio.to_thread(transcribe_audio, audio_bytes)

    print("\n" + "=" * 55)
    print(f"🎙️ [USER VOICE DETECTED]: \"{user_text}\"")

    # Step 2: Query LangChain Agent off the event loop under agent_lock
    ai_reply = ""
    if user_text and user_text.strip():
        async with agent_lock:
            ai_reply = await asyncio.to_thread(agent.chat, user_text)
        print(f"🤖 [AI AGENT RESPONSE]:\n{ai_reply}")
    else:
        ai_reply = "I didn't catch that. Could you please repeat?"

    print("=" * 55 + "\n")

    return JSONResponse(content={
        "transcription": user_text,
        "ai_response": ai_reply
    })


@app.post("/end-session")
async def end_session_endpoint():
    """Analyzes recent conversation and persists long-term facts."""
    async with agent_lock:
        await asyncio.to_thread(agent.end_session)
        agent.reset_session()
    return JSONResponse(content={"status": "session_ended_and_memory_saved"})


@app.post("/synthesize")
async def synthesize_endpoint(body: dict):
    """
    Converts AI response text into spoken audio (MP3) using Edge-TTS.

    Receives: JSON body { "text": "Hello, I am Gojo..." }
    Returns:  Raw MP3 audio bytes with Content-Type: audio/mpeg
    """
    text = body.get("text", "")
    if not text.strip():
        return Response(content=b"", media_type="audio/mpeg")

    print(f"🔊 [TTS SYNTHESIZING]: {len(text)} characters")
    audio_bytes = await synthesize_speech(text)
    print(f"✅ [TTS COMPLETE]: {len(audio_bytes)} bytes of MP3 audio")

    return Response(content=audio_bytes, media_type="audio/mpeg")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

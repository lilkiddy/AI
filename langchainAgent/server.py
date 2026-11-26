from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from stt_service import transcribe_audio
from tts_service import synthesize_speech
from agent import VoiceAgent

app = FastAPI(title="Voice Agent - End-to-End Gateway")

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the LangChain Agent with persistent memory
agent = VoiceAgent(user_id="praveen")

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice AI Agent</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .card {
            background: #1e293b;
            border-radius: 20px;
            padding: 40px;
            max-width: 580px;
            width: 100%;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 1px solid #334155;
        }
        h1 { font-size: 1.8rem; margin-bottom: 8px; color: #38bdf8; }
        p.subtitle { font-size: 0.95rem; color: #94a3b8; margin-bottom: 30px; }
        .mic-btn {
            width: 110px;
            height: 110px;
            border-radius: 50%;
            background: #3b82f6;
            border: none;
            color: white;
            font-size: 38px;
            cursor: pointer;
            outline: none;
            transition: all 0.2s ease;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
            margin: 0 auto 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .mic-btn:hover { transform: scale(1.05); background: #2563eb; }
        .mic-btn.recording {
            background: #ef4444;
            animation: pulse 1.2s infinite;
            box-shadow: 0 0 25px rgba(239, 68, 68, 0.7);
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        .status {
            font-size: 0.95rem;
            color: #cbd5e1;
            margin-bottom: 25px;
            min-height: 24px;
            font-weight: 500;
        }
        .dialogue-box {
            display: flex;
            flex-direction: column;
            gap: 15px;
            text-align: left;
            margin-bottom: 25px;
        }
        .result-box {
            background: #0f172a;
            border-radius: 12px;
            padding: 16px 20px;
            border: 1px solid #334155;
        }
        .ai-box {
            background: #172554;
            border-color: #1e40af;
        }
        .result-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .ai-box .result-label {
            color: #60a5fa;
        }
        .result-text {
            font-size: 1rem;
            color: #f1f5f9;
            line-height: 1.5;
            word-break: break-word;
        }
        .btn-end {
            background: transparent;
            border: 1px solid #475569;
            color: #94a3b8;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }
        .btn-end:hover {
            background: #334155;
            color: #f8fafc;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Voice AI Agent</h1>
        <p class="subtitle">Microphone ➡️ Faster-Whisper ➡️ LangChain Agent ➡️ Edge-TTS</p>
        
        <button id="micBtn" class="mic-btn" onclick="toggleRecording()">🎙️</button>
        <div id="status" class="status">Click microphone to speak</div>

        <div class="dialogue-box">
            <div class="result-box">
                <div class="result-label">🗣️ You Said:</div>
                <div id="userText" class="result-text">Waiting for your voice...</div>
            </div>

            <div class="result-box ai-box">
                <div class="result-label">🤖 AI Agent Response:</div>
                <div id="aiText" class="result-text">AI is ready.</div>
            </div>
        </div>

        <button class="btn-end" onclick="endSession()">💾 End Session & Save Memory</button>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        let audioPlayer = new Audio();  // Reusable audio player for TTS playback

        const micBtn = document.getElementById("micBtn");
        const status = document.getElementById("status");
        const userText = document.getElementById("userText");
        const aiText = document.getElementById("aiText");

        async function toggleRecording() {
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = event => {
                        if (event.data.size > 0) audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        await sendAudioToServer(audioBlob);
                    };

                    mediaRecorder.start();
                    isRecording = true;
                    micBtn.classList.add("recording");
                    micBtn.innerText = "⏹️";
                    status.innerText = "Listening... Click to stop";
                } catch (err) {
                    alert("Microphone permission denied: " + err.message);
                }
            } else {
                mediaRecorder.stop();
                isRecording = false;
                micBtn.classList.remove("recording");
                micBtn.innerText = "🎙️";
                status.innerText = "Transcribing & Thinking...";
            }
        }

        async function sendAudioToServer(blob) {
            const formData = new FormData();
            formData.append("file", blob, "recording.wav");

            try {
                const response = await fetch("/transcribe", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) throw new Error("Server error " + response.status);

                const data = await response.json();
                userText.innerText = data.transcription || "(No speech detected)";
                aiText.innerText = data.ai_response || "(No response)";
                status.innerText = "🔊 Speaking response...";

                // Play AI response as audio via Edge-TTS
                if (data.ai_response) {
                    await playTTS(data.ai_response);
                }
                status.innerText = "Ready! Click microphone to reply.";
            } catch (error) {
                status.innerText = "Error processing voice request";
                aiText.innerText = "Failed: " + error.message;
            }
        }

        async function playTTS(text) {
            try {
                // Stop any currently playing audio
                audioPlayer.pause();
                audioPlayer.currentTime = 0;

                // Fetch MP3 audio from the /synthesize endpoint
                const response = await fetch("/synthesize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: text })
                });

                if (!response.ok) throw new Error("TTS error " + response.status);

                // Convert response to a playable audio blob
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);

                audioPlayer.src = audioUrl;
                await audioPlayer.play();

                // Wait for audio to finish playing before returning
                await new Promise(resolve => {
                    audioPlayer.onended = resolve;
                    audioPlayer.onerror = resolve;
                });

                // Clean up the blob URL to free memory
                URL.revokeObjectURL(audioUrl);
            } catch (err) {
                console.error("TTS playback failed:", err);
            }
        }

        async function endSession() {
            try {
                status.innerText = "Analyzing memory and saving profile...";
                const res = await fetch("/end-session", { method: "POST" });
                const data = await res.json();
                status.innerText = "Memory saved successfully! Session reset.";
                userText.innerText = "Waiting for your voice...";
                aiText.innerText = "AI is ready.";
            } catch (e) {
                status.innerText = "Could not save memory.";
            }
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the test interface for microphone audio capture."""
    return HTMLResponse(content=HTML_UI)


@app.post("/transcribe")
async def transcribe_and_respond(file: UploadFile = File(...)):
    """
    1. Transcribes incoming audio using Faster-Whisper.
    2. Passes recognized text to the LangChain Agent.
    3. Prints both to terminal and returns them to the UI.
    """
    audio_bytes = await file.read()

    # Step 1: Transcribe user audio
    user_text = transcribe_audio(audio_bytes)
    
    print("\n" + "=" * 55)
    print(f"🎙️ [USER VOICE DETECTED]: \"{user_text}\"")

    # Step 2: Query LangChain Agent if speech was detected
    ai_reply = ""
    if user_text and user_text.strip():
        ai_reply = agent.chat(user_text)
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
    agent.end_session()
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

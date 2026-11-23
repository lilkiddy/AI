from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from stt_service import transcribe_audio

app = FastAPI(title="Voice Agent - STT Testing Gateway")

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice AI Agent - Audio Test</title>
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
            max-width: 500px;
            width: 100%;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 1px solid #334155;
        }
        h1 { font-size: 1.8rem; margin-bottom: 8px; color: #38bdf8; }
        p.subtitle { font-size: 0.95rem; color: #94a3b8; margin-bottom: 30px; }
        .mic-btn {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: #3b82f6;
            border: none;
            color: white;
            font-size: 40px;
            cursor: pointer;
            outline: none;
            transition: all 0.2s ease;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
            margin: 0 auto 25px auto;
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
        .result-box {
            background: #0f172a;
            border-radius: 12px;
            padding: 20px;
            text-align: left;
            border: 1px solid #334155;
            min-height: 80px;
        }
        .result-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 6px;
        }
        .result-text {
            font-size: 1.05rem;
            color: #f1f5f9;
            line-height: 1.5;
            word-break: break-word;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Voice Input Gateway</h1>
        <p class="subtitle">Task 1: Microphone ➡️ .wav ➡️ Faster-Whisper</p>
        
        <button id="micBtn" class="mic-btn" onclick="toggleRecording()">🎙️</button>
        <div id="status" class="status">Click microphone to speak</div>

        <div class="result-box">
            <div class="result-label">Transcribed Speech:</div>
            <div id="resultText" class="result-text">Waiting for audio...</div>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        const micBtn = document.getElementById("micBtn");
        const status = document.getElementById("status");
        const resultText = document.getElementById("resultText");

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
                    alert("Microphone permission denied or not available: " + err.message);
                }
            } else {
                mediaRecorder.stop();
                isRecording = false;
                micBtn.classList.remove("recording");
                micBtn.innerText = "🎙️";
                status.innerText = "Transcribing with Faster-Whisper...";
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
                resultText.innerText = data.transcription || "(No speech detected)";
                status.innerText = "Ready. Click microphone to speak again.";
            } catch (error) {
                status.innerText = "Error transcribing audio";
                resultText.innerText = "Failed: " + error.message;
            }
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the test interface for recording microphone audio."""
    return HTMLResponse(content=HTML_UI)


@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """Receives recorded audio (.wav) from the browser, transcribes it, and prints it."""
    audio_bytes = await file.read()
    
    # Run Faster-Whisper transcription
    transcribed_text = transcribe_audio(audio_bytes)
    
    # Print to server terminal
    print("\n" + "=" * 50)
    print(f"🎙️ [USER VOICE DETECTED]: \"{transcribed_text}\"")
    print("=" * 50 + "\n")
    
    return JSONResponse(content={"transcription": transcribed_text})


if __name__ == "__main__":
    # Runs FastAPI server on port 8000
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

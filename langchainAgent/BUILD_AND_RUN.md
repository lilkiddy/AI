# Build and Run Guide

Complete, step-by-step instructions to set up, execute, and test both the **CLI Memory Agent** and the **Voice Input Web Gateway**.

---

## 📋 1. Prerequisites

Ensure the following tools are available on your system:
- **Python**: Version 3.12+ (Verify with `python3 --version`)
- **Docker** *(Optional for containerized run)*: Version 20.10+ (Verify with `docker --version`)
- **Web Browser**: Chrome, Edge, Firefox, or Safari (for microphone audio capture)

---

## ⚙️ 2. Environment Setup

### Step A: Clone or Navigate to Project
```bash
cd /home/prvn/ai/experiments/AI/langchainAgent
```

### Step B: Create & Activate Virtual Environment
```bash
# If .venv is already present:
source .venv/bin/activate

# Or create a fresh virtual environment:
python3 -m venv .venv
source .venv/bin/activate
```

### Step C: Configure API Keys (`.env`)
Create your `.env` file from the example template:
```bash
cp .env.example .env
```

Open `.env` and supply your Google Gemini API key:
```ini
GOOGLE_API_KEY=your_gemini_api_key_here
ENVIRONMENT=development
```

### Step D: Install Dependencies
```bash
pip install -r requirements.txt
```

> [!IMPORTANT]
> PyAV must be version `< 18` (e.g. `17.1.0`) to maintain compatibility with Faster-Whisper's audio container decoding. This is automatically enforced by [requirements.txt](requirements.txt).

---

## 🚀 3. Execution Modes

### Mode A: Run the Interactive CLI Agent (With Persistent Memory)

Runs the conversational agent in your terminal with the Two-Tier memory engine and real-time response streaming.

```bash
python main.py
```

* **Introduce yourself / persona:** e.g., *"I am Gojo, a developer by day and sorcerer by night."*
* **Ask anything:** Real-time tokens stream immediately via `llm.stream()`.
* **Exit:** Type `exit` or `quit`.
  - The agent analyzes today's chat, extracts new user facts, and updates `memory/praveen.json`.
  - When you restart `python main.py`, the agent instantly recalls your identity!

---

### Mode B: Run the Voice Input Gateway (Web UI + Faster-Whisper)

Starts the FastAPI server serving the browser-based voice recording interface and Faster-Whisper STT engine.

```bash
python server.py
```

1. Open your browser and navigate to:
   ```text
   http://localhost:8000
   ```
2. Click the **🎙️ microphone button** and grant microphone permissions when prompted.
3. Speak your prompt (e.g., *"Hello Gojo, what are we deploying today?"*).
4. Click the button again to stop.
5. **Expected Output:**
   - The audio (`.wav`) is sent to the `/transcribe` endpoint.
   - Faster-Whisper transcribes the audio on your CPU in ~400ms.
   - Your terminal prints:
     ```text
     ==================================================
     🎙️ [USER VOICE DETECTED]: "Hello Gojo, what are we deploying today?"
     ==================================================
     ```
   - The recognized speech text appears instantly on the web page.

---

## 🐳 4. Running with Docker

### Build the Image
```bash
docker build -t voice-agent:latest .
```

### Run the Container
```bash
docker run --rm -p 8000:8000 --env-file .env voice-agent:latest
```

* Open `http://localhost:8000` in your host browser.
* Browser handles host audio natively; container runs completely isolated.

---

## 🔍 5. Troubleshooting & FAQ

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `TypeError: open() got an unexpected keyword argument 'metadata_errors'` | PyAV v19+ incompatibility | Run `pip install "av<18"` |
| `Microphone permission denied` in browser | Browser security policy | Click the padlock icon in the browser URL bar and allow Microphone access for `localhost`. |
| `KeyError: 'GOOGLE_API_KEY'` | Missing `.env` | Ensure `.env` is created and contains a valid key. |
| Model download on first run is slow | First-time Hugging Face pull | Faster-Whisper downloads `base.en` (~145MB) once. Subsequent runs load instantly from local cache. |
| `GoogleModelNotFoundError: 404 NOT_FOUND` | Deprecated model name | Ensure `model="gemini-3.5-flash-lite"` is used in `main.py`. |

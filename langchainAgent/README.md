# Voice AI Agent

A containerized, end-to-end **Voice AI Agent** powered by **FastAPI**, **Faster-Whisper (STT)**, **LangChain + Gemini**, and a **Two-Tier Persistent Memory** engine.

---

## 📌 Project Overview

Speak directly into your browser microphone and converse with an AI agent that remembers your identity, preferences, and context across sessions—running identically on your local machine or inside Docker.

```text
Browser Mic (.wav) ──▶ FastAPI Gateway (server.py)
                              │
                              ├──▶ Faster-Whisper STT (stt_service.py)
                              └──▶ LangChain + Gemini Agent (agent.py)
                                         │
                                         └──▶ Persistent Memory (memory/praveen.json)
                              ◀──
                              └──▶ Edge-TTS (tts_service.py) ──▶ MP3 Audio ──▶ Browser Speaker
```

### Key Highlights
- **Browser-Native Voice Input**: Uses Web Audio (`MediaRecorder`) in the browser—portable across Linux, macOS, Windows, and Docker without host audio passthrough.
- **CPU-Optimized Speech-to-Text**: Runs `faster-whisper` (`base.en`, INT8 via CTranslate2) locally on CPU with sub-second transcription.
- **Two-Tier Memory Engine**: Combines an ephemeral in-RAM sliding window (`MAX_SHORT_TERM_TURNS = 20`) with deterministic JSON fact extraction and auto-compaction on disk (`memory/<user_id>.json`).
- **Production-Hardened Docker**: Pre-caches the Whisper model at build time, runs as non-root `appuser` (UID 1000), and excludes secrets (`.env`) via `.dockerignore`.

---

## 📂 Project Structure

```text
langchainAgent/
├── docs/                                # Architecture & technical references
│   ├── ARCHITECTURE.md                  # High-level architecture & system evolution
│   ├── CODE_FLOW_AND_API.md             # Chronological code flow & function API guide
│   ├── FRONTEND_AND_COMMUNICATION.md    # Beginner-friendly guide to UI & Web Audio HTTP flow
│   ├── MEMORY_ARCHITECTURE.md           # Deep dive on Two-Tier memory & compaction
│   └── voice_agent_flow.png             # Visual system workflow diagram
├── memory/
│   └── praveen.json                     # Persistent user facts & persona storage (JSON)
├── .dockerignore                        # Prevents venv, cache, and secrets from entering image
├── .env.example                         # Template for API keys and configuration
├── agent.py                             # LangChain VoiceAgent core, CLI mode & Two-Tier memory
├── BUILD_AND_RUN.md                     # Complete instructions for Web, CLI, and Docker
├── docker-compose.yml                   # Container orchestration configuration
├── Dockerfile                           # Multi-platform Linux container definition
├── README.md                            # Project overview & documentation
├── requirements.txt                     # Python package dependencies
├── server.py                            # FastAPI voice gateway & browser Web Audio UI
├── stt_service.py                       # Faster-Whisper CTranslate2 STT service wrapper
└── tts_service.py                       # Edge-TTS text-to-speech service wrapper
```

---

## 🐳 Docker Architecture & Setup

| Component | Specification | Purpose |
| :--- | :--- | :--- |
| **Base Image** | `python:3.12-slim` | Minimal attack surface, small image footprint |
| **System Packages** | `curl`, `ca-certificates`, `ffmpeg` | Core networking and audio/speech decoding |
| **Process User** | `appuser` (UID 1000) | Enforces least-privilege non-root execution |
| **Output Buffering** | `PYTHONUNBUFFERED=1` | Real-time log streaming for container runtimes |
| **Pre-Cached STT** | `faster-whisper` `base.en` (INT8) | Downloaded during `docker build` for instant startup |

---

## 🚀 Quick Start

### 1. Configure Environment Variables
Copy the template and supply your Gemini API key:
```bash
cp .env.example .env
```

### 2. Run with Docker Compose (Recommended)
```bash
docker compose up --build
```
Then open `http://localhost:8000` in your browser.

### 3. Run Locally (without Docker)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```
Then open `http://localhost:8000` in your browser. *(To run text-only CLI mode instead, run `python agent.py`.)*

---

## 📖 Documentation Reference

All architectural references, execution flows, and deep-dive technical guides are organized in [`docs/`](docs/):

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: End-to-end design, system evolution (Phases 1–3), and architectural decisions with rationale.
- **[CODE_FLOW_AND_API.md](docs/CODE_FLOW_AND_API.md)**: Function-by-function execution sequence, phase lifecycle, and REST API contract.
- **[FRONTEND_AND_COMMUNICATION.md](docs/FRONTEND_AND_COMMUNICATION.md)**: Beginner-friendly, zero-jargon explanation of how the UI records voice and talks to Python.
- **[MEMORY_ARCHITECTURE.md](docs/MEMORY_ARCHITECTURE.md)**: Deep dive into the Two-Tier memory system, deterministic delta updates, and auto-compaction.
- **[BUILD_AND_RUN.md](BUILD_AND_RUN.md)**: Complete guide to running the Voice Web Server, CLI Agent, and Docker deployment.

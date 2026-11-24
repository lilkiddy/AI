# WisprXscaler AI Agent

WisprXscaler is a containerized Python-based AI agent environment engineered to run seamlessly across any host machine without dependency conflicts or environmental drift.

---

## 📌 Project Overview

This project provides a robust foundation for building, testing, and deploying full-fledged AI agents. It encapsulates all dependencies, runtime environments, and system-level packages (like audio/voice processors and networking tools) using Docker.

### Key Highlights
- **Universal Portability**: Runs identically on local development environments, cloud servers (AWS, GCP, DigitalOcean), or hybrid environments.
- **Dependency Isolation**: Uses Docker containerization and Python virtual environments to prevent host dependency clashes.
- **Production Hardened**: Pre-configured non-root user, real-time unbuffered logging, and layer-cached Docker builds.
- **Secret Protection**: `.env` and sensitive files are excluded from image builds via `.dockerignore`.

---

## 📂 Project Structure

```text
langchainAgent/
├── docs/                                          # Architecture & technical references
│   ├── architecture.md                            # High-level architecture & system evolution
│   ├── CODE_FLOW_AND_API.md                       # Chronological code flow & function API guide
│   ├── FRONTEND_AND_COMMUNICATION.md              # Zero-jargon guide to UI & Web Audio communication
│   ├── MEMORY_ARCHITECTURE.md                     # Deep dive on Two-Tier memory & compaction
│   └── voice agent flow from browser to agent and vice versa.png # Visual system workflow diagram
├── memory/
│   └── praveen.json                               # Persistent user facts & persona storage (JSON)
├── .dockerignore                                   # Prevents venv, cache, and secrets from entering image
├── .env.example                                    # Template for API keys and configuration
├── BUILD_AND_RUN.md                                # Complete instructions for CLI, Web, and Docker
├── docker-compose.yml                              # Container orchestration configuration
├── Dockerfile                                      # Multi-platform Linux container definition
├── main.py                                         # LangChain agent core with Two-Tier memory engine
├── README.md                                       # Project overview & documentation
├── requirements.txt                                # Python package dependencies
├── server.py                                       # FastAPI voice gateway & browser Web Audio UI
└── stt_service.py                                  # Faster-Whisper CTranslate2 STT service wrapper
```

---

## 🐳 Docker Architecture & Setup

The project uses a streamlined multi-stage container build process:

| Component | Specification | Purpose |
| :--- | :--- | :--- |
| **Base Image** | `python:3.12-slim` | Minimal attack surface, small image footprint (~150MB base) |
| **System Packages** | `curl`, `ca-certificates`, `ffmpeg` | Core networking and audio/speech capability |
| **Process User** | `appuser` (UID 1000) | Enforces least-privilege non-root execution |
| **Output Buffering** | `PYTHONUNBUFFERED=1` | Real-time log streaming for container runtimes |
| **Cache Optimization** | Layered `pip install` | Fast subsequent builds when only code changes |

---

## 🚀 Quick Start

### 1. Configure Environment Variables
Copy the template and supply your model API keys:
```bash
cp .env.example .env
```

### 2. Run with Docker Compose
```bash
docker compose up --build
```

### 3. Run Locally (without Docker)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 📖 Documentation Reference

All architectural references, execution flows, and deep-dive technical guides are organized in the [`docs/`](docs/) directory:

- **[CODE_FLOW_AND_API.md](docs/CODE_FLOW_AND_API.md)**: Function-by-function execution sequence, phase lifecycle, and REST API contract.
- **[architecture.md](docs/architecture.md)**: End-to-end design, system evolution (Phases 1–3), and interview talking points.
- **[FRONTEND_AND_COMMUNICATION.md](docs/FRONTEND_AND_COMMUNICATION.md)**: Beginner-friendly, zero-jargon explanation of how the UI records voice and talks to Python.
- **[MEMORY_ARCHITECTURE.md](docs/MEMORY_ARCHITECTURE.md)**: Deep dive into the Two-Tier memory system, deterministic delta updates, and auto-compaction.
- **[BUILD_AND_RUN.md](BUILD_AND_RUN.md)**: Complete guide to running the CLI Agent, the Voice Web Server, and Docker deployment.


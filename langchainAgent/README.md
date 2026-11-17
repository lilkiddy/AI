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
wisprXscaler/
├── .dockerignore          # Prevents venv, cache, and secrets from entering image
├── .env.example           # Template for API keys and configuration
├── BUILD_AND_RUN.md       # Step-by-step instructions for building & executing
├── docker-compose.yml     # Orchestration config for containerized execution
├── Dockerfile             # Multi-platform container specification
├── main.py                # Main application & agent entry point
├── README.md              # Project overview & documentation
└── requirements.txt       # Python package dependencies
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

## 📖 Detailed Instructions

For detailed build commands, CLI execution, interactive sessions, troubleshooting, and production deployment instructions, refer to **[BUILD_AND_RUN.md](BUILD_AND_RUN.md)**.


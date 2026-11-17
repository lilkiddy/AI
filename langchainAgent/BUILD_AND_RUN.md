# Build and Run Guide

This document provides complete, step-by-step instructions to build, run, and deploy the WisprXscaler application across any environment.

---

## 📋 Prerequisites

Before proceeding, ensure you have the following installed on your machine:
- **Docker**: Engine version 20.10+ (Check with `docker --version`)
- **Docker Compose**: Plugin v2+ (Check with `docker compose version`)
- *(Optional for local dev)* **Python**: 3.12+ (Check with `python3 --version`)

---

## ⚙️ Initial Configuration

Create your local `.env` configuration file from the template:

```bash
cd wisprXscaler
cp .env.example .env
```

Open `.env` in an editor and insert your relevant API keys (e.g. OpenAI, Anthropic, Gemini, OpenRouter):
```ini
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
ENVIRONMENT=development
```

> [!IMPORTANT]
> The `.env` file is excluded in `.dockerignore` so your secrets are never baked into container images.

---

## 🐳 Method 1: Run with Docker Compose (Recommended)

Docker Compose simplifies build and run lifecycle management.

### Build and Start
```bash
docker compose up --build
```

### Run Interactively (for Agents with Terminal Prompt / Chat CLI)
If your agent expects command-line user interaction:
```bash
docker compose run --rm agent
```

### Run in the Background (Detached Mode)
```bash
docker compose up -d
```

### View Live Logs
```bash
docker compose logs -f
```

### Stop Containers
```bash
docker compose down
```

---

## 🛠️ Method 2: Run with Standard Docker CLI

### 1. Build the Docker Image
```bash
docker build -t wispr-agent:latest .
```

### 2. Run the Container

**Non-Interactive / Single Execution:**
```bash
docker run --rm --env-file .env wispr-agent:latest
```

**Interactive Mode (Terminal input / chat interface):**
```bash
docker run --rm -it --env-file .env wispr-agent:latest
```

**Background (Daemon) Mode:**
```bash
docker run -d --name wispr_ai_agent --env-file .env --restart unless-stopped wispr-agent:latest
```

**Inspect Container Logs:**
```bash
docker logs -f wispr_ai_agent
```

**Stop the Running Container:**
```bash
docker stop wispr_ai_agent && docker rm wispr_ai_agent
```

---

## 🐍 Method 3: Run Locally with Python Virtual Environment

If you prefer testing directly on your host machine without Docker:

### 1. Activate or Create Virtual Environment
```bash
# If .venv already exists:
source .venv/bin/activate

# Or create a fresh environment:
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python main.py
```

---

## 🔄 Adding New Packages to your Agent

When you install new libraries during development:

1. Add the package name and version to `requirements.txt`:
   ```text
   langchain>=0.2.0
   pydantic>=2.0.0
   ```
2. Rebuild the Docker image:
   ```bash
   docker compose build
   # or
   docker build -t wispr-agent:latest .
   ```

---

## 🚀 Deploying to Any Remote Machine

Because the application is packaged in a self-contained Docker image, you can deploy it to any server without installing Python or dependencies on the target host:

1. **Tag and Push Image to Docker Hub / Registry:**
   ```bash
   docker tag wispr-agent:latest your-username/wispr-agent:latest
   docker push your-username/wispr-agent:latest
   ```

2. **Run on Target Server:**
   ```bash
   # Ensure .env is present on the target server
   docker run -d \
     --name wispr-agent \
     --restart always \
     --env-file .env \
     your-username/wispr-agent:latest
   ```

---

## 🔍 Troubleshooting & Debugging

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| `KeyError: 'OPENAI_API_KEY'` | Missing `.env` | Ensure `.env` exists and pass `--env-file .env` |
| Image build uses old code | Docker caching | Run `docker build --no-cache -t wispr-agent .` |
| Output does not show in console | Output buffering | Confirmed by `PYTHONUNBUFFERED=1` in Dockerfile |
| Permission denied inside container | Non-root `appuser` | Container runs under UID 1000. Avoid writing to root-owned paths |

### Open an Interactive Shell inside Container for Debugging:
```bash
docker run --rm -it --entrypoint /bin/bash wispr-agent:latest
```


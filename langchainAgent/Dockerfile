# 1. Base Image - Official lightweight Python 3.12 image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr (vital for real-time logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 2. Install essential system dependencies (ffmpeg is required for audio decoding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 3. Create a non-root user for security best practices
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# 4. Copy dependency specifications first (leverages Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# 5. Pre-download Faster-Whisper model into image (ensures instant startup with zero runtime download lag)
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base.en', device='cpu', compute_type='int8')"

# 6. Copy the rest of the application code
COPY . .

# Set file and home directory ownership to non-root user
RUN chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Expose web gateway port
EXPOSE 8000

# 7. Default execution command (starts the FastAPI Voice Gateway)
CMD ["python", "server.py"]

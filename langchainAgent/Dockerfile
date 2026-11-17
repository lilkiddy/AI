# 1. Base Image - Official lightweight Python 3.12 image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr (vital for real-time logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 2. Install essential system dependencies (common for AI & audio/speech agent tools)
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

# 5. Copy the rest of the application code
COPY . .

# Set file ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# 6. Default execution command
CMD ["python", "main.py"]


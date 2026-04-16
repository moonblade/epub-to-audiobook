# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    EPUBTOAUDIO_UPLOAD_PATH=/data/input \
    EPUBTOAUDIO_OUTPUT_PATH=/data/output

# Install system dependencies
# - gcc: for compiling Python extensions
# - ffmpeg: for pydub audio processing
# - libsndfile1: for soundfile library
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model
RUN python -m spacy download en_core_web_sm

# Create directories for data, models, and logs
RUN mkdir -p /data/input /data/output /app/models /app/jobs /app/voice_mappings \
    && chmod -R 755 /data /app/models /app/jobs /app/voice_mappings

# Download TTS models (~500MB total)
RUN curl -L -o /app/models/kokoro-v1.0.onnx \
    https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx \
    && curl -L -o /app/models/voices-v1.0.bin \
    https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin

# Copy application code
COPY config.py .
COPY converter.py .
COPY job_manager.py .
COPY log_store.py .
COPY logger.py .
COPY main.py .
COPY models.py .
COPY preprocessor.py .
COPY voice_mapping_store.py .
COPY templates/ templates/
COPY static/ static/

# Expose the port the app runs on
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3002/voices || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3002"]

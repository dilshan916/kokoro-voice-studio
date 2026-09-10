FROM python:3.11-slim

# Set up non-root user with UID 1000 required by Hugging Face Spaces
RUN useradd -m -u 1000 user

WORKDIR /app

# Install system audio dependencies (espeak-ng for phonemizer & ffmpeg for audio rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn fastapi soundfile numpy kokoro-onnx pydub

# Copy app files and grant permissions to user
COPY --chown=user:user . .

# Ensure data directory exists with write permissions for SQLite billing database
RUN mkdir -p /app/data /app/output /app/assets/kokoro && chown -R user:user /app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860 \
    HOST=0.0.0.0

EXPOSE 7860

CMD ["python", "server.py"]

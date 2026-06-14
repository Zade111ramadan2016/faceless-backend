# Cloud Run – FacelessShorts Backend
FROM python:3.11-slim

# Install system dependencies (ffmpeg needed by moviepy/imageio-ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Cloud Run requires listening on $PORT (default 8080)
ENV PORT=8080
EXPOSE 8080

# Use multiple workers; Cloud Run sets concurrency separately
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1"]

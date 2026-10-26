# Dockerfile for DAR — Fake Job Detector
# Following docs/03_TECHNICAL_DESIGN.md section 11

FROM python:3.11-slim

# Install Tesseract OCR (English only) and clean apt cache
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Non-root user setup
RUN useradd --create-home daruser \
    && mkdir -p /app/instance \
    && chown -R daruser:daruser /app

# Install Python dependencies first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .
RUN chown -R daruser:daruser /app

# Run as non-root user
USER daruser

# Default port
ENV PORT=5000

# Start gunicorn bound to PORT environment variable with 1 worker, 2 threads, timeout 120
CMD gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120

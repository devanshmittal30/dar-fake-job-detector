# Dockerfile for DAR — Fake Job Detector
# To be completed in P17.

FROM python:3.11-slim

# Install Tesseract OCR (English only)
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Run as non-root user
RUN useradd --create-home daruser
USER daruser

# Start gunicorn
CMD gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120

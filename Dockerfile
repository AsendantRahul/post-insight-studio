FROM python:3.11-slim

# Install system dependencies required for OCR and PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt ./backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy the complete project
COPY . .

# Flask backend
WORKDIR /app/backend

# Render provides the PORT environment variable
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} run:app"]
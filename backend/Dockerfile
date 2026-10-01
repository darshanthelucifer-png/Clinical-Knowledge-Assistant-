# ==============================================================================
# ClinSaarthi AI - Production Backend Dockerfile
# Optimized for Django 5 + Uvicorn ASGI Server & Streaming SSE Support
# ==============================================================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

WORKDIR /app

# Install system dependencies for OCR, PyMuPDF, and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script and set executable permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy application source code
COPY . /app/

# Create non-root user and persistent storage directories with proper ownership
RUN useradd -m -u 1000 appuser && \
    mkdir -p /data/chroma_db /data/media /app/staticfiles && \
    chown -R appuser:appuser /app /data

USER appuser

# Expose backend port
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

# Default command runs Uvicorn ASGI server with workers
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

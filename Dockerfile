# ==============================================================================
# Legal Metrology Compliance System - Dockerfile
# Production-grade container with PaddleOCR, Tesseract, OpenCV, and Gunicorn
# ==============================================================================

FROM python:3.11-slim-bookworm

# Set Python and runtime environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DEBIAN_FRONTEND=noninteractive \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

# Install system dependencies required by OpenCV, PaddlePaddle, and Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download and cache PaddleOCR PP-OCRv4 models into image
# This avoids runtime latency and enables offline container deployments
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='en', ocr_version='PP-OCRv4')"

# Copy application source code
COPY . .

# Ensure storage directories exist and entrypoint is executable
RUN mkdir -p uploads/crops reports instance && \
    chmod +x entrypoint.sh

# Expose web application port
EXPOSE 5000

# Health check to monitor web service availability
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/login || exit 1

# Entrypoint automatically initializes database if needed
ENTRYPOINT ["./entrypoint.sh"]

# Default server is Gunicorn with 2 workers, 4 threads, and 180s request timeout for deep learning OCR
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "180", "app:app"]

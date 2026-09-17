FROM python:3.11-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=5

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libpq-dev \
    gcc \
    g++ \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel/setuptools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install CPU-only PyTorch first (much smaller download, prevents timeout)
RUN pip install --no-cache-dir --timeout 300 --retries 5 \
    torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .

# Install remaining dependencies with generous timeout and retry policy
RUN pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

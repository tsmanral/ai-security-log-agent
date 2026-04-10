# AI-Sentinel V3 — Multi-stage Docker build
FROM python:3.12-slim AS base

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data /app/data/models /app/logs

# Expose ports (API + Dashboard)
EXPOSE 8000 8501

# Default: run the API server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

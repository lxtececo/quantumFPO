# Multi-stage build for Python FastAPI application
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies and create user in single layer
RUN apt-get update && apt-get install -y \
    curl \
    g++ \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --disabled-password --gecos '' python

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY backend/src/main/python/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/src/main/python/ ./

# Change ownership to python user
RUN chown -R python:python /app

# Switch to non-root user
USER python

# Expose port 8002
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["uvicorn", "portfolio_api:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
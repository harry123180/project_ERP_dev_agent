# Multi-stage Docker build for Flask backend with PostgreSQL support
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production
ARG REQUIREMENTS_FILE=requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir psycopg2-binary gunicorn

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=0

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/instance && \
    chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

# Create health check script
COPY --chown=appuser:appuser <<EOF /app/health_check.py
#!/usr/bin/env python3
import requests
import sys
import os

def health_check():
    try:
        host = os.getenv('HOST', '0.0.0.0')
        port = os.getenv('PORT', '5000')
        url = f"http://{host}:{port}/api/v1/health"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Health check passed")
            return True
        else:
            print(f"Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Health check failed with error: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)
EOF

RUN chmod +x /app/health_check.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/health_check.py || exit 1

# Default command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
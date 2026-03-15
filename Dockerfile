# Multi-stage build for Horizon Web UI
# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Stage 2: Backend with frontend bundled
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy application source first (required for editable install)
COPY src/ ./src/
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[webui,mqtt]" && \
    rm -rf /root/.cache/pip

# Copy config directory
COPY config/ ./config/

# Copy frontend build from previous stage
# The vite build outputs to ../src/webui/static/dist relative to frontend dir
COPY --from=frontend-builder /src/webui/static/dist ./src/webui/static/dist

# Create necessary directories
RUN mkdir -p data/processed data/raw data/external config

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m -u 1000 horizon && \
    chown -R horizon:horizon /app

USER horizon

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application with log level from environment
CMD ["sh", "-c", "python3 -m uvicorn src.webui.main:app --host 0.0.0.0 --port 8000 --log-level $(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]')"]

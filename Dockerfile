###############################################
# Multi-stage build for smaller, secure image #
###############################################

# ===== Stage 1: Builder =====
FROM python:3.11-slim AS builder

ENV VENV_PATH=/opt/venv

WORKDIR /app

# System deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into a virtual environment
COPY requirements.txt ./requirements.txt
RUN python -m venv ${VENV_PATH} \
    && ${VENV_PATH}/bin/pip install --upgrade pip \
    && ${VENV_PATH}/bin/pip install --no-cache-dir -r requirements.txt

# ===== Stage 2: Runtime =====
FROM python:3.11-slim AS runtime

ENV VENV_PATH=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy prebuilt virtualenv from builder
COPY --from=builder ${VENV_PATH} ${VENV_PATH}

# Create non-root user
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /app \
    && chown -R app:app /app

# Only copy what we need
COPY src/ ./src/
    # Do not bake secrets into the image; rely on environment variables at runtime
    # If a local .env exists during development, python-dotenv will load it automatically
    # COPY .env .env  <-- intentionally disabled to avoid CI failures and secret leakage

# Use non-root user
USER app

# Expose API port
EXPOSE 8000

# Healthcheck: ping /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Default command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

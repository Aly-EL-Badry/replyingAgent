# ── Stage 1: Builder ──────────────────────────────────────────
# Using a specific python version to match the runtime
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime AS builder

# System deps needed for building/compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────
# CRITICAL: Version must match the builder's Python (3.11)
FROM python:3.11-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UVICORN_WORKERS=1

# Copy application code
COPY main.py           ./main.py
COPY app/              ./app/
COPY config/           ./config/

# FastAPI default port
EXPOSE 8000

# Health-check (Using absolute path to be safe)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
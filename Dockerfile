# Start with your PyTorch base
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --no-cache-dir pipenv

WORKDIR /app

# Copy Pipenv files
COPY Pipfile Pipfile.lock ./

# THE FIX: Add --ignore-pipfile to bypass the 3.13 vs 3.11 check
RUN pipenv install --system --deploy --ignore-pipfile

# Copy application code
COPY . .

# Railway uses $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
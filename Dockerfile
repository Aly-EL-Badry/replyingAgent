# Start with your PyTorch base
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

# Install system deps for Postgres and Pipenv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --no-cache-dir pipenv

WORKDIR /app

# Copy Pipenv files first (for better caching)
COPY Pipfile Pipfile.lock ./

# Install dependencies system-wide inside the container
# --system tells Pipenv not to create a second virtual environment
# --deploy ensures the build fails if Pipfile.lock is out of sync
RUN pipenv install --system --deploy

# Copy your application code
COPY . .

# Railway uses $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
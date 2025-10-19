# Base image
FROM python:3.11-slim AS builder

WORKDIR /app

# Avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies for psycopg2 and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock* requirements.txt ./

# Install dependencies [prefer poetry if available, fall back to pip]
RUN if [ -f "poetry.lock" ]; then \
        echo "Using poetry for dependencies"; \
        pip install --no-cache-dir poetry && \
        poetry config virtualenvs.create false && \
        poetry install --no-interaction --no-ansi --no-root --only main; \
    elif [ -f "requirements.txt" ]; then \
        echo "Using requirements.txt for dependencies"; \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "No dependency file found! Exiting." && exit 1; \
    fi

# Copy app source
COPY . .

# Runtime image
FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

EXPOSE 8000

# Run FastAPI using uvicorn
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
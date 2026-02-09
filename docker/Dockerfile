# syntax=docker/dockerfile:1

############################
# Builder stage
############################
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps (Postgres client libs + build tools for any wheels that need compiling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (better layer caching)
COPY pyproject.toml README.md LICENSE ./

# Create a virtualenv inside the image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade tooling + install your project with prod extras
RUN pip install --upgrade pip setuptools wheel \
  && pip install ".[prod]"

############################
# Runtime stage
############################
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime deps only (no compiler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
  && rm -rf /var/lib/apt/lists/*

# Add non-root user
RUN useradd -m -u 10001 appuser

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src ./src
COPY migrations ./migrations
COPY wsgi.py ./wsgi.py
COPY docker/gunicorn.conf.py ./gunicorn.conf.py

# If you use instance/ at runtime, keep it (otherwise omit)
COPY instance ./instance

# Common Flask/Gunicorn env
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

USER appuser

# Start gunicorn. If you have docker/gunicorn.conf.py, you can use it:
# CMD ["gunicorn", "-c", "docker/gunicorn.conf.py", "wsgi:app"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]


HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

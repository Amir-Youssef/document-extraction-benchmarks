# Single-stage development image — simplicity over size.
FROM python:3.12-slim

WORKDIR /app

# System dependencies (gcc for C extensions, curl for manual debugging)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency metadata and install all deps (including dev).
# Source code is mounted via volume at runtime — NOT copied here.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

# Copy source so the package can be installed.
# In practice docker-compose will override /app/src with a volume mount,
# but this ensures the image is functional standalone.
COPY src/ ./src/
RUN uv sync --frozen

# Ensure the virtualenv binaries are first in PATH
ENV PATH="/app/.venv/bin:$PATH"

# FastAPI / Uvicorn default port
EXPOSE 8000

# Healthcheck using curl (available in dev image for debugging)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8000/health"]

# Development command — hot reload enabled
CMD ["fastapi", "dev", "src/backend/main.py", "--host", "0.0.0.0", "--port", "8000"]

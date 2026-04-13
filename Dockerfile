# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# System dependencies required for compiling C extensions (cryptography, etc.)
# Installed only in this stage — will NOT exist in the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency metadata and README (required by hatchling build).
# Source code changes will NOT invalidate this layer.
COPY pyproject.toml uv.lock README.md ./

# Install dependencies in a dedicated virtual environment.
# --frozen ensures uv.lock is the single source of truth.
# --no-install-project skips installing the project itself (done after source copy).
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source code
COPY src/ ./src/

# Now install the project package itself (uses cached deps from above)
RUN uv sync --frozen --no-dev


# ---- Runtime stage ----
FROM python:3.12-slim

WORKDIR /app

# Copy the virtual environment with all installed packages from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY --from=builder /app/src /app/src

# Ensure the virtualenv binaries are first in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --no-log-init --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# FastAPI / Uvicorn default port
EXPOSE 8000

# Healthcheck using Python stdlib — avoids adding curl to the image
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)"]

# Production command — no reload, single worker by default.
# Scale workers via: --workers N (based on available CPUs).
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

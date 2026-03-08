# ============================================================================
# Project AEGIS - Digital Twin Emergency Vehicle System
# Multi-stage Dockerfile for optimized production deployment
# ============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies with uv
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files and README for hatchling
COPY pyproject.toml uv.lock README.md ./

# Install dependencies to a virtual environment
RUN uv sync --no-dev

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 aegis && \
    mkdir -p /app /app/logs /app/data && \
    chown -R aegis:aegis /app

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=aegis:aegis /app/.venv /app/.venv

# Copy application code
COPY --chown=aegis:aegis src/ ./src/
COPY --chown=aegis:aegis data/ ./data/
COPY --chown=aegis:aegis main.py ./
COPY --chown=aegis:aegis pyproject.toml ./

# Set Python path to use venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Switch to non-root user
USER aegis

EXPOSE 8501

# Health check (can be overridden per service)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command (override in docker-compose)
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

# -----------------------------------------------------------------------------
# Stage 3: Development - Includes dev dependencies and tools
# -----------------------------------------------------------------------------
FROM runtime AS development

USER root

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy full dependency spec and README for hatchling
COPY pyproject.toml uv.lock README.md ./

# Install dev dependencies
RUN uv sync

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Switch back to aegis user
USER aegis

# Development default command
CMD ["bash"]

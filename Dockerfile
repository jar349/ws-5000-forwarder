# Multi-stage Dockerfile for production and testing
# Use Python version from .python-version file
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY uv.lock ./
COPY app.py ./
COPY README.md ./
COPY gunicorn.conf.py ./

# Production stage
FROM base AS production

# Install only production dependencies
RUN uv sync

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create and set permissions for UV cache directory
RUN mkdir -p /tmp/uv-cache && chown -R appuser:appuser /tmp/uv-cache

# Change ownership of the app directory to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uv", "run", "gunicorn", "-c", "gunicorn.conf.py", "app:app"]

# Testing stage
FROM base AS testing

# Set additional environment for testing
ENV PYTHONPATH=/app

# Install dependencies including test dependencies
RUN uv sync --group dev

# Create test results directory
RUN mkdir -p /app/test-results

# Copy tests (could be done at runtime via volume mount instead)
COPY tests/ ./tests/

# Create a non-root user for tests (optional - can run as root in test containers)
RUN groupadd -r testuser && useradd -r -g testuser testuser

# Create and set permissions for UV cache and test results
RUN mkdir -p /tmp/uv-cache /app/test-results && \
    chown -R testuser:testuser /tmp/uv-cache /app/test-results /app

# Default user for testing (can be overridden)
USER testuser

# Default command for testing (can be overridden)
CMD ["uv", "run", "pytest", "-v"]

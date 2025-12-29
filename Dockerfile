# Stage 1: Builder stage
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONPATH=/app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Use --no-cache-dir to prevent pip cache, clean up after install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt && \
    find /root/.local -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && \
    find /root/.local -name "*.pyc" -delete && \
    find /root/.local -name "*.pyo" -delete

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# Install runtime system dependencies only (no build tools)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage (no build tools)
COPY --from=builder /root/.local /root/.local

# Copy application code only (exclude dev files)
COPY api/ ./api/
COPY core/ ./core/
COPY ingestion/ ./ingestion/
COPY services/ ./services/
COPY schemas/ ./schemas/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY run_etl.py ./
COPY data/ ./data/

# Expose API port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


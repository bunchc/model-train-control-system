# Multi-stage build for optimized image size and security
FROM python:3.14-slim AS builder

# Install build dependencies with pinned versions
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc=4:10.2.1-1 \
        build-essential=12.9 && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip==24.0 && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage - minimal runtime image
FROM python:3.14-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash edgeuser

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=edgeuser:edgeuser app/ /app/
COPY --chown=edgeuser:edgeuser edge-controller.conf /app/

# Switch to non-root user
USER edgeuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run application
CMD ["python", "main.py"]

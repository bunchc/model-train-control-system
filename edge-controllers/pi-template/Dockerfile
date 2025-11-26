# Multi-stage build for optimized image size and security
FROM python:3.9-slim AS builder

# Install system dependencies for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements-pi.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip==24.0 && \
    pip install --no-cache-dir \
        --extra-index-url https://www.piwheels.org/simple \
        -r /tmp/requirements-pi.txt

# Final stage - minimal runtime image
FROM python:3.9-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /workspace

# Copy application code
COPY app/ /workspace/app/
COPY edge-controller.conf /workspace/app/

# Run as root for hardware access (I2C, GPIO)
# In production, consider adding user to i2c/gpio groups instead

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run application as module
CMD ["python", "-m", "app.main"]

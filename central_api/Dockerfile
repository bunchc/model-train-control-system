# Multi-stage build for optimized production image

# --- Stage 1: Build SQLite with modern version ---
FROM debian:bullseye-slim AS sqlite-builder

ENV SQLITE_VERSION=3510000
WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN wget https://www.sqlite.org/2025/sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    tar xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    cd sqlite-autoconf-${SQLITE_VERSION} && \
    ./configure --prefix=/sqlite && \
    make && \
    make install

# --- Stage 2: Python dependencies ---
FROM python:3.11-slim AS python-builder

WORKDIR /build

# Install dependencies in user space for easy copy
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 3: Final runtime image ---
FROM python:3.11-slim

# Copy SQLite from builder
COPY --from=sqlite-builder /sqlite /usr/local

# Copy Python packages from builder
COPY --from=python-builder /root/.local /root/.local

# Set environment for SQLite
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV PATH=/usr/local/bin:/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash apiuser

# Set working directory and copy application
WORKDIR /app
COPY --chown=apiuser:apiuser app /app

# Switch to non-root user
USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/ping', timeout=2).raise_for_status()"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

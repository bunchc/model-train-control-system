
# --- Stage 1: Build SQLite ---
FROM debian:bullseye as sqlite-builder

ENV SQLITE_VERSION=3510000
WORKDIR /build

RUN apt-get update && \
	apt-get install -y wget build-essential

RUN wget https://www.sqlite.org/2025/sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
	tar xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
	cd sqlite-autoconf-${SQLITE_VERSION} && \
	./configure --prefix=/sqlite && \
	make && make install

# --- Stage 2: Final Python image ---
FROM python:3.9-slim

# Copy SQLite binaries and libraries from builder
COPY --from=sqlite-builder /sqlite /usr/local

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app

# Set environment variables to ensure Python uses the new SQLite
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV PATH=/usr/local/bin:$PATH

# Expose the API port
EXPOSE 8000

# Set PYTHONPATH so app package is found
ENV PYTHONPATH=/app
# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Multi-stage build for Mining OS

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Build backend
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY src/mining_os/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY src/mining_os/ ./src/mining_os/

# Copy built frontend
COPY --from=frontend-builder /app/dist ./src/mining_os/static

# Stage 3: Final image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from builder
COPY --from=backend-builder /app/src/mining_os/ ./src/mining_os/

# Install Python dependencies
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Create non-root user
RUN useradd --create-home --shell /bin/bash miner
USER miner

# Expose ports
EXPOSE 31415

# Health check
HEALTHCHECK CMD curl -f http://localhost:31415/health || exit 1

# Set default environment variables
ENV PAYOUT_ADDR=""
ENV WORKER_NAME="rig01"
ENV MINIMUM_PAYOUT_THRESHOLD="0.005"
ENV SSL_CERTFILE=""
ENV SSL_KEYFILE=""

# Entry point script to check for required environment variables
COPY <<'EOF' /app/entrypoint.sh
#!/bin/bash
if [ -z "$PAYOUT_ADDR" ]; then
  echo "Error: PAYOUT_ADDR environment variable is required"
  echo "Please run with: docker run -e PAYOUT_ADDR=your_wallet_address -p 31415:31415 mining-os"
  exit 64
fi

# Check if SSL is configured
if [ -n "$SSL_CERTFILE" ] && [ -n "$SSL_KEYFILE" ]; then
  echo "SSL configured with cert: $SSL_CERTFILE and key: $SSL_KEYFILE"
  # Verify files exist
  if [ ! -f "$SSL_CERTFILE" ]; then
    echo "Error: SSL certificate file not found: $SSL_CERTFILE"
    exit 65
  fi
  if [ ! -f "$SSL_KEYFILE" ]; then
    echo "Error: SSL key file not found: $SSL_KEYFILE"
    exit 65
  fi
fi

exec python -m src.mining_os "$@"
EOF

RUN chmod +x /app/entrypoint.sh

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]
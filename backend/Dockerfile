FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (static binary - architecture-aware)
# Note: We only need the Docker client to manage MCP containers, not the daemon
# The daemon runs on the host and is accessed via /var/run/docker.sock
# Detect architecture and download appropriate Docker CLI
RUN ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "amd64" ]; then \
        DOCKER_ARCH="x86_64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        DOCKER_ARCH="aarch64"; \
    else \
        echo "Unsupported architecture: $ARCH"; exit 1; \
    fi \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${DOCKER_ARCH}/docker-24.0.7.tgz" -o /tmp/docker.tgz \
    && tar -xz -C /tmp -f /tmp/docker.tgz \
    && mv /tmp/docker/docker /usr/local/bin/docker \
    && chmod +x /usr/local/bin/docker \
    && rm -rf /tmp/docker /tmp/docker.tgz \
    && docker --version

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install MCP sandbox SDK (local package)
COPY python-mcp-sandbox-openai-sdk-main /tmp/mcp-sandbox-sdk
RUN cd /tmp/mcp-sandbox-sdk && pip install --no-cache-dir -e . && rm -rf /tmp/mcp-sandbox-sdk

# Copy backend code
COPY backend/ .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]


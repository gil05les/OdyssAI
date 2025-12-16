FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (curl for health/debug; build-essential for any optional native deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml uv.lock ./ 
RUN pip install --no-cache-dir uv && \
    uv pip install --no-cache-dir .

# App code
COPY src ./src
COPY example ./example

# Default command runs the Amadeus example runner; override as needed.
CMD ["python", "-m", "example.amadeus_runner"]









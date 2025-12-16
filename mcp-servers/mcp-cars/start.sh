#!/bin/bash
# Startup script for mcp-cars
# Installs dependencies and starts the server

set -e

# Install dependencies if requirements.txt exists
if [ -f /sandbox/requirements.txt ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --break-system-packages -q -r /sandbox/requirements.txt
fi

# Start the server
exec python3 /sandbox/server.py


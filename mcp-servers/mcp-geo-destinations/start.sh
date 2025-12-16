#!/bin/bash
# Startup script for mcp-geo-destinations
# Installs additional dependencies and starts the server

set -e

# Install dependencies if requirements.txt exists and not already installed
if [ -f /sandbox/requirements.txt ]; then
    # Check if amadeus is already installed (main dependency)
    if ! python3 -c "import amadeus" 2>/dev/null; then
        echo "Installing dependencies from requirements.txt..."
    pip install --break-system-packages -q -r /sandbox/requirements.txt
    else
        echo "Dependencies already installed, skipping..."
    fi
fi

# Start the server
exec python3 /sandbox/server.py


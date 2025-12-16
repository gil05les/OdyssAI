#!/bin/bash
# Script to rebuild backend container with logging support

set -e

echo "🔄 Rebuilding Backend Container with Logging Support"
echo "=================================================="
echo ""

# Step 1: Stop and remove backend
echo "📦 Step 1: Stopping and removing backend container..."
docker stop odyssai-backend 2>/dev/null || true
docker rm odyssai-backend 2>/dev/null || true
echo "✅ Backend container removed"
echo ""

# Step 2: Rebuild backend image
echo "🔨 Step 2: Rebuilding backend image..."
docker build -f backend/Dockerfile -t odyssai-backend:latest .
echo "✅ Backend image rebuilt"
echo ""

# Step 3: Start backend with new volume mounts
echo "🚀 Step 3: Starting backend container with logging volume..."
cd "$(dirname "$0")"
if [ -f ".env" ]; then
    set -a
    . .env
    set +a
fi

docker run -d \
    --name odyssai-backend \
    -p 8000:8000 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(pwd)/backend:/app" \
    -v "$(pwd)/mcp-servers:/mcp-servers" \
    -v "$(pwd)/python-mcp-sandbox-openai-sdk-main:/python-mcp-sandbox-openai-sdk-main" \
    -v "$(pwd)/logs:/app/logs" \
    -e "HOST_PROJECT_ROOT=$(pwd)" \
    -e "MCP_AUTO_CONSENT=true" \
    -e "AMADEUS_CLIENT_ID=${AMADEUS_CLIENT_ID:-${AMADEUS_API_KEY}}" \
    -e "AMADEUS_CLIENT_SECRET=${AMADEUS_CLIENT_SECRET:-${AMADEUS_API_SECRET}}" \
    -e "AMADEUS_API_KEY=${AMADEUS_API_KEY}" \
    -e "AMADEUS_API_SECRET=${AMADEUS_API_SECRET}" \
    -e "AMADEUS_HOSTNAME=${AMADEUS_HOSTNAME:-${AMADEUS_ENV}}" \
    -e "AMADEUS_ENV=${AMADEUS_ENV}" \
    -e "OPENAI_API_KEY=${OPENAI_API_KEY}" \
    -e "UNSPLASH_ACCESS_KEY=${UNSPLASH_ACCESS_KEY}" \
    -e "DEFAULT_MODEL=${DEFAULT_MODEL:-gpt-4o}" \
    odyssai-backend:latest

echo "✅ Backend container started"
echo ""

# Step 4: Verify logs directory
echo "📋 Step 4: Verifying logs directory..."
sleep 2
if docker exec odyssai-backend ls -la /app/logs/ >/dev/null 2>&1; then
    echo "✅ Logs directory accessible in container"
    docker exec odyssai-backend ls -la /app/logs/ | head -5
else
    echo "⚠️  Logs directory will be created on first log write"
fi
echo ""

# Step 5: Show log access commands
echo "📖 Step 5: Log access commands:"
echo "  make logs-agents    # View agent logs"
echo "  make logs-mcp       # View MCP logs"
echo "  make logs-api       # View API logs"
echo "  make logs-all       # View all logs"
echo ""

echo "🎉 Rebuild complete! Backend is running with logging support."
echo "   API: http://localhost:8000"
echo ""




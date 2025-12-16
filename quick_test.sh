#!/bin/bash
# Quick test script for MCP Flights Server

echo "=========================================="
echo "MCP Flights Server - Quick Test"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "mcp-servers/mcp-flights" ]; then
    echo "❌ Error: Please run this script from the OdyssAI directory"
    exit 1
fi

# Check environment variables
echo "Checking environment variables..."
if [ -z "$AMADEUS_CLIENT_ID" ] || [ -z "$AMADEUS_CLIENT_SECRET" ]; then
    echo "⚠️  Warning: AMADEUS_CLIENT_ID and/or AMADEUS_CLIENT_SECRET not set"
    echo ""
    echo "Please set them first:"
    echo "  export AMADEUS_CLIENT_ID='your_id'"
    echo "  export AMADEUS_CLIENT_SECRET='your_secret'"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Environment variables set"
fi

# Check Python
echo ""
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi
echo "✅ Python found: $(python3 --version)"

# Check dependencies
echo ""
echo "Checking dependencies..."
cd mcp-servers/mcp-flights
if ! python3 -c "import amadeus" 2>/dev/null; then
    echo "⚠️  Warning: amadeus package not installed"
    echo "Installing dependencies..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
fi
echo "✅ Dependencies installed"

# Run tests
echo ""
echo "=========================================="
echo "Running Tool Tests"
echo "=========================================="
echo ""
python3 test_tools.py

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If tests passed, try the MCP server test:"
echo "   cd mcp-servers/mcp-flights && python3 test_mcp_server.py"
echo ""
echo "2. Or test with the full agent:"
echo "   cd backend && python3 main.py"
echo ""


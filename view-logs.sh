#!/bin/bash
# Quick script to view OdyssAI logs

LOG_DIR="logs"
CONTAINER_NAME="odyssai-backend"
MCP_FLIGHTS="odyssai-mcp-flights"
MCP_HOTELS="odyssai-mcp-hotels"
MCP_CARS="odyssai-mcp-cars"
MCP_GEO="odyssai-mcp-geo"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "OdyssAI Log Viewer"
    echo ""
    echo "Usage: ./view-logs.sh [OPTION]"
    echo ""
    echo "Backend Logs:"
    echo "  app          View application log (default)"
    echo "  agents       View agent execution log (full input/output)"
    echo "  mcp          View MCP server communication log (backend perspective)"
    echo "  api          View API request/response log"
    echo "  errors       View error log only"
    echo "  all          View all backend logs simultaneously"
    echo ""
    echo "MCP Container Logs:"
    echo "  mcp-flights  View flights MCP server container logs"
    echo "  mcp-hotels   View hotels MCP server container logs"
    echo "  mcp-cars     View cars MCP server container logs"
    echo "  mcp-geo      View geo destinations MCP server container logs"
    echo "  mcp-all      View all MCP container logs"
    echo ""
    echo "Other:"
    echo "  docker       View Docker backend container console output"
    echo "  search TEXT  Search for TEXT in all logs"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./view-logs.sh agents        # View agent logs with full I/O"
    echo "  ./view-logs.sh mcp-flights   # View flights MCP server logs"
    echo "  ./view-logs.sh search ERROR  # Search for errors"
    echo "  ./view-logs.sh all           # View all backend logs"
}

view_log() {
    local log_file=$1
    local description=$2
    
    if [ ! -f "$LOG_DIR/$log_file" ]; then
        echo -e "${YELLOW}Warning: $log_file doesn't exist yet${NC}"
        echo "Waiting for logs to be created..."
        tail -f "$LOG_DIR/$log_file" 2>/dev/null || echo "Log file will appear when the backend starts"
        return
    fi
    
    echo -e "${GREEN}Viewing: $description${NC}"
    echo -e "${BLUE}File: $LOG_DIR/$log_file${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    tail -f "$LOG_DIR/$log_file"
}

view_docker_logs() {
    echo -e "${GREEN}Viewing Docker container console output${NC}"
    echo -e "${BLUE}Container: $CONTAINER_NAME${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    docker logs -f "$CONTAINER_NAME"
}

search_logs() {
    local search_term=$1
    echo -e "${GREEN}Searching for: $search_term${NC}"
    echo ""
    grep -r "$search_term" "$LOG_DIR"/*.log --color=always -n
}

view_all_logs() {
    echo -e "${GREEN}Viewing all backend logs simultaneously${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    tail -f "$LOG_DIR"/*.log
}

view_mcp_container_logs() {
    local container_name=$1
    local description=$2
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${YELLOW}Warning: Container ${container_name} is not running${NC}"
        echo "Start it with: make docker-start-flights (or hotels/cars/geo)"
        return
    fi
    
    echo -e "${GREEN}Viewing: ${description}${NC}"
    echo -e "${BLUE}Container: ${container_name}${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    docker logs -f "$container_name"
}

view_all_mcp_logs() {
    echo -e "${GREEN}Viewing all MCP container logs${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    echo -e "${BLUE}Note: This will show logs from all MCP containers${NC}"
    echo ""
    docker logs -f "$MCP_FLIGHTS" 2>/dev/null &
    docker logs -f "$MCP_HOTELS" 2>/dev/null &
    docker logs -f "$MCP_CARS" 2>/dev/null &
    docker logs -f "$MCP_GEO" 2>/dev/null &
    wait
}

# Main script
case "${1:-app}" in
    app)
        view_log "app.log" "Application Log"
        ;;
    agents)
        view_log "agents.log" "Agent Execution Log"
        ;;
    mcp)
        view_log "mcp.log" "MCP Server Communication Log"
        ;;
    api)
        view_log "api.log" "API Request/Response Log"
        ;;
    errors)
        view_log "errors.log" "Error Log"
        ;;
    docker)
        view_docker_logs
        ;;
    search)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please provide a search term${NC}"
            echo "Example: ./view-logs.sh search FlightAgent"
            exit 1
        fi
        search_logs "$2"
        ;;
    all)
        view_all_logs
        ;;
    mcp-flights)
        view_mcp_container_logs "$MCP_FLIGHTS" "Flights MCP Server Logs"
        ;;
    mcp-hotels)
        view_mcp_container_logs "$MCP_HOTELS" "Hotels MCP Server Logs"
        ;;
    mcp-cars)
        view_mcp_container_logs "$MCP_CARS" "Cars MCP Server Logs"
        ;;
    mcp-geo)
        view_mcp_container_logs "$MCP_GEO" "Geo Destinations MCP Server Logs"
        ;;
    mcp-all)
        view_all_mcp_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac


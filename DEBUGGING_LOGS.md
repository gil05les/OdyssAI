# Complete Guide to Accessing Logs for Debugging

## Overview

OdyssAI has comprehensive logging for debugging. Since everything runs in Docker, here's how to access all logs including MCP tool inputs/outputs and agent execution.

## Log Structure

### Backend Logs (in `logs/` directory)
- **`logs/agents.log`** - Full agent input/output, state transitions, LLM interactions
- **`logs/mcp.log`** - MCP tool requests/responses from backend perspective
- **`logs/api.log`** - API request/response logs
- **`logs/app.log`** - General application logs
- **`logs/errors.log`** - Error-only logs

### MCP Server Logs (in separate Docker containers)
- **`odyssai-mcp-flights`** - Flights MCP server logs
- **`odyssai-mcp-hotels`** - Hotels MCP server logs
- **`odyssai-mcp-cars`** - Cars MCP server logs
- **`odyssai-mcp-geo`** - Geo destinations MCP server logs

## Quick Access Methods

### Method 1: View Agent Logs (Full Input/Output)

```bash
# View agent execution logs with full input/output
tail -f logs/agents.log

# Search for specific agent
grep "FlightAgent" logs/agents.log | tail -50

# View last 100 lines
tail -100 logs/agents.log
```

### Method 2: View MCP Tool Logs

#### Backend MCP Logs (tool requests/responses)
```bash
# View MCP communication from backend
tail -f logs/mcp.log

# Search for specific tool
grep "search_flights" logs/mcp.log -A 20
```

#### MCP Server Container Logs (internal MCP server logs)
```bash
# View flights MCP server logs
docker logs -f odyssai-mcp-flights

# View hotels MCP server logs
docker logs -f odyssai-mcp-hotels

# View cars MCP server logs
docker logs -f odyssai-mcp-cars

# View geo destinations MCP server logs
docker logs -f odyssai-mcp-geo
```

### Method 3: View All Logs Together

```bash
# View all backend logs simultaneously
tail -f logs/*.log

# View all MCP container logs
docker logs -f odyssai-mcp-flights &
docker logs -f odyssai-mcp-hotels &
docker logs -f odyssai-mcp-cars &
docker logs -f odyssai-mcp-geo &
```

## Detailed Debugging Workflow

### Step 1: Find the Request

```bash
# Search for a specific flight search in agent logs
grep -A 50 "FlightAgent.execute" logs/agents.log | tail -100

# Or search by timestamp
grep "2025-12-12 15:30" logs/agents.log
```

### Step 2: Trace Agent Execution

```bash
# View full agent input
grep -A 30 "AGENT INPUT.*FlightAgent" logs/agents.log

# View agent output
grep -A 30 "AGENT OUTPUT.*FlightAgent" logs/agents.log

# View state transitions
grep "STATE.*FlightAgent" logs/agents.log
```

### Step 3: Trace MCP Tool Calls

```bash
# View MCP tool request
grep -A 30 "MCP REQUEST.*search_flights" logs/mcp.log

# View MCP tool response
grep -A 30 "MCP RESPONSE.*search_flights" logs/mcp.log

# View MCP server internal logs
docker logs odyssai-mcp-flights | grep "search_flights" -A 20
```

### Step 4: Check API Layer

```bash
# View API request
grep -A 20 "API REQUEST.*POST /api/flights" logs/api.log

# View API response
grep -A 20 "API RESPONSE.*POST /api/flights" logs/api.log
```

## Complete Debugging Script

Create a script to view all relevant logs for a specific operation:

```bash
#!/bin/bash
# debug-flight-search.sh - View all logs for flight search debugging

echo "=== Agent Logs (Input/Output) ==="
grep -A 50 "FlightAgent.execute" logs/agents.log | tail -100
echo ""

echo "=== MCP Tool Logs (Backend) ==="
grep -A 30 "MCP.*search_flights" logs/mcp.log | tail -50
echo ""

echo "=== MCP Server Logs (Container) ==="
docker logs odyssai-mcp-flights 2>&1 | tail -50
echo ""

echo "=== API Logs ==="
grep -A 20 "POST /api/flights" logs/api.log | tail -50
```

## Understanding Log Format

### Agent Log Format
```
2025-12-12 15:30:45 | DEBUG | agents.flight | execute | 113 | ================================================================================
2025-12-12 15:30:45 | DEBUG | agents.flight | execute | 114 | 📥 AGENT INPUT: FlightAgent.execute
2025-12-12 15:30:45 | DEBUG | agents.flight | execute | 192 | Input Data:
{
  "origin": "ZRH",
  "destination": "LIS",
  "departure_date": "2026-01-11",
  ...
}
```

### MCP Log Format
```
2025-12-12 15:30:46 | DEBUG | mcp.flights | search_flights | 250 | ================================================================================
2025-12-12 15:30:46 | DEBUG | mcp.flights | search_flights | 251 | 📡 MCP REQUEST: flights.search_flights
2025-12-12 15:30:46 | DEBUG | mcp.flights | search_flights | 254 | Request:
{
  "origin": "ZRH",
  "destination": "LIS",
  ...
}
```

### MCP Server Container Log Format
```
[2025-12-12 15:30:46.123] [INFO] [search_flights] [REQ:search_1234567890] Searching flights: ZRH -> LIS on 2026-01-11 for 1 adult(s)
```

## Useful Commands

### Search Across All Logs
```bash
# Search for a specific term in all logs
grep -r "search_flights" logs/ --color=always

# Search with context
grep -r -A 10 -B 5 "ERROR" logs/ --color=always
```

### Filter by Time
```bash
# View logs from last 10 minutes
grep "$(date -d '10 minutes ago' '+%Y-%m-%d %H:%M')" logs/agents.log

# View logs from specific time range
grep "2025-12-12 15:3" logs/agents.log
```

### View Log File Sizes
```bash
# Check log file sizes
ls -lh logs/

# Check MCP container log sizes
docker exec odyssai-mcp-flights sh -c "du -sh /tmp/*.log 2>/dev/null || echo 'No log files in container'"
```

### Clear Logs (Start Fresh)
```bash
# Clear all backend logs
rm -f logs/*.log

# Clear MCP container logs (restart container)
docker restart odyssai-mcp-flights
```

## Real-Time Monitoring

### Monitor All Components
```bash
# Terminal 1: Agent logs
tail -f logs/agents.log

# Terminal 2: MCP backend logs
tail -f logs/mcp.log

# Terminal 3: MCP server container logs
docker logs -f odyssai-mcp-flights

# Terminal 4: API logs
tail -f logs/api.log
```

### Using `multitail` (if installed)
```bash
# Install multitail
brew install multitail  # macOS
# or
sudo apt-get install multitail  # Linux

# View all logs with colors
multitail logs/agents.log logs/mcp.log logs/api.log
```

## Docker Container Access

### Get Shell in Backend Container
```bash
docker exec -it odyssai-backend /bin/bash

# Inside container:
cd /app/logs
ls -lah
tail -f agents.log
```

### Get Shell in MCP Container
```bash
docker exec -it odyssai-mcp-flights /bin/bash

# Inside container:
# MCP servers log to stderr, check Docker logs instead
# Or check for any log files:
find /sandbox -name "*.log" 2>/dev/null
```

## Troubleshooting

### Logs Not Appearing?

1. **Check containers are running:**
   ```bash
   docker ps | grep odyssai
   ```

2. **Check log directory exists:**
   ```bash
   ls -la logs/
   ```

3. **Check volume mount:**
   ```bash
   docker inspect odyssai-backend | grep -A 5 "Mounts"
   ```

4. **Check permissions:**
   ```bash
   docker exec odyssai-backend ls -la /app/logs/
   ```

### Too Much Output?

1. **Filter by log level:**
   ```bash
   grep "ERROR\|WARNING" logs/agents.log
   ```

2. **Use less/more:**
   ```bash
   tail -100 logs/agents.log | less
   ```

3. **Search for specific patterns:**
   ```bash
   grep "FlightAgent.*execute" logs/agents.log | tail -50
   ```

## Quick Reference

```bash
# Most common: View agent logs with full I/O
tail -f logs/agents.log

# View MCP tool calls
tail -f logs/mcp.log

# View MCP server internal logs
docker logs -f odyssai-mcp-flights

# Search for specific operation
grep -A 50 "FlightAgent.execute" logs/agents.log

# View all logs together
tail -f logs/*.log
```

## Example: Debugging a Flight Search

```bash
# 1. Find the request in agent logs
grep -B 5 -A 100 "FlightAgent.execute" logs/agents.log | tail -150

# 2. Check MCP tool call
grep -A 30 "MCP REQUEST.*search_flights" logs/mcp.log | tail -50

# 3. Check MCP server response
grep -A 30 "MCP RESPONSE.*search_flights" logs/mcp.log | tail -50

# 4. Check MCP container logs
docker logs odyssai-mcp-flights 2>&1 | grep "search_flights" -A 20

# 5. Check API response
grep -A 30 "API RESPONSE.*POST /api/flights" logs/api.log | tail -50
```




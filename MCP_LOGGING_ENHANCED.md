# MCP Server Comprehensive Logging

## Overview

The MCP servers now have **comprehensive logging** enabled that captures:
- ✅ **Full tool inputs** (all parameters)
- ✅ **Full tool outputs** (complete return values)
- ✅ **Full API requests** (endpoint, method, all parameters)
- ✅ **Full API responses** (complete response data)

## Log File Locations

MCP server logs are written to files in the `logs/` directory:

- **`logs/mcp_flights.log`** - Flights MCP server logs
- **`logs/mcp_hotels.log`** - Hotels MCP server logs  
- **`logs/mcp_cars.log`** - Cars MCP server logs
- **`logs/mcp_geo_destinations.log`** - Geo destinations MCP server logs

Logs are also available via Docker logs:
```bash
docker logs -f odyssai-mcp-flights
```

## What Gets Logged

### 1. Tool Inputs (Full Parameters)

Every tool call logs:
```
================================================================================
=== MCP TOOL CALL: search_flights ===
================================================================================
Tool Name: search_flights
Request ID: search_1234567890
Full Tool Input: {
  "origin": "ZRH",
  "destination": "LIS",
  "departure_date": "2026-01-11",
  "return_date": "2026-01-18",
  "adults": 4,
  "max_price": 1000
}
================================================================================
```

### 2. API Requests (Full Details)

Every Amadeus API call logs:
```
=== AMADEUS API REQUEST ===
Endpoint: GET /v2/shopping/flight-offers
Full Request Parameters: {
  "originLocationCode": "ZRH",
  "destinationLocationCode": "LIS",
  "departureDate": "2026-01-11",
  "returnDate": "2026-01-18",
  "adults": 4
}
```

### 3. API Responses (Full Data)

Every API response logs:
```
=== AMADEUS API RESPONSE ===
Response: 10 flight offers returned
Full API Response Data: {
  "data": [
    {
      "id": "OFFER_123",
      "price": {
        "total": "420.00",
        "currency": "CHF"
      },
      "itineraries": [...],
      ...
    },
    ...
  ]
}
```

### 4. Tool Outputs (Full Return Values)

Every tool completion logs:
```
================================================================================
=== MCP TOOL OUTPUT: search_flights ===
================================================================================
Tool Name: search_flights
Request ID: search_1234567890
Status: SUCCESS
Full Tool Output: {
  "flight_options": [
    {
      "id": "OFFER_123",
      "price": 420.0,
      "currency": "CHF",
      "flight_number": "KL1005",
      "return_flight_number": "KL1006",
      ...
    },
    ...
  ],
  "search_params": {...},
  "source": "api"
}
================================================================================
```

## Accessing Logs

### Method 1: View Log Files Directly

```bash
# View flights MCP logs
tail -f logs/mcp_flights.log

# View all MCP logs
tail -f logs/mcp_*.log

# Search for specific tool calls
grep "search_flights" logs/mcp_flights.log -A 50

# Search for API calls
grep "AMADEUS API" logs/mcp_flights.log -A 30
```

### Method 2: Docker Logs

```bash
# View flights MCP container logs
docker logs -f odyssai-mcp-flights

# View with timestamps
docker logs -t odyssai-mcp-flights

# View last 100 lines
docker logs --tail 100 odyssai-mcp-flights
```

### Method 3: Enhanced Log Viewer Script

```bash
# View MCP flights logs
./view-logs.sh mcp-flights

# View all MCP logs
./view-logs.sh mcp-all
```

## Log Format

Each log entry follows this format:
```
[TIMESTAMP] [LEVEL] [TOOL_NAME] [REQ:REQUEST_ID] MESSAGE
```

Example:
```
[2025-12-12 15:30:46.123] [INFO] [search_flights] [REQ:search_1234567890] === TOOL: search_flights ===
[2025-12-12 15:30:46.124] [INFO] [search_flights] [REQ:search_1234567890] Full Input Parameters:
[2025-12-12 15:30:46.125] [INFO] [search_flights] [REQ:search_1234567890]   origin: ZRH
[2025-12-12 15:30:46.126] [INFO] [search_flights] [REQ:search_1234567890]   destination: LIS
```

## Log Levels

- **INFO**: Important events (tool calls, API calls, tool outputs)
- **DEBUG**: Detailed information (full JSON dumps, intermediate steps)
- **WARNING**: Warnings (rate limits, network issues)
- **ERROR**: Errors (API failures, exceptions)

## Log Rotation

Log files automatically rotate when they reach 10MB, keeping the last 5 backups:
- `mcp_flights.log`
- `mcp_flights.log.1`
- `mcp_flights.log.2`
- etc.

## Example: Complete Tool Call Trace

Here's what you'll see for a complete tool call:

```
[2025-12-12 15:30:46.123] [INFO] [SERVER] [REQ:search_123] ================================================================================
[2025-12-12 15:30:46.124] [INFO] [SERVER] [REQ:search_123] === MCP TOOL CALL: search_flights ===
[2025-12-12 15:30:46.125] [INFO] [SERVER] [REQ:search_123] ================================================================================
[2025-12-12 15:30:46.126] [INFO] [SERVER] [REQ:search_123] Tool Name: search_flights
[2025-12-12 15:30:46.127] [INFO] [SERVER] [REQ:search_123] Request ID: search_123
[2025-12-12 15:30:46.128] [INFO] [SERVER] [REQ:search_123] Full Tool Input: {"origin": "ZRH", ...}
[2025-12-12 15:30:46.129] [INFO] [search_flights] [REQ:search_123] === TOOL: search_flights ===
[2025-12-12 15:30:46.130] [INFO] [search_flights] [REQ:search_123] Full Input Parameters: ...
[2025-12-12 15:30:46.131] [INFO] [search_flights] [REQ:search_123] === AMADEUS API REQUEST ===
[2025-12-12 15:30:46.132] [INFO] [search_flights] [REQ:search_123] Endpoint: GET /v2/shopping/flight-offers
[2025-12-12 15:30:46.133] [INFO] [search_flights] [REQ:search_123] Full Request Parameters: {...}
[2025-12-12 15:30:47.234] [INFO] [search_flights] [REQ:search_123] API call completed in 1.101s
[2025-12-12 15:30:47.235] [INFO] [search_flights] [REQ:search_123] === AMADEUS API RESPONSE ===
[2025-12-12 15:30:47.236] [INFO] [search_flights] [REQ:search_123] Response: 10 flight offers returned
[2025-12-12 15:30:47.237] [DEBUG] [search_flights] [REQ:search_123] Full API Response Data: {...}
[2025-12-12 15:30:47.500] [INFO] [search_flights] [REQ:search_123] === TOOL OUTPUT: search_flights ===
[2025-12-12 15:30:47.501] [INFO] [search_flights] [REQ:search_123] Output Summary: 10 flight options found
[2025-12-12 15:30:47.502] [INFO] [search_flights] [REQ:search_123] Full Tool Output: {...}
[2025-12-12 15:30:47.503] [INFO] [SERVER] [REQ:search_123] === MCP TOOL OUTPUT: search_flights ===
[2025-12-12 15:30:47.504] [INFO] [SERVER] [REQ:search_123] Status: SUCCESS
[2025-12-12 15:30:47.505] [INFO] [SERVER] [REQ:search_123] Full Tool Output: {...}
```

## Troubleshooting

### Logs Not Appearing?

1. **Check if log file exists:**
   ```bash
   ls -la logs/mcp_flights.log
   ```

2. **Check container is running:**
   ```bash
   docker ps | grep odyssai-mcp-flights
   ```

3. **Check Docker logs:**
   ```bash
   docker logs odyssai-mcp-flights 2>&1 | tail -50
   ```

### Too Much Output?

The logs are comprehensive by design. To reduce verbosity:
- Use `grep` to filter specific tool calls
- Focus on ERROR/WARNING levels
- Use log rotation (automatic at 10MB)

### Need to Clear Logs?

```bash
# Clear MCP log files
rm -f logs/mcp_*.log

# Restart containers to start fresh
docker restart odyssai-mcp-flights
```

## Summary

✅ **Full tool inputs** - All parameters logged  
✅ **Full tool outputs** - Complete return values logged  
✅ **Full API requests** - Endpoint, method, all parameters logged  
✅ **Full API responses** - Complete response data logged  
✅ **File logging enabled** - Logs written to `logs/mcp_*.log`  
✅ **Docker logs** - Also available via `docker logs`  
✅ **Log rotation** - Automatic at 10MB with 5 backups  

All logging is at DEBUG/INFO level for maximum visibility into MCP tool execution and API interactions.




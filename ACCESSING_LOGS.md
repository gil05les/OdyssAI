# Accessing Logs in Dockerized Environment

## Overview

Since the OdyssAI backend runs in Docker, logs are written inside the container. This guide shows you how to access them.

## Log Locations

Logs are written to the `logs/` directory, which is mounted as a volume:
- **Host path**: `OdyssAI/logs/`
- **Container path**: `/app/logs/`

## Method 1: Direct File Access (Recommended)

Since logs are mounted as a volume, you can access them directly on your host machine:

```bash
# View all logs
tail -f logs/app.log

# View agent logs
tail -f logs/agents.log

# View MCP logs
tail -f logs/mcp.log

# View API logs
tail -f logs/api.log

# View errors only
tail -f logs/errors.log
```

## Method 2: Docker Exec Commands

Access logs directly from inside the container:

```bash
# View all logs
docker exec odyssai-backend tail -f /app/logs/app.log

# View agent logs
docker exec odyssai-backend tail -f /app/logs/agents.log

# View MCP logs
docker exec odyssai-backend tail -f /app/logs/mcp.log

# View API logs
docker exec odyssai-backend tail -f /app/logs/api.log

# View errors
docker exec odyssai-backend tail -f /app/logs/errors.log
```

## Method 3: Docker Logs (Console Output)

View console output from the container:

```bash
# View all console output
docker logs odyssai-backend

# Follow logs in real-time
docker logs -f odyssai-backend

# View last 100 lines
docker logs --tail 100 odyssai-backend

# View logs with timestamps
docker logs -t odyssai-backend
```

## Method 4: Interactive Shell Access

Get a shell inside the container to explore logs:

```bash
# Get interactive shell
docker exec -it odyssai-backend /bin/bash

# Then inside the container:
cd /app/logs
ls -lah
tail -f agents.log
grep "FlightAgent" agents.log
```

## Useful Commands

### Search Logs

```bash
# Search for specific agent
grep "FlightAgent" logs/agents.log

# Search for MCP tool calls
grep "MCP REQUEST" logs/mcp.log

# Search for errors
grep "ERROR" logs/errors.log

# Search by date/time
grep "2025-12-12 15:00" logs/app.log
```

### View Log File Sizes

```bash
# On host
ls -lh logs/

# In container
docker exec odyssai-backend ls -lh /app/logs/
```

### Clear Logs

```bash
# Clear all logs (on host)
rm -f logs/*.log

# Clear specific log
> logs/app.log

# Clear logs in container
docker exec odyssai-backend sh -c "rm -f /app/logs/*.log"
```

### Copy Logs from Container

If logs aren't mounted (shouldn't happen, but just in case):

```bash
# Copy all logs
docker cp odyssai-backend:/app/logs ./logs

# Copy specific log
docker cp odyssai-backend:/app/logs/agents.log ./logs/agents.log
```

## Log Files

- **`logs/app.log`** - General application logs (all components)
- **`logs/agents.log`** - Detailed agent execution logs (input/output, state)
- **`logs/mcp.log`** - MCP server communication logs (tool calls, responses)
- **`logs/api.log`** - API request/response logs
- **`logs/errors.log`** - Error-only logs (for quick error scanning)

## Real-Time Monitoring

### Watch Multiple Logs Simultaneously

```bash
# Using multitail (if installed)
multitail logs/app.log logs/agents.log logs/mcp.log logs/api.log

# Using tail for multiple files
tail -f logs/app.log logs/agents.log logs/mcp.log logs/api.log
```

### Filter Logs by Component

```bash
# Only agent logs
tail -f logs/agents.log | grep "FlightAgent"

# Only MCP logs
tail -f logs/mcp.log | grep "search_flights"

# Only API logs
tail -f logs/api.log | grep "POST /api/flights"
```

## For AI Agents (Like Me)

When debugging, I can access logs by:

1. **Reading log files directly** from the `logs/` directory
2. **Using terminal commands** to search and filter logs
3. **Reading specific log entries** to understand the flow

Example commands I might use:
```bash
# Read the last 50 lines of agent logs
tail -50 logs/agents.log

# Search for a specific flight search
grep -A 20 "FlightAgent.execute" logs/agents.log | tail -30

# Check MCP tool calls
grep "MCP REQUEST.*search_flights" logs/mcp.log -A 10
```

## Troubleshooting

### Logs Not Appearing?

1. **Check if logs directory exists**:
   ```bash
   ls -la logs/
   ```

2. **Check container is running**:
   ```bash
   docker ps | grep odyssai-backend
   ```

3. **Check volume mount**:
   ```bash
   docker inspect odyssai-backend | grep -A 5 "Mounts"
   ```

4. **Check permissions**:
   ```bash
   docker exec odyssai-backend ls -la /app/logs/
   ```

### Logs Directory Not Mounted?

If the volume isn't mounted, logs are only in the container. You can:
1. Add the volume mount to `docker-compose.yml` (already done)
2. Restart the container: `docker-compose restart backend`
3. Or copy logs out: `docker cp odyssai-backend:/app/logs ./logs`

## Quick Reference

```bash
# Most common: View agent logs in real-time
tail -f logs/agents.log

# View all logs in real-time
tail -f logs/*.log

# Search for errors
grep -i error logs/*.log

# View last 100 lines of all logs
tail -100 logs/*.log
```




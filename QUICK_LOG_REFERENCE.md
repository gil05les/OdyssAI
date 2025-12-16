# Quick Log Reference

## Quick Commands

### Using Makefile (Easiest)

```bash
# View agent logs (most useful for debugging)
make logs-agents

# View MCP server communication
make logs-mcp

# View API requests/responses
make logs-api

# View all logs at once
make logs-all

# View Docker console output
make logs-docker

# Search logs
make logs-search TERM="FlightAgent"
```

### Using Direct Commands

```bash
# View agent logs
tail -f logs/agents.log

# View MCP logs
tail -f logs/mcp.log

# View all logs
tail -f logs/*.log

# Search logs
grep "FlightAgent" logs/agents.log
```

### Using Docker Commands

```bash
# View container console output
docker logs -f odyssai-backend

# View logs from inside container
docker exec odyssai-backend tail -f /app/logs/agents.log

# Get shell access
docker exec -it odyssai-backend /bin/bash
```

### Using Helper Script

```bash
# Make script executable (first time only)
chmod +x view-logs.sh

# View agent logs
./view-logs.sh agents

# View all logs
./view-logs.sh all

# Search logs
./view-logs.sh search FlightAgent
```

## Log Files

- `logs/app.log` - All application logs
- `logs/agents.log` - Agent execution (input/output, state)
- `logs/mcp.log` - MCP tool calls and responses
- `logs/api.log` - API requests/responses
- `logs/errors.log` - Errors only

## Most Common Use Cases

### Debug Flight Agent
```bash
make logs-agents | grep FlightAgent
```

### Debug MCP Tool Calls
```bash
make logs-mcp | grep search_flights
```

### Debug API Issues
```bash
make logs-api | grep "/api/flights"
```

### Find Errors
```bash
make logs-errors
# or
grep ERROR logs/*.log
```

## Tips

1. **Use `make logs-agents`** for detailed agent debugging
2. **Use `make logs-mcp`** to see MCP tool communication
3. **Use `make logs-all`** to see everything at once
4. **Use `grep`** to filter specific components
5. **Logs are in real-time** - they update as things happen




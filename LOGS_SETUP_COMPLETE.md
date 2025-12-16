# ✅ Logging System Setup Complete

## What Was Set Up

1. **Comprehensive Logging Configuration** (`backend/utils/logging_config.py`)
   - File logging to `logs/` directory
   - Console logging with formatting
   - Separate log files for different concerns
   - Automatic log rotation (10MB files, 5 backups)

2. **Docker Volume Mount** (`docker-compose.yml`)
   - Logs directory mounted: `./logs:/app/logs`
   - Logs accessible from both host and container

3. **Makefile Commands** (Easy access)
   - `make logs-agents` - View agent execution logs
   - `make logs-mcp` - View MCP communication logs
   - `make logs-api` - View API request/response logs
   - `make logs-all` - View all logs simultaneously
   - `make logs-search TERM="..."` - Search logs

4. **Helper Script** (`view-logs.sh`)
   - Easy-to-use script for viewing logs
   - Multiple viewing modes

5. **Documentation**
   - `ACCESSING_LOGS.md` - Complete guide
   - `QUICK_LOG_REFERENCE.md` - Quick commands
   - `LOGGING.md` - Detailed logging documentation

## How to Access Logs

### Method 1: Makefile (Recommended)
```bash
make logs-agents    # View agent logs
make logs-mcp       # View MCP logs
make logs-api       # View API logs
make logs-all       # View all logs
```

### Method 2: Direct File Access
```bash
tail -f logs/agents.log
tail -f logs/mcp.log
tail -f logs/api.log
```

### Method 3: Docker Commands
```bash
docker logs -f odyssai-backend                    # Console output
docker exec odyssai-backend tail -f /app/logs/agents.log  # File logs
```

### Method 4: Helper Script
```bash
./view-logs.sh agents
./view-logs.sh all
./view-logs.sh search FlightAgent
```

## Log Files Location

- **Host**: `OdyssAI/logs/`
- **Container**: `/app/logs/`
- **Mounted**: Yes (accessible from both)

## What Gets Logged

### Agent Logs (`logs/agents.log`)
- Input parameters (full JSON)
- State transitions (EXECUTING, CALLING_LLM, COMPLETED, FAILED)
- Output data (full JSON)
- Method calls with parameters
- LLM interactions

### MCP Logs (`logs/mcp.log`)
- Tool requests (server, tool name, parameters)
- Tool responses (data, success/failure)
- Server state (connection, initialization)

### API Logs (`logs/api.log`)
- Request details (method, path, headers, body)
- Response details (status, data, duration)
- Timing information

### Error Logs (`logs/errors.log`)
- All ERROR and CRITICAL level messages
- Stack traces
- Error context

## Next Steps

1. **Restart backend** to apply logging changes:
   ```bash
   make docker-restart-backend
   ```

2. **View logs** while testing:
   ```bash
   make logs-agents
   ```

3. **Monitor in real-time** as you use the frontend

## For AI Agents

I can now access logs by:
- Reading log files directly from `logs/` directory
- Using terminal commands to search/filter
- Reading specific log entries to understand flow

Example: When debugging, I'll read `logs/agents.log` to see what the FlightAgent is doing, and `logs/mcp.log` to see MCP tool calls.




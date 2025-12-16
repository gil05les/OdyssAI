# OdyssAI Detailed Logging System

## Overview

The OdyssAI backend now includes a comprehensive logging system that provides detailed visibility into:
- **Agent execution**: Input/output, state transitions, method calls
- **MCP server communication**: Tool requests/responses, server state
- **API requests/responses**: Full request/response logging with timing
- **Error tracking**: Detailed error logs with stack traces

## Log Files

All logs are stored in the `logs/` directory (created automatically):

- **`logs/app.log`** - General application logs (all components)
- **`logs/agents.log`** - Detailed agent execution logs (input/output, state)
- **`logs/mcp.log`** - MCP server communication logs (tool calls, responses)
- **`logs/api.log`** - API request/response logs
- **`logs/errors.log`** - Error-only logs (for quick error scanning)

Log files are automatically rotated when they reach 10MB, keeping the last 5 backups.

## Log Levels

- **DEBUG** - Very detailed information (default, for maximum visibility)
- **INFO** - General informational messages
- **WARNING** - Warning messages
- **ERROR** - Error messages
- **CRITICAL** - Critical errors

## What Gets Logged

### Agent Logging

Every agent execution logs:
1. **Input**: Full input parameters with JSON formatting
2. **State Transitions**: When agent moves between states (EXECUTING, CALLING_LLM, COMPLETED, FAILED)
3. **Output**: Full output data with success/failure status
4. **Method Calls**: Every method call with parameters
5. **LLM Interactions**: When LLM is called, prompt details, response details

### MCP Server Logging

Every MCP interaction logs:
1. **Tool Requests**: Server name, tool name, request parameters
2. **Tool Responses**: Response data, success/failure status
3. **Server State**: Connection status, initialization

### API Logging

Every API request logs:
1. **Request**: Method, path, headers, body (if applicable)
2. **Response**: Status code, response data, duration
3. **Timing**: Request duration in seconds

## Viewing Logs

### Terminal/Console

Logs are automatically displayed in the terminal with color coding and timestamps.

### Log Files

View logs in real-time:

```bash
# All logs
tail -f logs/app.log

# Agent logs only
tail -f logs/agents.log

# MCP logs only
tail -f logs/mcp.log

# API logs only
tail -f logs/api.log

# Errors only
tail -f logs/errors.log
```

### Search Logs

```bash
# Search for specific agent
grep "FlightAgent" logs/agents.log

# Search for MCP tool calls
grep "MCP REQUEST" logs/mcp.log

# Search for errors
grep "ERROR" logs/errors.log

# Search by time
grep "2025-12-12 15:00" logs/app.log
```

## Log Format

### Console Format
```
HH:MM:SS | LEVEL    | LOGGER_NAME                    | MESSAGE
```

### File Format (Detailed)
```
YYYY-MM-DD HH:MM:SS | LEVEL    | LOGGER_NAME                    | FUNCTION_NAME          | LINE | MESSAGE
```

## Example Log Entries

### Agent Execution
```
2025-12-12 15:30:45 | DEBUG    | agents.flight                  | execute                 | 113  | ================================================================================
2025-12-12 15:30:45 | DEBUG    | agents.flight                  | execute                 | 114  | 📥 AGENT INPUT: FlightAgent.execute
2025-12-12 15:30:45 | DEBUG    | agents.flight                  | execute                 | 115  | Agent: FlightAgent
2025-12-12 15:30:45 | DEBUG    | agents.flight                  | execute                 | 116  | Method: execute
2025-12-12 15:30:45 | DEBUG    | agents.flight                  | execute                 | 117  | Input Data:
{
  "origin": "ZRH",
  "destination": "LIS",
  "departure_date": "2026-01-11",
  ...
}
```

### MCP Tool Call
```
2025-12-12 15:30:46 | DEBUG    | mcp.flights                    | search_flights          | 250  | ================================================================================
2025-12-12 15:30:46 | DEBUG    | mcp.flights                    | search_flights          | 251  | 📡 MCP REQUEST: flights.search_flights
2025-12-12 15:30:46 | DEBUG    | mcp.flights                    | search_flights          | 252  | Server: flights
2025-12-12 15:30:46 | DEBUG    | mcp.flights                    | search_flights          | 253  | Tool: search_flights
2025-12-12 15:30:46 | DEBUG    | mcp.flights                    | search_flights          | 254  | Request:
{
  "origin": "ZRH",
  "destination": "LIS",
  ...
}
```

### API Request
```
2025-12-12 15:30:44 | INFO     | api                            | log_requests            | 75   | ================================================================================
2025-12-12 15:30:44 | INFO     | api                            | log_requests            | 76   | 🌐 API REQUEST: POST /api/flights
2025-12-12 15:30:44 | DEBUG    | api                            | log_requests            | 77   | Method: POST
2025-12-12 15:30:44 | DEBUG    | api                            | log_requests            | 78   | Path: /api/flights
```

## Configuration

Logging is configured in `backend/utils/logging_config.py`. To change settings:

```python
from utils.logging_config import setup_logging

# Change log level
setup_logging(level=logging.INFO)  # Less verbose

# Disable file logging (console only)
setup_logging(enable_file_logging=False)

# Change log file size
setup_logging(max_bytes=20 * 1024 * 1024)  # 20MB
```

## Integration with AI Agents

The logging system is designed to be accessible by AI agents (like me) for debugging:

1. **Structured Log Files**: Easy to parse and analyze
2. **Separate Log Files**: Different concerns separated for easier navigation
3. **Detailed Context**: Function names, line numbers, full data dumps
4. **State Tracking**: Clear state transitions for understanding flow

## Best Practices

1. **Use appropriate log levels**: DEBUG for detailed info, INFO for important events, ERROR for errors
2. **Log state transitions**: Help understand agent flow
3. **Log inputs/outputs**: Critical for debugging
4. **Include context**: Always include relevant parameters in log messages
5. **Don't log sensitive data**: Be careful with API keys, passwords, etc.

## Troubleshooting

### Logs not appearing?

1. Check that `logs/` directory exists and is writable
2. Verify logging is initialized (should see startup message)
3. Check log level (DEBUG shows everything)

### Too many logs?

1. Increase log level to INFO or WARNING
2. Disable file logging if only need console
3. Adjust rotation settings to keep fewer backups

### Need to clear logs?

```bash
# Clear all logs
rm -f logs/*.log

# Clear specific log
> logs/app.log
```




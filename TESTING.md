# Testing Guide for MCP Flights Server

This guide explains how to test the MCP Flights server at different levels.

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd OdyssAI/mcp-servers/mcp-flights
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export AMADEUS_CLIENT_ID="your_amadeus_client_id"
   export AMADEUS_CLIENT_SECRET="your_amadeus_client_secret"
   export AMADEUS_HOSTNAME="test"  # Use "test" for testing, "production" for production
   ```

   For testing with the agent:
   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   ```

## Testing Methods

### Method 1: Direct Tool Testing (Recommended First Step)

Test individual tools without the MCP server wrapper:

```bash
cd OdyssAI/mcp-servers/mcp-flights
python test_tools.py
```

This will:
- Test `autocomplete_airport_or_city` with "Zurich"
- Test `search_flights` for ZRH → LIS
- Test `get_airline_routes` for Swiss Airlines from Zurich

**Expected Output:**
- ✅ Success messages for each tool
- JSON responses with data
- Any errors with full tracebacks

### Method 2: MCP Server Protocol Testing

Test the MCP server's JSON-RPC implementation:

```bash
cd OdyssAI/mcp-servers/mcp-flights
python test_mcp_server.py
```

This will:
- Initialize the MCP server
- List available tools
- Call the autocomplete tool via JSON-RPC

**Expected Output:**
- Server initialization confirmation
- List of 5 tools
- Successful tool call with results

### Method 3: Manual MCP Server Testing

Test the server interactively via stdin/stdout:

```bash
cd OdyssAI/mcp-servers/mcp-flights
python server.py
```

Then send JSON-RPC requests manually (or use a script):

```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "autocomplete_airport_or_city", "arguments": {"query": "New York"}}}
```

### Method 4: Full Integration Test (With Agent)

Test the complete system with the agent and sandboxed MCP server:

```bash
cd OdyssAI/backend
python main.py
```

This will:
1. Mount the MCP server code into Docker
2. Request user consent for permissions
3. Start the agent with the MCP server
4. Execute a test query

**Note:** Requires Docker to be running.

### Method 5: Individual Tool Unit Testing

Test a specific tool in Python:

```python
from amadeus_client import AmadeusClientWrapper
from tools.autocomplete import autocomplete_airport_or_city

client = AmadeusClientWrapper()
result = autocomplete_airport_or_city("Zurich", "CH", client=client)
print(result)
```

## Testing Checklist

### ✅ Basic Functionality
- [ ] Tools can be imported without errors
- [ ] Amadeus client initializes correctly
- [ ] Logger works and outputs to stdout

### ✅ Tool Tests
- [ ] `autocomplete_airport_or_city` returns IATA codes
- [ ] `search_flights` returns flight options
- [ ] `price_flight_offer` returns pricing (requires offer from search)
- [ ] `get_airline_routes` returns destinations
- [ ] `book_flight` creates booking (use test environment!)

### ✅ MCP Protocol
- [ ] Server responds to `initialize`
- [ ] Server lists all 5 tools
- [ ] Server handles `tools/call` correctly
- [ ] Server returns proper JSON-RPC responses
- [ ] Server handles errors gracefully

### ✅ Logging
- [ ] Logs appear with timestamps
- [ ] Tool names are included in logs
- [ ] Request IDs are unique
- [ ] API calls are logged
- [ ] Errors are logged with stack traces

### ✅ Error Handling
- [ ] Invalid tool names return errors
- [ ] Missing required parameters return errors
- [ ] API errors are caught and returned properly
- [ ] Network errors trigger retries

## Common Issues and Solutions

### Issue: "Amadeus credentials not provided"
**Solution:** Set `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` environment variables

### Issue: "Module not found" errors
**Solution:** Make sure you're running from the correct directory and dependencies are installed

### Issue: Docker errors when testing with agent
**Solution:** 
- Ensure Docker is running: `docker ps`
- Check Docker has permission to access the code directory
- Verify the code mount path is correct

### Issue: API rate limit errors
**Solution:** 
- Use the test environment (`AMADEUS_HOSTNAME=test`)
- Wait between test runs
- Check your Amadeus account rate limits

### Issue: Import errors in tools
**Solution:** The tools use absolute imports. When running in sandbox, ensure the working directory is set correctly.

## Debugging Tips

1. **Enable Debug Logging:**
   - Logs are already set to DEBUG level
   - Check stdout for detailed log messages

2. **Test with Minimal Data:**
   - Start with `autocomplete_airport_or_city` (simplest tool)
   - Then test `search_flights` with known routes
   - Finally test booking (use test environment!)

3. **Check API Responses:**
   - Amadeus test environment may have limited data
   - Some routes might not have test data available
   - Try different dates/cities if one doesn't work

4. **Verify JSON-RPC Format:**
   - Responses must be valid JSON
   - Must include `jsonrpc: "2.0"` and `id` fields
   - Errors must follow JSON-RPC error format

## Next Steps After Testing

Once basic tests pass:
1. Test with real travel scenarios
2. Test error conditions (invalid inputs, API failures)
3. Test with the full agent workflow
4. Monitor performance and optimize if needed
5. Add more comprehensive test cases


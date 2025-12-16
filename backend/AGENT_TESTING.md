# Agent Testing Guide

This guide explains how to test the multi-agent system (Orchestrator, Destination Agent, and Flight Agent).

## Prerequisites

1. **Environment Variables**
   ```bash
   export AMADEUS_CLIENT_ID="your_amadeus_client_id"
   export AMADEUS_CLIENT_SECRET="your_amadeus_client_secret"
   export AMADEUS_HOSTNAME="test"  # Use "test" for testing
   export OPENAI_API_KEY="your_openai_api_key"
   ```

2. **Docker**
   - Docker must be running (required for MCP server sandboxing)
   - Check with: `docker ps`

3. **Dependencies**
   - All Python dependencies should be installed
   - MCP sandbox SDK should be installed

## Quick Start

### Run All Tests

```bash
cd OdyssAI/backend
python test_agents.py
```

This will run all tests:
1. Configuration validation
2. Destination Agent test
3. Flight Agent test
4. Orchestrator - Destination query
5. Orchestrator - Flight query
6. Orchestrator - Combined query

### Quick Smoke Test

Run a quick test to verify basic functionality:

```bash
python test_agents.py --quick
```

### Run Specific Test

Test individual components:

```bash
# Test configuration only
python test_agents.py --test config

# Test destination agent only
python test_agents.py --test destination

# Test flight agent only
python test_agents.py --test flight

# Test orchestrator only
python test_agents.py --test orchestrator
```

## Test Descriptions

### Test 1: Configuration Validation
- Verifies all required environment variables are set
- Checks Amadeus API configuration
- Validates model configuration

**Expected:** ✅ Configuration is valid

### Test 2: Destination Agent
- Tests destination discovery with a sample query
- Verifies agent can suggest destinations based on preferences
- Checks that agent returns meaningful results

**Query:** "I'm looking for beach destinations in Europe for a relaxing vacation."

**Expected:** ✅ Agent returns destination suggestions with descriptions

### Test 3: Flight Agent
- Tests flight search functionality
- Verifies agent can search for flights using MCP tools
- Checks that agent returns flight options

**Query:** "Find flights from Zurich (ZRH) to Lisbon (LIS) on 2025-05-10 for 1 adult"

**Expected:** ✅ Agent returns flight search results

### Test 4: Orchestrator - Destination Query
- Tests orchestrator's ability to route destination queries
- Verifies orchestrator invokes destination agent correctly
- Checks result aggregation

**Query:** "I'm looking for beach destinations in Europe. Suggest some options."

**Expected:** ✅ Orchestrator routes to destination agent and returns results

### Test 5: Orchestrator - Flight Query
- Tests orchestrator's ability to route flight queries
- Verifies orchestrator invokes flight agent correctly
- Checks result aggregation

**Query:** "Find flights from Zurich (ZRH) to Lisbon (LIS) on 2025-05-10 for 1 adult"

**Expected:** ✅ Orchestrator routes to flight agent and returns results

### Test 6: Orchestrator - Combined Query
- Tests orchestrator's ability to handle complex queries
- Verifies orchestrator can invoke multiple agents
- Checks workflow: destination discovery → flight search

**Query:** "I'm looking for beach destinations in Europe. Find flights from Zurich to one of them."

**Expected:** ✅ Orchestrator invokes both agents and returns combined results

## Manual Testing

### Test Individual Agents

You can also test agents manually using the main script:

```bash
cd OdyssAI/backend
python main.py
```

This runs the orchestrator with sample queries.

### Test with Custom Queries

Modify `main.py` to test with your own queries:

```python
# In main.py, replace the test queries with your own
test_query = "Your custom query here"
result = await orchestrator.orchestrate(test_query)
print(result)
```

## Expected Behavior

### Successful Test Output

```
✅ Configuration is valid
✅ Destination agent returned results
✅ Flight agent returned results
✅ Orchestrator returned results for destination query
✅ Orchestrator returned results for flight query
✅ Orchestrator returned results for combined query

Total: 6/6 tests passed
✅ All tests passed! 🎉
```

### Common Issues

#### Issue: "Configuration validation failed"
**Solution:** 
- Check that all required environment variables are set
- Verify `.env` file exists and is in the project root
- Run: `python -c "from config import Config; print(Config.validate())"`

#### Issue: "Docker errors"
**Solution:**
- Ensure Docker is running: `docker ps`
- Check Docker has permission to access directories
- Verify Docker can pull images

#### Issue: "Agent returned empty response"
**Possible causes:**
- API rate limits (wait and retry)
- Network issues
- Invalid API credentials
- Model API issues

**Solution:**
- Check API credentials are correct
- Verify network connectivity
- Check API rate limits
- Try with a simpler query

#### Issue: "Import errors"
**Solution:**
- Ensure you're in the correct directory (`backend/`)
- Verify all dependencies are installed
- Check Python path includes required directories

## Testing Checklist

Before deploying, verify:

- [ ] All environment variables are set
- [ ] Docker is running
- [ ] Configuration validation passes
- [ ] Destination agent can discover destinations
- [ ] Flight agent can search for flights
- [ ] Orchestrator routes queries correctly
- [ ] Orchestrator handles combined queries
- [ ] Error handling works (test with invalid queries)
- [ ] Resource cleanup works (no hanging processes)

## Performance Testing

For performance testing, you can:

1. **Measure response times:**
   ```python
   import time
   start = time.time()
   result = await orchestrator.orchestrate(query)
   print(f"Response time: {time.time() - start:.2f}s")
   ```

2. **Test with multiple queries:**
   - Run the test suite multiple times
   - Monitor for memory leaks
   - Check Docker container cleanup

3. **Load testing:**
   - Send multiple queries concurrently
   - Monitor API rate limits
   - Check system resources

## Debugging

### Enable Verbose Logging

The agents use the standard logging module. To see more details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check MCP Server Logs

MCP servers log to stdout. Check Docker logs if needed:

```bash
docker ps  # Find container ID
docker logs <container_id>
```

### Test Individual Components

If a test fails, isolate the issue:

1. Test configuration first: `python test_agents.py --test config`
2. Test destination agent: `python test_agents.py --test destination`
3. Test flight agent: `python test_agents.py --test flight`
4. Test orchestrator: `python test_agents.py --test orchestrator`

## Next Steps

After all tests pass:

1. Test with real-world scenarios
2. Test error conditions
3. Test edge cases (invalid dates, unknown cities, etc.)
4. Performance optimization
5. Integration with frontend


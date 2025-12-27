# Uber API Integration - Disabled

## Status

**Uber API integration is currently disabled** as we were unable to obtain an Uber API key.

## Implementation

The `get_uber_estimate` tool in the mcp-transport server always returns a graceful error that triggers LLM fallback. The LLM generates reasonable ride estimates based on:

- Distance between origin and destination (calculated using haversine formula)
- Typical ride-share pricing patterns (~$2-3/km + $3-5 base fare)
- Local market knowledge
- Traffic patterns and typical durations

## User Experience

- All LLM-generated ride estimates are tagged with `source="llm"` for transparency
- Frontend displays an "AI Estimate" badge for LLM-generated options
- Users see realistic estimates even without API access
- System gracefully handles the absence of Uber API

## Code Location

- **Client**: `mcp-servers/mcp-transport/uber_client.py`
- **Tool**: `mcp-servers/mcp-transport/tools/uber_estimate.py`
- **Documentation**: Updated in `mcp-servers/README.md`

## Future Enhancement

If an Uber API key becomes available in the future:

1. Update `uber_client.py` to remove the early return
2. Add Uber credentials to `.env`:
   ```
   UBER_CLIENT_ID=your_client_id
   UBER_CLIENT_SECRET=your_client_secret
   # OR
   UBER_SERVER_TOKEN=your_server_token
   ```
3. Update `backend/config.py` to restore Uber API permissions
4. The existing error handling will still work for API failures

## Current Behavior

The `get_estimate()` method in `UberClient`:
- Calculates approximate distance between coordinates
- Returns a structured error with helpful fallback hints
- Provides distance-based pricing guidance for the LLM
- Logs that Uber API is not available

This ensures the transport agent always has useful information to generate estimates, even without API access.


# OdyssAI Connection Flow

This document describes how the frontend, backend, agents, and MCP servers are connected.

## Full Connection Chain

```
Frontend (React) 
  ↓ HTTP POST /api/orchestrate
Nginx Proxy (port 8080)
  ↓ forwards to backend:8000
Backend API (FastAPI, port 8000)
  ↓ calls orchestrator.orchestrate_structured()
Orchestrator Agent
  ↓ creates specialized agents (Flight, Hotel, etc.)
Specialized Agents (FlightAgent, HotelAgent, etc.)
  ↓ creates Agent with MCP servers
SandboxedMCPStdio
  ↓ connects to Docker container via stdio
MCP Server Container (odyssai-mcp-flights, etc.)
  ↓ uses Amadeus SDK
Amadeus APIs (test.api.amadeus.com or api.amadeus.com)
```

## Detailed Flow

### 1. Frontend → Backend

**Frontend (`frontend/src/lib/api.ts`):**
- Calls `orchestrateTravelPlan(preferences)`
- Sends POST to `/api/orchestrate`
- Uses `API_BASE_URL` which is `/api` (proxied by nginx)

**Nginx (`frontend/nginx.conf`):**
- Listens on port 80 (exposed as 8080)
- Proxies `/api/*` requests to `http://backend:8000`
- Serves static frontend files

**Backend (`backend/api.py`):**
- Receives POST at `/api/orchestrate`
- Calls `orchestrator.orchestrate_structured(preferences)`

### 2. Backend → Agents

**Orchestrator (`backend/travel_agents/orchestrator.py`):**
- Determines which agents are needed (destination, flight, hotel, transport)
- Creates/get agents: `await self._get_flight_agent()`
- Each agent is lazy-loaded on first use

**Agent Creation (`backend/travel_agents/flight_agent.py`):**
- `_create_agent()` method:
  1. Ensures MCP container is running: `ensure_container_running(Config.MCP_FLIGHTS_CONTAINER)`
  2. Gets runtime permissions: `Config.get_runtime_permissions()`
  3. Creates `DevMCPManifest` with:
     - `code_mount`: Path to MCP server code (`/mcp-servers/mcp-flights`)
     - `exec_command`: Command to run (`python3 server.py`)
     - `permissions`: Network and env var access
  4. Creates `SandboxedMCPStdio` with manifest
  5. Creates `Agent` with MCP servers
  6. Returns agent for use

### 3. Agents → MCP Servers

**SandboxedMCPStdio (`python-mcp-sandbox-openai-sdk-main/src/mcp_sandbox_openai_sdk/sandbox.py`):**
- Connects to existing Docker container or creates new one
- Uses Docker stdio to communicate with MCP server
- Container runs in sandbox with restricted permissions

**MCP Server Container:**
- Started by `make docker-start-all` or `make up`
- Container name: `odyssai-mcp-flights`, `odyssai-mcp-hotels`, etc.
- Runs MCP server code from mounted volume
- Has access to:
  - Amadeus API domain (test.api.amadeus.com or api.amadeus.com)
  - Environment variables (AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET)

### 4. MCP Servers → Amadeus APIs

**MCP Server Code (`mcp-servers/mcp-flights/server.py`):**
- Implements MCP protocol
- Exposes tools (e.g., `search_flights`, `get_flight_price`)
- Uses Amadeus SDK to call APIs
- Returns structured data to agent

**Amadeus SDK:**
- Authenticates with OAuth2
- Makes API calls to Amadeus endpoints
- Returns flight/hotel/transfer data

## Path Resolution

### In Docker:

**Backend Config (`backend/config.py`):**
- `__file__` = `/app/config.py`
- `os.path.dirname(__file__)` = `/app`
- `os.path.dirname(os.path.dirname(__file__))` = `/`
- `MCP_FLIGHTS_PATH` = `/mcp-servers/mcp-flights` ✓

**Docker Compose:**
- Mounts `./mcp-servers:/mcp-servers`
- So `/mcp-servers/mcp-flights` exists in container ✓

## Environment Variables

Required in `.env` file:
- `AMADEUS_CLIENT_ID` - Amadeus API client ID
- `AMADEUS_CLIENT_SECRET` - Amadeus API client secret
- `OPENAI_API_KEY` - OpenAI API key for agents
- `AMADEUS_HOSTNAME` - `test` or `production` (default: `test`)
- `DEFAULT_MODEL` - OpenAI model (default: `gpt-4o`)

## Verification Checklist

✅ Frontend calls `/api/orchestrate` endpoint
✅ Nginx proxies `/api/*` to backend
✅ Backend receives request and calls orchestrator
✅ Orchestrator creates agents with MCP servers
✅ Agents connect to MCP containers via stdio
✅ MCP containers have access to Amadeus APIs
✅ Docker socket mounted for container management
✅ Paths resolve correctly in Docker environment

## Troubleshooting

If connections fail:

1. **Frontend can't reach backend:**
   - Check nginx logs: `docker logs odyssai-frontend`
   - Verify backend is running: `docker ps | grep odyssai-backend`
   - Test backend directly: `curl http://localhost:8000/health`

2. **Backend can't connect to MCP servers:**
   - Check MCP containers are running: `make docker-status`
   - Verify Docker socket is mounted: `docker exec odyssai-backend ls /var/run/docker.sock`
   - Check container logs: `docker logs odyssai-mcp-flights`

3. **MCP servers can't reach Amadeus:**
   - Verify environment variables: `docker exec odyssai-mcp-flights env | grep AMADEUS`
   - Check network permissions in container
   - Verify Amadeus credentials are correct

4. **Path resolution issues:**
   - Check paths in container: `docker exec odyssai-backend ls -la /mcp-servers`
   - Verify volume mounts in docker-compose.yml
   - Check config.py path calculations







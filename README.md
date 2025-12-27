# OdyssAI — Agentic Travel Planning with MCP

A multi-agent travel planning system that transforms user preferences into complete trip plans using specialized AI agents and sandboxed MCP (Model Context Protocol) servers.

## Overview

OdyssAI solves the fragmented nature of travel planning by providing an end-to-end workflow:

**Destinations → Flights → Hotels → Itinerary → Transport**

Each step is handled by a specialized AI agent that uses real travel APIs through sandboxed MCP servers, ensuring secure and consistent tool execution.

### Key Features

- **Multi-Agent Architecture**: 5 specialized agents (Destination, Flight, Hotel, Itinerary, Transport) coordinated by an LLM orchestrator
- **MCP Server Sandboxing**: Tools run in Docker containers via GuardiAgent for security and reproducibility
- **Real API Integration**: Amadeus (flights, hotels, cars, POIs), OpenWeatherMap, Yelp, Google Maps
- **Conversational Planning**: Chat sidebar for natural language preference capture
- **Trip Persistence**: Save, resume, and manage trip plans with PostgreSQL storage
- **Modern UI**: React + TypeScript with a cinematic, glass-morphism design

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────────────┐
│   React Frontend│────▶│  FastAPI Backend │────▶│      LLM Orchestrator           │
│   (Vite + TS)   │     │                  │     │                                 │
└─────────────────┘     └──────────────────┘     └──────────┬──────────────────────┘
                                                            │
                              ┌──────────────────────────────┼──────────────────────────────┐
                              │                              │                              │
                        ┌─────▼─────┐               ┌────────▼────────┐            ┌────────▼────────┐
                        │Destination│               │  Flight Agent   │            │  Hotel Agent    │
                        │  Agent    │               │                 │            │                 │
                        └─────┬─────┘               └────────┬────────┘            └────────┬────────┘
                              │                              │                              │
                    ┌─────────┴─────────┐                    │                              │
                    ▼                   ▼                    ▼                              ▼
            ┌──────────────┐   ┌──────────────┐      ┌──────────────┐              ┌──────────────┐
            │ mcp-flights  │   │   mcp-geo    │      │ mcp-flights  │              │  mcp-hotels  │
            │ (autocomplete)│   │(weather,POI) │      │  (search)    │              │   (search)   │
            └──────────────┘   └──────────────┘      └──────────────┘              └──────────────┘
                              Docker Sandbox (GuardiAgent)
```

## Prerequisites

- **Docker** and **Docker Compose** (required for MCP sandboxing)
- **Python 3.10+** (for local development)
- **Node.js 18+** (for frontend development)
- API keys (see [Environment Variables](#environment-variables))

## Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd OdyssAI

# Copy the example environment file and fill in your API keys
cp .env.example .env
```

### 2. Start All Services

```bash
# Using Make (recommended)
make up

# Or using Docker Compose directly
HOST_PROJECT_ROOT=$(pwd) docker-compose up -d
```

This starts:
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432

### 3. Start MCP Servers

```bash
make docker-start-all
```

## Environment Variables

Create a `.env` file in the project root with the following:

```bash
# Required: Amadeus API (flights, hotels, cars, POIs)
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
AMADEUS_ENV=test  # or "prod" for production

# Required: OpenAI API (agent reasoning)
OPENAI_API_KEY=your_openai_api_key

# Required: Unsplash (destination images)
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# Required: OpenWeatherMap (weather/seasonality)
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key

# Required: Yelp (activities/business search)
YELP_API_KEY=your_yelp_api_key

# Required: Google Maps (directions, geocoding)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Optional: Model configuration
DEFAULT_MODEL=gpt-5.1

# Docker configuration (auto-detected, but can be overridden)
HOST_PROJECT_ROOT=/path/to/OdyssAI
```

### Getting API Keys

| API | Sign Up | Free Tier |
|-----|---------|-----------|
| Amadeus | https://developers.amadeus.com/ | Test environment free |
| OpenAI | https://platform.openai.com/ | Pay-as-you-go |
| Unsplash | https://unsplash.com/developers | 50 requests/hour |
| OpenWeatherMap | https://openweathermap.org/api | 1,000 calls/day |
| Yelp | https://www.yelp.com/developers | 5,000 calls/day |
| Google Maps | https://console.cloud.google.com/ | $200 credit/month |

## Project Structure

```
OdyssAI/
├── backend/                    # FastAPI backend
│   ├── api.py                  # Main API endpoints
│   ├── config.py               # Configuration management
│   ├── database/               # PostgreSQL models and schemas
│   ├── services/               # Image, temperature, chat services
│   └── travel_agents/          # Agent implementations
│       ├── destination_agent.py
│       ├── flight_agent.py
│       ├── hotel_agent.py
│       ├── itinerary_agent.py
│       ├── transport_agent.py
│       ├── llm_orchestrator.py
│       └── base_agent.py
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/travel/  # Trip planning UI components
│   │   ├── pages/              # Route pages
│   │   ├── contexts/           # Auth and form contexts
│   │   └── services/           # API service layer
│   └── ...
├── mcp-servers/                # MCP server implementations
│   ├── mcp-flights/            # Amadeus flights API
│   ├── mcp-hotels/             # Amadeus hotels API
│   ├── mcp-cars/               # Amadeus car rentals
│   ├── mcp-geo-destinations/   # Country info, weather, POIs
│   ├── mcp-activities/         # Yelp business search
│   ├── mcp-transport/          # Google Maps directions
│   └── mcp-preferences/        # User preference storage
├── docker-compose.yml          # Service orchestration
├── Makefile                    # Development commands
└── logs/                       # Application logs
```

## Development

### Running Locally (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Useful Make Commands

```bash
make help              # Show all available commands
make up                # Start all services
make down              # Stop all services
make logs              # View logs from all services
make logs-agents       # View agent execution logs
make logs-mcp          # View MCP server logs
make test-backend      # Run backend tests
make docker-status     # Check container status
```

### Testing

```bash
# Backend agent tests
cd backend
python test_agents.py --quick    # Quick smoke test
python test_agents.py            # Full test suite

# Test specific component
python test_agents.py --test flight
python test_agents.py --test orchestrator
```

## MCP Servers

Each MCP server provides specific tools for travel operations:

| Server | Tools | API |
|--------|-------|-----|
| mcp-flights | autocomplete, search, price, book, routes | Amadeus |
| mcp-hotels | search by city, search by coordinates, offer details | Amadeus |
| mcp-cars | search at airport, offer details | Amadeus |
| mcp-geo-destinations | country info, travel season, weather, POIs | RestCountries, OpenWeatherMap, Amadeus |
| mcp-activities | business search | Yelp |
| mcp-transport | geocode, directions (driving/transit/walking), ride estimates | Google Maps |
| mcp-preferences | user preference storage | PostgreSQL |

All MCP servers run in Docker sandboxes with restricted network access (only allowed API domains).

## Known Limitations

- **Authentication**: Uses mock header-based auth (`X-User-ID`) for demo purposes. Production would require JWT tokens.
- **Uber API**: Integration disabled (no API access obtained). LLM generates ride estimates as fallback.
- **Amadeus API**: Test environment may have intermittent reliability. Caching is implemented to mitigate.

## Logs

Application logs are stored in the `logs/` directory:

```bash
logs/
├── app.log      # General application log
├── agents.log   # Agent execution details
├── mcp.log      # MCP server communication
├── api.log      # API request/response
└── errors.log   # Error log
```

View logs in real-time:
```bash
make logs-all      # All logs
make logs-agents   # Agent logs only
```

## Tech Stack

**Backend**: Python, FastAPI, SQLAlchemy, Pydantic, OpenAI Agents SDK

**Frontend**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Radix UI

**Infrastructure**: Docker, Docker Compose, PostgreSQL, GuardiAgent MCP Sandbox

**APIs**: Amadeus, OpenAI, Unsplash, OpenWeatherMap, Yelp, Google Maps

## License

This project was developed as part of a university course on AI-assisted development.

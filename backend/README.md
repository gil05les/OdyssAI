# OdyssAI Backend

Backend for the OdyssAI travel planning system with multi-agent architecture.

**Security:** All MCP servers run in GuardiAgent sandboxed Docker containers with restricted permissions for secure execution.

## Quick Start

### Prerequisites

1. Set environment variables (create `.env` in project root):
   ```bash
   AMADEUS_CLIENT_ID=your_client_id
   AMADEUS_CLIENT_SECRET=your_client_secret
   AMADEUS_HOSTNAME=test
   OPENAI_API_KEY=your_openai_key
   ```

2. Ensure Docker is running (required for MCP server sandboxing)

3. Install dependencies:
   ```bash
   pip install -r requirements.txt  # If you have one
   pip install openai-agents python-dotenv
   ```

### Running Tests

**Quick test:**
```bash
python test_agents.py --quick
```

**Full test suite:**
```bash
python test_agents.py
```

**Test specific component:**
```bash
python test_agents.py --test config      # Test configuration
python test_agents.py --test destination # Test destination agent
python test_agents.py --test flight     # Test flight agent
python test_agents.py --test orchestrator # Test orchestrator
```

### Running the Application

```bash
python main.py
```

This will run the orchestrator with sample queries.

## Architecture

- **Orchestrator**: Coordinates workflow between specialized agents
- **Destination Agent**: Discovers destinations based on user preferences
- **Flight Agent**: Handles flight search and booking operations

## Testing

See [AGENT_TESTING.md](AGENT_TESTING.md) for detailed testing documentation.

## Configuration

See [config.py](config.py) for configuration options.


# Rebuilding Docker Containers for Logging

## Quick Rebuild (Backend Only)

If you only need to rebuild the backend with new logging:

```bash
# Stop and remove backend
make docker-rm-backend

# Rebuild backend image
make docker-build-backend

# Start backend (will use new volume mount)
make docker-start-backend
```

## Full Rebuild (All Containers)

To rebuild everything from scratch:

```bash
# Stop all containers
make docker-down

# Remove backend container and image
docker rmi odyssai-backend:latest 2>/dev/null || true

# Rebuild backend
make docker-build-backend

# Start everything
make docker-up
```

## Using Docker Compose

Alternatively, using docker-compose:

```bash
# Stop and remove all containers
docker-compose down

# Rebuild backend image
docker-compose build backend

# Start all services
docker-compose up -d
```

## Verify Logging is Working

After rebuilding, check:

```bash
# Check logs directory exists in container
docker exec odyssai-backend ls -la /app/logs/

# View logs
make logs-agents

# Or check Docker console output
docker logs odyssai-backend | tail -20
```

## Expected Output

After restart, you should see in the logs:

```
🚀 OdyssAI Logging System Initialized
📁 Log directory: /app/logs
📄 Application log: /app/logs/app.log
📄 Agent log: /app/logs/agents.log
...
```




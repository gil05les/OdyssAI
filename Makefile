# Makefile for OdyssAI MCP Servers
# Manages dockerized sandboxed MCP servers, dependencies, and backend

# Variables
PROJECT_ROOT := $(shell pwd)
MCP_SERVERS_DIR := $(PROJECT_ROOT)/mcp-servers
MCP_FLIGHTS_DIR := $(MCP_SERVERS_DIR)/mcp-flights
MCP_HOTELS_DIR := $(MCP_SERVERS_DIR)/mcp-hotels
MCP_CARS_DIR := $(MCP_SERVERS_DIR)/mcp-cars
MCP_GEO_DIR := $(MCP_SERVERS_DIR)/mcp-geo-destinations
SANDBOX_SDK_DIR := $(PROJECT_ROOT)/python-mcp-sandbox-openai-sdk-main
BACKEND_DIR := $(PROJECT_ROOT)/backend

# Docker sandbox image
SANDBOX_IMAGE_REGISTRY := ghcr.io/guardiagent
SANDBOX_IMAGE_NAME := mcp-sandbox-pypi
SANDBOX_IMAGE_VERSION := latest
SANDBOX_IMAGE := $(SANDBOX_IMAGE_REGISTRY)/$(SANDBOX_IMAGE_NAME):$(SANDBOX_IMAGE_VERSION)

# Container names
CONTAINER_FLIGHTS := odyssai-mcp-flights
CONTAINER_HOTELS := odyssai-mcp-hotels
CONTAINER_CARS := odyssai-mcp-cars
CONTAINER_GEO := odyssai-mcp-geo
CONTAINER_BACKEND := odyssai-backend
CONTAINER_POSTGRES := odyssai-postgres

# Backend Docker image
BACKEND_IMAGE_NAME := odyssai-backend
BACKEND_IMAGE_VERSION := latest
BACKEND_IMAGE := $(BACKEND_IMAGE_NAME):$(BACKEND_IMAGE_VERSION)
BACKEND_PORT := 8000

# Load environment variables from .env if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Python commands (prefer Python 3.10+, fallback to python3, then python)
# Try specific versions first, then check python3/python
PYTHON := $(shell \
	if command -v python3.13 >/dev/null 2>&1; then \
		python3.13 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null && echo python3.13; \
	elif command -v python3.12 >/dev/null 2>&1; then \
		python3.12 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null && echo python3.12; \
	elif command -v python3.11 >/dev/null 2>&1; then \
		python3.11 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null && echo python3.11; \
	elif command -v python3.10 >/dev/null 2>&1; then \
		echo python3.10; \
	elif command -v python3 >/dev/null 2>&1; then \
		python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null && echo python3; \
	elif command -v python >/dev/null 2>&1; then \
		python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null && echo python; \
	fi \
)
# Fallback if no Python 3.10+ found
ifeq ($(PYTHON),)
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
endif
PIP := $(shell \
	if command -v pip3.13 >/dev/null 2>&1; then echo pip3.13; \
	elif command -v pip3.12 >/dev/null 2>&1; then echo pip3.12; \
	elif command -v pip3.11 >/dev/null 2>&1; then echo pip3.11; \
	elif command -v pip3.10 >/dev/null 2>&1; then echo pip3.10; \
	elif command -v pip3 >/dev/null 2>&1; then echo pip3; \
	else echo pip; \
	fi \
)

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help install-all install-mcp-servers install-mcp-flights install-mcp-hotels \
	install-mcp-cars install-mcp-geo install-sandbox-sdk install-backend \
	test-mcp-flights test-mcp-hotels test-mcp-cars test-mcp-geo test-all-servers \
	docker-pull-sandbox docker-clean-containers docker-clean-all docker-ps \
	docker-start-all docker-stop-all docker-restart-all docker-status \
	docker-start-flights docker-start-hotels docker-start-cars docker-start-geo \
	docker-stop-flights docker-stop-hotels docker-stop-cars docker-stop-geo \
	docker-build-backend docker-start-backend docker-stop-backend docker-restart-backend \
	docker-logs-backend docker-shell-backend docker-rm-backend \
	docker-up docker-down \
	build up down logs \
	run-backend test-backend clean \
	logs-app logs-agents logs-mcp logs-api logs-errors logs-all logs-docker logs-search

# Help target - shows all available commands
help: ## Show this help message
	@echo "OdyssAI - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Installation targets
install-all: install-mcp-servers install-sandbox-sdk install-backend ## Install all dependencies

install-mcp-servers: install-mcp-flights install-mcp-hotels install-mcp-cars install-mcp-geo ## Install dependencies for all MCP servers

install-mcp-flights: ## Install dependencies for mcp-flights server
	@echo "Installing dependencies for mcp-flights..."
	@cd "$(MCP_FLIGHTS_DIR)" && $(PIP) install -r requirements.txt || exit 1
	@echo "✓ mcp-flights dependencies installed"

install-mcp-hotels: ## Install dependencies for mcp-hotels server
	@echo "Installing dependencies for mcp-hotels..."
	@cd "$(MCP_HOTELS_DIR)" && $(PIP) install -r requirements.txt || exit 1
	@echo "✓ mcp-hotels dependencies installed"

install-mcp-cars: ## Install dependencies for mcp-cars server
	@echo "Installing dependencies for mcp-cars..."
	@cd "$(MCP_CARS_DIR)" && $(PIP) install -r requirements.txt || exit 1
	@echo "✓ mcp-cars dependencies installed"

install-mcp-geo: ## Install dependencies for mcp-geo-destinations server
	@echo "Installing dependencies for mcp-geo-destinations..."
	@cd "$(MCP_GEO_DIR)" && $(PIP) install -r requirements.txt || exit 1
	@echo "✓ mcp-geo-destinations dependencies installed"

install-sandbox-sdk: ## Install the MCP sandbox SDK
	@echo "Installing MCP sandbox SDK..."
	@if [ ! -d "$(SANDBOX_SDK_DIR)" ]; then \
		echo "Error: Sandbox SDK directory not found at $(SANDBOX_SDK_DIR)"; \
		exit 1; \
	fi
	@cd "$(SANDBOX_SDK_DIR)" && $(PIP) install -e . || exit 1
	@echo "✓ MCP sandbox SDK installed"

install-backend: ## Install backend dependencies
	@echo "Installing backend dependencies..."
	@if [ -f "$(BACKEND_DIR)/requirements.txt" ]; then \
		echo "Installing from requirements.txt..."; \
		$(PIP) install -r "$(BACKEND_DIR)/requirements.txt" || exit 1; \
	else \
		echo "Installing core dependencies..."; \
		$(PIP) install fastapi uvicorn[standard] pydantic python-dotenv python-multipart openai-agents || exit 1; \
	fi
	@echo "✓ Backend dependencies installed"

# Testing targets
test-all-servers: test-mcp-flights test-mcp-hotels test-mcp-cars test-mcp-geo ## Test all MCP servers directly (without Docker)

test-mcp-flights: ## Test mcp-flights server directly (without Docker)
	@echo "Testing mcp-flights server..."
	@cd "$(MCP_FLIGHTS_DIR)" && $(PYTHON) server.py --help 2>/dev/null || echo "Note: Server runs via JSON-RPC over stdin/stdout. Use test_tools.py for testing."
	@if [ -f "$(MCP_FLIGHTS_DIR)/test_tools.py" ]; then \
		echo "Running test_tools.py..."; \
		cd "$(MCP_FLIGHTS_DIR)" && $(PYTHON) test_tools.py || exit 1; \
	fi

test-mcp-hotels: ## Test mcp-hotels server directly (without Docker)
	@echo "Testing mcp-hotels server..."
	@cd "$(MCP_HOTELS_DIR)" && $(PYTHON) server.py --help 2>/dev/null || echo "Note: Server runs via JSON-RPC over stdin/stdout. Use test_tools.py for testing."
	@if [ -f "$(MCP_HOTELS_DIR)/test_tools.py" ]; then \
		echo "Running test_tools.py..."; \
		cd "$(MCP_HOTELS_DIR)" && $(PYTHON) test_tools.py || exit 1; \
	fi

test-mcp-cars: ## Test mcp-cars server directly (without Docker)
	@echo "Testing mcp-cars server..."
	@cd "$(MCP_CARS_DIR)" && $(PYTHON) server.py --help 2>/dev/null || echo "Note: Server runs via JSON-RPC over stdin/stdout. Use test_tools.py for testing."
	@if [ -f "$(MCP_CARS_DIR)/test_tools.py" ]; then \
		echo "Running test_tools.py..."; \
		cd "$(MCP_CARS_DIR)" && $(PYTHON) test_tools.py || exit 1; \
	fi

test-mcp-geo: ## Test mcp-geo-destinations server directly (without Docker)
	@echo "Testing mcp-geo-destinations server..."
	@cd "$(MCP_GEO_DIR)" && $(PYTHON) server.py --help 2>/dev/null || echo "Note: Server runs via JSON-RPC over stdin/stdout. Use test_tools.py for testing."
	@if [ -f "$(MCP_GEO_DIR)/test_tools.py" ]; then \
		echo "Running test_tools.py..."; \
		cd "$(MCP_GEO_DIR)" && $(PYTHON) test_tools.py || exit 1; \
	fi

# Docker management targets
docker-pull-sandbox: ## Pull the GuardiAgent MCP sandbox Docker image
	@echo "Pulling MCP sandbox Docker image: $(SANDBOX_IMAGE)"
	@docker pull $(SANDBOX_IMAGE) || exit 1
	@echo "✓ Sandbox image pulled successfully"

docker-clean-containers: ## Remove stopped MCP server containers
	@echo "Cleaning stopped MCP server containers..."
	@CONTAINERS=$$(docker ps -a --filter "ancestor=$(SANDBOX_IMAGE)" --format "{{.ID}}"); \
	if [ -n "$$CONTAINERS" ]; then \
		echo "$$CONTAINERS" | xargs docker rm; \
	else \
		echo "No containers to remove"; \
	fi
	@echo "✓ Containers cleaned"

docker-clean-all: ## Remove all containers and images related to MCP servers
	@echo "Cleaning all MCP-related Docker resources..."
	@CONTAINERS=$$(docker ps -a --filter "ancestor=$(SANDBOX_IMAGE)" --format "{{.ID}}"); \
	if [ -n "$$CONTAINERS" ]; then \
		echo "$$CONTAINERS" | xargs docker rm -f; \
	else \
		echo "No containers to remove"; \
	fi
	@echo "✓ All MCP Docker resources cleaned"

docker-ps: ## List running MCP-related containers
	@echo "Running MCP-related containers:"
	@docker ps --filter "ancestor=$(SANDBOX_IMAGE)" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}" || echo "No running containers"

# Long-running container management targets
docker-start-all: docker-start-flights docker-start-hotels docker-start-cars docker-start-geo ## Start all MCP server containers

docker-stop-all: docker-stop-flights docker-stop-hotels docker-stop-cars docker-stop-geo ## Stop all MCP server containers

docker-restart-all: docker-stop-all docker-start-all ## Restart all MCP server containers

docker-up: docker-start-all docker-start-backend ## Start all containers (MCP servers + backend)
	@echo ""
	@echo "✓ All containers started!"
	@echo "  API available at http://localhost:$(BACKEND_PORT)"

docker-down: docker-stop-backend docker-stop-all ## Stop all containers (backend + MCP servers)
	@echo ""
	@echo "✓ All containers stopped"

# Simple convenience commands
build: docker-pull-sandbox docker-build-backend ## Build all Docker images
	@echo "Building frontend image..."
	@docker-compose build frontend || exit 1
	@echo ""
	@echo "✓ All images built successfully"

up: ## Start all services
	@echo "Starting all services..."
	@HOST_PROJECT_ROOT="$(PROJECT_ROOT)" docker-compose up -d || exit 1
	@$(MAKE) docker-start-all
	@echo ""
	@echo "✓ All services started!"
	@echo "  Frontend: http://localhost:8080"
	@echo "  Backend API: http://localhost:8000"
	@echo "  Postgres: localhost:5432"

down: ## Stop all services
	@echo "Stopping all services..."
	@docker-compose down || true
	@$(MAKE) docker-stop-all
	@echo ""
	@echo "✓ All services stopped"

logs: ## View logs from all services (use SERVICE=backend|frontend|postgres|flights|hotels|cars|geo for specific service)
	@if [ -n "$(SERVICE)" ]; then \
		case "$(SERVICE)" in \
			backend) docker-compose logs -f backend 2>/dev/null || docker logs -f $(CONTAINER_BACKEND) 2>/dev/null || echo "Backend container not running" ;; \
			frontend) docker-compose logs -f frontend 2>/dev/null || echo "Frontend container not running" ;; \
			postgres) docker-compose logs -f postgres 2>/dev/null || docker logs -f $(CONTAINER_POSTGRES) 2>/dev/null || echo "Postgres container not running" ;; \
			flights) docker logs -f $(CONTAINER_FLIGHTS) 2>/dev/null || echo "Flights container not running" ;; \
			hotels) docker logs -f $(CONTAINER_HOTELS) 2>/dev/null || echo "Hotels container not running" ;; \
			cars) docker logs -f $(CONTAINER_CARS) 2>/dev/null || echo "Cars container not running" ;; \
			geo) docker logs -f $(CONTAINER_GEO) 2>/dev/null || echo "Geo container not running" ;; \
			*) echo "Unknown service: $(SERVICE). Use: backend, frontend, postgres, flights, hotels, cars, or geo" ;; \
		esac; \
	else \
		echo "Showing logs from docker-compose services (backend, frontend, postgres)..."; \
		echo "Use 'make logs SERVICE=<name>' to view specific service logs"; \
		echo "Available services: backend, frontend, postgres, flights, hotels, cars, geo"; \
		echo ""; \
		docker-compose logs -f 2>/dev/null || echo "No docker-compose services running"; \
	fi

docker-status: ## Show status of all containers (MCP servers + backend + postgres)
	@echo "OdyssAI Container Status:"
	@echo ""
	@echo "Docker Compose Services:"
	@for container in $(CONTAINER_BACKEND) $(CONTAINER_POSTGRES); do \
		if docker ps -a --format "{{.Names}}" | grep -q "^$$container$$"; then \
			status=$$(docker ps -a --filter "name=^$$container$$" --format "{{.Status}}"); \
			echo "  $$container: $$status"; \
		else \
			echo "  $$container: Not found"; \
		fi; \
	done
	@echo ""
	@echo "MCP Servers:"
	@for container in $(CONTAINER_FLIGHTS) $(CONTAINER_HOTELS) $(CONTAINER_CARS) $(CONTAINER_GEO); do \
		if docker ps -a --format "{{.Names}}" | grep -q "^$$container$$"; then \
			status=$$(docker ps -a --filter "name=^$$container$$" --format "{{.Status}}"); \
			echo "  $$container: $$status"; \
		else \
			echo "  $$container: Not found"; \
		fi; \
	done

# Helper function to start a container
# Note: Containers run in detached mode but keep stdin open for MCP stdio communication
define start-container
	@if docker ps -a --format "{{.Names}}" | grep -q "^$(1)$$"; then \
		if docker ps --format "{{.Names}}" | grep -q "^$(1)$$"; then \
			echo "Container $(1) is already running"; \
		else \
			echo "Starting existing container $(1)..."; \
			docker start $(1) || exit 1; \
			echo "✓ Container $(1) started"; \
		fi; \
	else \
		echo "Creating and starting container $(1)..."; \
		if [ -f "$(PROJECT_ROOT)/.env" ]; then \
			set -a; \
			. "$(PROJECT_ROOT)/.env"; \
			set +a; \
		fi; \
		if [ "$$AMADEUS_HOSTNAME" = "production" ] || [ "$$AMADEUS_ENV" = "prod" ] || [ "$$AMADEUS_ENV" = "production" ]; then \
			AMADEUS_DOMAIN="api.amadeus.com"; \
		else \
			AMADEUS_DOMAIN="test.api.amadeus.com"; \
		fi; \
		if [ -f "$(2)/start.sh" ]; then \
			EXE_CMD="/sandbox/start.sh"; \
		else \
			EXE_CMD="python3 server.py"; \
		fi; \
		docker run -d -i \
			--name $(1) \
			--cap-add=NET_ADMIN \
			-e PACKAGE=amadeus \
			-e PRE_INSTALLED=true \
			-e "EXE=$$EXE_CMD" \
			-e "ALLOWED_EGRESS=$$AMADEUS_DOMAIN:443,pypi.org:443,files.pythonhosted.org:443" \
			-e "AMADEUS_CLIENT_ID=$$AMADEUS_CLIENT_ID" \
			-e "AMADEUS_CLIENT_SECRET=$$AMADEUS_CLIENT_SECRET" \
			$$(if [ -n "$$AMADEUS_HOSTNAME" ] && [ "$$AMADEUS_HOSTNAME" != "test" ]; then echo "-e AMADEUS_HOSTNAME=$$AMADEUS_HOSTNAME"; fi) \
			--mount type=bind,src="$(2)",dst=/sandbox \
			$(SANDBOX_IMAGE) || exit 1; \
		echo "✓ Container $(1) created and started"; \
	fi
endef

docker-start-flights: ## Start mcp-flights container
	$(call start-container,$(CONTAINER_FLIGHTS),$(MCP_FLIGHTS_DIR))

docker-start-hotels: ## Start mcp-hotels container
	$(call start-container,$(CONTAINER_HOTELS),$(MCP_HOTELS_DIR))

docker-start-cars: ## Start mcp-cars container
	$(call start-container,$(CONTAINER_CARS),$(MCP_CARS_DIR))

docker-start-geo: ## Start mcp-geo-destinations container
	@if docker ps -a --format "{{.Names}}" | grep -q "^$(CONTAINER_GEO)$$"; then \
		if docker ps --format "{{.Names}}" | grep -q "^$(CONTAINER_GEO)$$"; then \
			echo "Container $(CONTAINER_GEO) is already running"; \
		else \
			echo "Starting existing container $(CONTAINER_GEO)..."; \
			docker start $(CONTAINER_GEO) || exit 1; \
			echo "✓ Container $(CONTAINER_GEO) started"; \
		fi; \
	else \
		echo "Creating and starting container $(CONTAINER_GEO)..."; \
		if [ -f "$(PROJECT_ROOT)/.env" ]; then \
			set -a; \
			. "$(PROJECT_ROOT)/.env"; \
			set +a; \
		fi; \
		if [ "$$AMADEUS_HOSTNAME" = "production" ] || [ "$$AMADEUS_ENV" = "prod" ] || [ "$$AMADEUS_ENV" = "production" ]; then \
			AMADEUS_DOMAIN="api.amadeus.com"; \
		else \
			AMADEUS_DOMAIN="test.api.amadeus.com"; \
		fi; \
		if [ -f "$(MCP_GEO_DIR)/start.sh" ]; then \
			EXE_CMD="/sandbox/start.sh"; \
		else \
			EXE_CMD="python3 server.py"; \
		fi; \
		docker run -d -i \
			--name $(CONTAINER_GEO) \
			--cap-add=NET_ADMIN \
			-e PACKAGE=amadeus \
			-e PRE_INSTALLED=true \
			-e "EXE=$$EXE_CMD" \
			-e "ALLOWED_EGRESS=$$AMADEUS_DOMAIN:443,pypi.org:443,files.pythonhosted.org:443,restcountries.com:443,api.openweathermap.org:443" \
			-e "AMADEUS_CLIENT_ID=$$AMADEUS_CLIENT_ID" \
			-e "AMADEUS_CLIENT_SECRET=$$AMADEUS_CLIENT_SECRET" \
			-e "OPENWEATHERMAP_API_KEY=$$OPENWEATHERMAP_API_KEY" \
			$$(if [ -n "$$AMADEUS_HOSTNAME" ] && [ "$$AMADEUS_HOSTNAME" != "test" ]; then echo "-e AMADEUS_HOSTNAME=$$AMADEUS_HOSTNAME"; fi) \
			--mount type=bind,src="$(MCP_GEO_DIR)",dst=/sandbox \
			$(SANDBOX_IMAGE) || exit 1; \
		echo "✓ Container $(CONTAINER_GEO) created and started"; \
	fi

# Helper function to stop a container
define stop-container
	@if docker ps --format "{{.Names}}" | grep -q "^$(1)$$"; then \
		echo "Stopping container $(1)..."; \
		docker stop $(1) || exit 1; \
		echo "✓ Container $(1) stopped"; \
	elif docker ps -a --format "{{.Names}}" | grep -q "^$(1)$$"; then \
		echo "Container $(1) is already stopped"; \
	else \
		echo "Container $(1) does not exist"; \
	fi
endef

docker-stop-flights: ## Stop mcp-flights container
	$(call stop-container,$(CONTAINER_FLIGHTS))

docker-stop-hotels: ## Stop mcp-hotels container
	$(call stop-container,$(CONTAINER_HOTELS))

docker-stop-cars: ## Stop mcp-cars container
	$(call stop-container,$(CONTAINER_CARS))

docker-stop-geo: ## Stop mcp-geo-destinations container
	$(call stop-container,$(CONTAINER_GEO))

# Backend Docker targets
docker-build-backend: ## Build the backend Docker image
	@echo "Building backend Docker image: $(BACKEND_IMAGE)"
	@docker build -f Dockerfile.backend -t $(BACKEND_IMAGE) "$(PROJECT_ROOT)" || exit 1
	@echo "✓ Backend image built successfully"

docker-start-backend: ## Start the backend container (requires MCP containers running)
	@if docker ps -a --format "{{.Names}}" | grep -q "^$(CONTAINER_BACKEND)$$"; then \
		if docker ps --format "{{.Names}}" | grep -q "^$(CONTAINER_BACKEND)$$"; then \
			echo "Container $(CONTAINER_BACKEND) is already running"; \
		else \
			echo "Starting existing container $(CONTAINER_BACKEND)..."; \
			docker start $(CONTAINER_BACKEND) || exit 1; \
			echo "✓ Container $(CONTAINER_BACKEND) started"; \
		fi; \
	else \
		echo "Creating and starting container $(CONTAINER_BACKEND)..."; \
		if [ -f "$(PROJECT_ROOT)/.env" ]; then \
			set -a; \
			. "$(PROJECT_ROOT)/.env"; \
			set +a; \
		fi; \
		docker run -d \
			--name $(CONTAINER_BACKEND) \
			-p $(BACKEND_PORT):8000 \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v "$(PROJECT_ROOT)/backend:/app" \
			-v "$(PROJECT_ROOT)/mcp-servers:/mcp-servers" \
			-v "$(PROJECT_ROOT)/python-mcp-sandbox-openai-sdk-main:/python-mcp-sandbox-openai-sdk-main" \
			-v "$(PROJECT_ROOT)/logs:/app/logs" \
			-e "HOST_PROJECT_ROOT=$(PROJECT_ROOT)" \
			-e "MCP_AUTO_CONSENT=true" \
			-e "AMADEUS_CLIENT_ID=$${AMADEUS_CLIENT_ID:-$$AMADEUS_API_KEY}" \
			-e "AMADEUS_CLIENT_SECRET=$${AMADEUS_CLIENT_SECRET:-$$AMADEUS_API_SECRET}" \
			-e "AMADEUS_API_KEY=$$AMADEUS_API_KEY" \
			-e "AMADEUS_API_SECRET=$$AMADEUS_API_SECRET" \
			-e "AMADEUS_HOSTNAME=$${AMADEUS_HOSTNAME:-$$AMADEUS_ENV}" \
			-e "AMADEUS_ENV=$$AMADEUS_ENV" \
			-e "OPENAI_API_KEY=$$OPENAI_API_KEY" \
			-e "OPENWEATHERMAP_API_KEY=$$OPENWEATHERMAP_API_KEY" \
			-e "UNSPLASH_ACCESS_KEY=$${UNSPLASH_ACCESS_KEY//\"/}" \
			-e "DEFAULT_MODEL=$${DEFAULT_MODEL:-gpt-4o}" \
			$(BACKEND_IMAGE) || exit 1; \
		echo "✓ Container $(CONTAINER_BACKEND) created and started"; \
		echo "  API available at http://localhost:$(BACKEND_PORT)"; \
	fi

docker-stop-backend: ## Stop the backend container
	@if docker ps --format "{{.Names}}" | grep -q "^$(CONTAINER_BACKEND)$$"; then \
		echo "Stopping container $(CONTAINER_BACKEND)..."; \
		docker stop $(CONTAINER_BACKEND) || exit 1; \
		echo "✓ Container $(CONTAINER_BACKEND) stopped"; \
	elif docker ps -a --format "{{.Names}}" | grep -q "^$(CONTAINER_BACKEND)$$"; then \
		echo "Container $(CONTAINER_BACKEND) is already stopped"; \
	else \
		echo "Container $(CONTAINER_BACKEND) does not exist"; \
	fi

docker-restart-backend: docker-stop-backend docker-start-backend ## Restart the backend container

docker-logs-backend: ## View backend container logs
	@docker logs -f $(CONTAINER_BACKEND)

docker-shell-backend: ## Open a shell in the backend container
	@docker exec -it $(CONTAINER_BACKEND) /bin/bash

docker-shell-postgres: ## Open a shell in the postgres container
	@docker exec -it $(CONTAINER_POSTGRES) /bin/sh

docker-psql: ## Connect to postgres database using psql
	@docker exec -it $(CONTAINER_POSTGRES) psql -U odyssai -d odyssai_db

docker-rm-backend: ## Remove the backend container
	@if docker ps -a --format "{{.Names}}" | grep -q "^$(CONTAINER_BACKEND)$$"; then \
		echo "Removing container $(CONTAINER_BACKEND)..."; \
		docker rm -f $(CONTAINER_BACKEND) || exit 1; \
		echo "✓ Container $(CONTAINER_BACKEND) removed"; \
	else \
		echo "Container $(CONTAINER_BACKEND) does not exist"; \
	fi

# Backend targets (local development)
run-backend: ## Run the backend application (local)
	@echo "Running backend application..."
	@cd "$(BACKEND_DIR)" && $(PYTHON) main.py

run-api: ## Run the FastAPI server (local, with hot-reload)
	@echo "Starting FastAPI server..."
	@cd "$(BACKEND_DIR)" && $(PYTHON) -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

test-backend: ## Run backend tests
	@echo "Running backend tests..."
	@cd "$(BACKEND_DIR)" && $(PYTHON) test_agents.py

# Log viewing targets
logs-app: ## View application log (all components)
	@echo "Viewing application log (Ctrl+C to stop)..."
	@tail -f "$(PROJECT_ROOT)/logs/app.log" 2>/dev/null || echo "Log file not found. Start the backend to generate logs."

logs-agents: ## View agent execution log (detailed I/O, state)
	@echo "Viewing agent execution log (Ctrl+C to stop)..."
	@tail -f "$(PROJECT_ROOT)/logs/agents.log" 2>/dev/null || echo "Log file not found. Start the backend to generate logs."

logs-mcp: ## View MCP server communication log (tool calls, responses)
	@echo "Viewing MCP server communication log (Ctrl+C to stop)..."
	@tail -f "$(PROJECT_ROOT)/logs/mcp.log" 2>/dev/null || echo "Log file not found. Start the backend to generate logs."

logs-api: ## View API request/response log
	@echo "Viewing API request/response log (Ctrl+C to stop)..."
	@tail -f "$(PROJECT_ROOT)/logs/api.log" 2>/dev/null || echo "Log file not found. Start the backend to generate logs."

logs-errors: ## View error log only
	@echo "Viewing error log (Ctrl+C to stop)..."
	@tail -f "$(PROJECT_ROOT)/logs/errors.log" 2>/dev/null || echo "Log file not found. Start the backend to generate logs."

logs-all: ## View all logs simultaneously
	@echo "Viewing all logs simultaneously (Ctrl+C to stop)..."
	@tail -f "$(PROJECT_ROOT)/logs"/*.log 2>/dev/null || echo "Log files not found. Start the backend to generate logs."

logs-docker: ## View Docker container console output
	@echo "Viewing Docker container console output (Ctrl+C to stop)..."
	@docker logs -f $(CONTAINER_BACKEND) 2>/dev/null || echo "Container not running."

logs-search: ## Search logs for a term (usage: make logs-search TERM="FlightAgent")
	@if [ -z "$(TERM)" ]; then \
		echo "Usage: make logs-search TERM=\"search term\""; \
		echo "Example: make logs-search TERM=\"FlightAgent\""; \
	else \
		echo "Searching for: $(TERM)"; \
		grep -r "$(TERM)" "$(PROJECT_ROOT)/logs"/*.log --color=always -n 2>/dev/null || echo "No matches found or log files don't exist."; \
	fi

# Utility targets
clean: ## Clean Python cache files and __pycache__ directories
	@echo "Cleaning Python cache files..."
	@find "$(PROJECT_ROOT)" -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find "$(PROJECT_ROOT)" -type f -name "*.pyc" -delete 2>/dev/null || true
	@find "$(PROJECT_ROOT)" -type f -name "*.pyo" -delete 2>/dev/null || true
	@find "$(PROJECT_ROOT)" -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "✓ Cache files cleaned"


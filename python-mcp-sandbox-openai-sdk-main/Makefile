PROJECT_NAME ?= amadeus-mcp
IMAGE ?= $(PROJECT_NAME):latest

# Build the Docker image
.PHONY: docker-build
docker-build:
	docker build -t $(IMAGE) .

# Run the example runner. Requires AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET envs.
.PHONY: run
run:
	@if [ -z "$$AMADEUS_CLIENT_ID" ] || [ -z "$$AMADEUS_CLIENT_SECRET" ]; then \
		echo "Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET"; exit 1; \
	fi
	docker run --rm \
		-e AMADEUS_CLIENT_ID \
		-e AMADEUS_CLIENT_SECRET \
		$(IMAGE)

# Build then run in one step.
.PHONY: up
up: docker-build run









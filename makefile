# Makefile for managing the Docker environment.

.PHONY: up down logs index-qdrant

# Starts the Docker containers in detached mode.
up:
	docker compose -f infra/docker-compose.yml up -d

# Rebuilds and starts the containers.
rebuild:
	docker compose -f infra/docker-compose.yml up -d --build

# Stops and removes the Docker containers.
down:
	docker compose -f infra/docker-compose.yml down

# Shows the logs of the Docker containers.
logs:
	docker compose -f infra/docker-compose.yml logs -f

# Indexes product embeddings into Qdrant using the backend container.
index-qdrant:
	docker compose -f infra/docker-compose.yml --env-file backend/.env exec backend \
		/app/.venv/bin/python -m app.services.qdrant_indexer

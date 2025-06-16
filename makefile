# Makefile for managing the Docker environment.

.PHONY: up down logs index-qdrant start-n8n stop-n8n logs-n8n restart-n8n

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

# n8n workflow automation commands
start-n8n:
	docker compose -f infra/docker-compose.yml up n8n -d
	@echo "n8n is starting..."
	@echo "Access n8n at: http://localhost:5678"
	@echo "Username: admin"
	@echo "Password: admin"

stop-n8n:
	docker compose -f infra/docker-compose.yml stop n8n

logs-n8n:
	docker compose -f infra/docker-compose.yml logs n8n -f

restart-n8n:
	docker compose -f infra/docker-compose.yml restart n8n

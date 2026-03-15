.PHONY: help build up down restart logs shell test clean

help: ## Show this help message
	@echo "Horizon Web UI - Makefile commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the Docker image
	docker-compose build

up: ## Start the application
	docker-compose up -d

down: ## Stop the application
	docker-compose down

restart: ## Restart the application
	docker-compose restart

logs: ## Show application logs
	docker-compose logs -f horizon

shell: ## Open a shell in the container
	docker-compose exec horizon /bin/bash

test: ## Run tests in the container
	docker-compose exec horizon python3 -m pytest tests/

clean: ## Remove containers, images, and volumes
	docker-compose down -v
	docker system prune -f

rebuild: ## Rebuild and restart the application
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

dev-backend: ## Start backend in development mode
	python3 -m uvicorn src.webui.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend in development mode
	cd frontend && npm run dev

install: ## Install dependencies
	pip3 install -e ".[webui,dev]"
	cd frontend && npm install

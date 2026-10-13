
.DEFAULT_GOAL := help
SHELL         := /bin/bash
UV            := uv
PYTHON        := $(UV) run python

.PHONY: help install dev up down logs lint typecheck test seed clean frontend-install frontend

## Show this help
help:
	@awk 'BEGIN{FS=":.*##"; printf "\n\033[1mUsage:\033[0m make \033[36m<target>\033[0m\n\n\033[1mTargets:\033[0m\n"} \
	     /^[a-zA-Z_-]+:.*?##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## Install all Python dependencies (including dev extras)
install:
	$(UV) sync --all-extras

## Start all docker services
up:
	docker compose up --build -d

## Stop and remove all services
down:
	docker compose down -v

## Tail logs from all services
logs:
	docker compose logs -f

# Development server
dev:
	$(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Install frontend dependencies
frontend-install:
	$(UV) pip install -r frontend/requirements.txt

## Run the Streamlit dashboard
frontend:
	$(UV) run streamlit run frontend/app.py

## Run ruff linter + formatter check
lint:
	$(UV) run ruff check app tests
	$(UV) run ruff format --check app tests

## Auto-fix lint issues
lint-fix:
	$(UV) run ruff check --fix app tests
	$(UV) run ruff format app tests

## Run mypy strict type checking
typecheck:
	$(UV) run mypy app --strict

# Tests

 ## Run all tests
test:
	$(UV) run pytest tests/ -v

 ## Run only unit tests
test-unit:
	$(UV) run pytest tests/unit/ -v

## Run graph/node tests
test-graph:
	$(UV) run pytest tests/graph/ -v

 ## Run integration tests
test-integration:
	$(UV) run pytest tests/integration/ -v

## Run API endpoint tests
test-api:
	$(UV) run pytest tests/api/ -v

## Run tests with coverage report
test-cov:
	$(UV) run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Data

## Seed sample documents into the running API
seed:
	@echo "Ingesting sample documents..."
	@for f in data/documents/*; do \
	    echo "  Ingesting $$f ..."; \
	    curl -s -X POST http://localhost:8000/documents/ingest \
	         -F "file=@$$f" | python3 -m json.tool; \
	done

# Cleanup
## Remove Python caches and build artefacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name "htmlcov"     -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true

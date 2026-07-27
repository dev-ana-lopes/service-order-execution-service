.PHONY: help install dev-install lint format test test-cov run run-dev compose-up compose-down compose-logs compose-mongo-shell compose-prod-up compose-prod-down compose-smoke clean build-docker docker-run check

help:
	@echo "Service Order Management API - Make Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies"
	@echo "  make dev-install      Install with dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black & isort"
	@echo "  make lint             Run lint suite"
	@echo "  make test             Run pytest"
	@echo "  make test-cov         Run pytest with coverage"
	@echo ""
	@echo "Running:"
	@echo "  make run              Run API server"
	@echo "  make run-dev          Run API server with reload"
	@echo "  make compose-up       Start local Docker stack"
	@echo "  make compose-mongo-shell Open a Mongo shell in the local Docker stack"
	@echo "  make compose-smoke    Run a quick local smoke test"

install:
	uv sync

dev-install:
	uv sync --dev

format:
	uv run black src tests
	uv run isort src tests

lint:
	uv run black --check src tests
	uv run isort --check-only src tests
	uv run flake8 src tests

test:
	uv run pytest -q

test-cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-report=html

run:
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8003

run-dev:
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload

compose-up:
	docker compose --env-file .env up -d --build

compose-smoke:
	curl -fsS http://localhost:8003/health >/dev/null
	curl -fsS http://localhost:8003/health/ready >/dev/null
	@echo "Compose smoke test passed"

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f api

compose-mongo-shell:
	docker compose exec mongo mongosh mongodb://localhost:27017/service_order

compose-prod-up:
	docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

compose-prod-down:
	docker compose --env-file .env.prod -f docker-compose.prod.yml down

clean:
	rm -rf .pytest_cache .coverage coverage.xml htmlcov build dist

build-docker:
	docker build -t service-order-execution-service:local .

docker-run:
	docker run -p 8003:8000 service-order-execution-service:local

check: lint test
	@echo "Checks passed."

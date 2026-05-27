.PHONY: install dev test test-cov lint migrate docker-up docker-down clean

PYTHON ?= python
PIP ?= pip

install:
	$(PIP) install -r requirements.txt -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

docker-up:
	docker compose up

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache htmlcov .coverage test.db
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help:
	@echo "Common targets:"
	@echo "  make install      Install dependencies"
	@echo "  make dev          Run dev server with reload"
	@echo "  make test         Run pytest"
	@echo "  make test-cov     Run pytest with coverage report"
	@echo "  make migrate      Apply Alembic migrations"
	@echo "  make docker-up    Start Postgres + API via docker compose"
	@echo "  make clean        Remove cache/coverage/DB artefacts"

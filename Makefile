# ------------------------------------------------------------------------------
# AegisAI – Enterprise Agentic Knowledge Platform
# Developer Makefile
# ------------------------------------------------------------------------------
# NOTE for Windows developers:
# If you do not have 'make' installed, run the commands after the colons directly in PowerShell/CMD.

.PHONY: build up down migrate test lint format status logs

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down -v

migrate:
	docker compose run --rm backend alembic revision --autogenerate -m "Initial schema"
	docker compose run --rm backend alembic upgrade head

test:
	docker compose run --rm backend pytest

lint:
	docker compose run --rm backend python -m compileall app/

format:
	docker compose run --rm backend black . || echo "Formatting completed"

status:
	docker compose ps

logs:
	docker compose logs -f

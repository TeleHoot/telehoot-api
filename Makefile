# Makefile for FastAPI project

.DEFAULT_GOAL:=help
.ONESHELL:
.EXPORT_ALL_VARIABLES:
MAKEFLAGS += --no-print-directory

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yml
DOCKER_COMPOSE_TEST = docker-compose -f docker-compose.tests.yml
DOCKER = docker
ALEMBIC = alembic
UV = uv
PRE_COMMIT = pre-commit
PYTEST = pytest
RUFF = ruff
UVICORN = uvicorn
HYPERCORN = hypercorn
PYRIGHT = pyright

# Help command
help:
	@echo "Available commands:"
	@echo ""
	@echo "== Development Environment =="
	@echo "  up                 - Start development containers (Docker)"
	@echo "  down               - Stop and remove development containers"
	@echo "  dev                - Full dev setup: start containers, run migrations, and launch app"
	@echo ""
	@echo "== Production Environment =="
	@echo "  prod               - Deploy production containers"
	@echo "  down-prod          - Stop and remove production containers"
	@echo ""
	@echo "== Database Management =="
	@echo "  migrate            - Apply database migrations and seed data"
	@echo ""
	@echo "== Dependency Management =="
	@echo "  install-deps       - Install all Python dependencies (prod + dev)"
	@echo ""
	@echo "== Code Quality & Testing =="
	@echo "  check              - Run all pre-commit checks"
	@echo "  pre-commit-install - Install git hook scripts for pre-commit"
	@echo "  lint               - Check code style with Ruff (with auto-fix)"
	@echo "  format             - Format code with Ruff formatter"
	@echo "  type-check         - Static type checking with Pyright"
	@echo "  pytest             - Run tests in Docker containers"
	@echo "  test               - Local test suite (lint + format + type-check + pytest)"
	@echo "  test-docker        - Docker-based test suite"
	@echo ""
	@echo "== Application Control =="
	@echo "  start              - Run FastAPI server with hot reload"
	@echo ""
	@echo "== Project Setup =="
	@echo "  uinit              - Unix setup: install deps + create .env"
	@echo "  winit              - Windows setup: install deps + create .env"
	@echo "  create-env-unix    - Create .env from example (Unix)"
	@echo "  create-env-windows - Create .env from example (Windows)"
	@echo "  keyfile            - Create keyfile for mongodb"
	@echo ""
	@echo "== Miscellaneous =="
	@echo "  help               - Show this help message"

# Start the development environment
up:
	$(DOCKER_COMPOSE) up -d --build

# Stop the development environment
down:
	$(DOCKER_COMPOSE) down

# Start the production environment
prod:
	$(DOCKER_COMPOSE_PROD) up -d --build

# Stop the production environment
down-prod:
	$(DOCKER_COMPOSE_PROD) down

# Run database migrations
migrate:
	$(UV) run $(ALEMBIC) -x run_seeds=true upgrade head

# Install dependencies using uv
install-deps:
	$(UV) sync --all-extras --dev

# Run pre-commit checks
check:
	$(UV) run $(PRE_COMMIT) run --all-files

# Install pre-commit hooks
pre-commit-install:
	$(PRE_COMMIT) install

# Perform linting on all files using ruff
lint:
	$(UV) run $(RUFF) check --fix .

# Format all files using ruff format
format:
	$(UV) run $(RUFF) format .

# Run static type checking using pyright
type-check:
	$(UV) run $(PYRIGHT)

# Run tests using pytest
pytest:
	$(DOCKER_COMPOSE_TEST) up --build --abort-on-container-exit
	$(DOCKER_COMPOSE_TEST) down

# Test the app (runs lint, format, and type-check first)
test: lint format type-check
	$(UV) run $(PYTEST) -v --durations=0 .

test-docker: lint format type-check pytest

# Start the app using uvicorn
start:
	$(UV) run $(HYPERCORN) src.main:app --bind 0.0.0.0:8000 --reload

# Create .env file from example.env on Unix systems
create-env-unix:
	@if [ -f .env ]; then \
		echo ".env file already exists. Aborting to avoid overwriting."; \
	else \
		cp example.env .env; \
		echo ".env file created from example.env."; \
	fi

# Create .env file from example.env on Windows systems
create-env-windows:
	@if exist .env ( \
		echo .env file already exists. Aborting to avoid overwriting. \
	) else ( \
		copy example.env .env && \
		echo .env file created from example.env. \
	)

# Initialize the project on Unix systems (install dependencies, create .env file)
uinit: install-deps create-env-unix keyfile
	@echo "Project initialized for Unix systems."

# Initialize the project on Windows systems (install dependencies, create .env file)
winit: install-deps create-env-windows keyfile
	@echo "Project initialized for Windows systems."

# Start the development environment and the app
dev: up migrate start

# Create keyfile for mongodb
keyfile:
	@echo "Creating keyfile in project root"; \
	$(DOCKER) build -t mongo-keygen -f docker/Dockerfile.keygen docker/; \
	$(DOCKER) run --rm -v .:/data mongo-keygen

.PHONY: help up down up-prod down-prod migrate install-deps pre-commit pre-commit-install lint format type-check pytest test test-docker start create-env-unix create-env-windows init-unix init-windows dev keyfile

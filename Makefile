# Makefile for FastAPI project

.DEFAULT_GOAL:=help
.ONESHELL:
.EXPORT_ALL_VARIABLES:
MAKEFLAGS += --no-print-directory

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yml
ALEMBIC = alembic
UV = uv
PRE_COMMIT = pre-commit
PYTEST = pytest
RUFF = ruff
UVICORN = uvicorn
PYRIGHT = pyright

# Help command
help:
	@echo "Available commands:"
	@echo "== Development Environment =="
	@echo "  up                 - Start the development environment using docker-compose"
	@echo "  down               - Stop the development environment"
	@echo "  dev                - Start the development environment and the app"
	@echo "== Production Environment =="
	@echo "  prod               - Start the production environment using docker-compose.prod.yml"
	@echo "  down-prod          - Stop the production environment"
	@echo "== Database =="
	@echo "  migrate            - Run database migrations"
	@echo "== Dependencies =="
	@echo "  install-deps       - Install dependencies using uv"
	@echo "== Code Quality =="
	@echo "  check              - Run pre-commit checks"
	@echo "  check-install      - Install pre-commit hooks"
	@echo "  lint               - Perform linting on all files using ruff"
	@echo "  format             - Format all files using ruff format"
	@echo "  type-check         - Run static type checking using pyright"
	@echo "  test               - Test the app (runs lint and format first)"
	@echo "== Application =="
	@echo "  start              - Start the app using uvicorn"
	@echo "== Project Initialization =="
	@echo "  uinit              - Initialize the project on Unix systems (install dependencies, create .env file)"
	@echo "  winit              - Initialize the project on Windows systems (install dependencies, create .env file)"
	@echo "  create-env-unix    - Create .env file from example.env on Unix systems"
	@echo "  create-env-windows - Create .env file from example.env on Windows systems"
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

# Test the app (runs lint, format, and type-check first)
test: lint format type-check
	$(UV) run $(PYTEST) -v --durations=0 --cov .

# Start the app using uvicorn
start:
	$(UV) run $(UVICORN) src.main:app --host 0.0.0.0 --port 8000 --reload

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
uinit: install-deps create-env-unix
	@echo "Project initialized for Unix systems."

# Initialize the project on Windows systems (install dependencies, create .env file)
winit: install-deps create-env-windows
	@echo "Project initialized for Windows systems."

# Start the development environment and the app
dev: up migrate start

.PHONY: help up down up-prod down-prod migrate install-deps pre-commit pre-commit-install lint format type-check test start create-env-unix create-env-windows init-unix init-windows dev

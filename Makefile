.PHONY: help db-up db-down backend-dev frontend-dev test migrate setup clean

# Default target
help:
	@echo "MogiPay Development Commands"
	@echo ""
	@echo "Database:"
	@echo "  make db-up           - Start PostgreSQL container"
	@echo "  make db-down         - Stop PostgreSQL container"
	@echo ""
	@echo "Development:"
	@echo "  make backend-dev     - Start backend development server"
	@echo "  make frontend-dev    - Start frontend development server"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run backend tests"
	@echo ""
	@echo "Database Management:"
	@echo "  make migrate         - Run database migrations"
	@echo ""
	@echo "Setup & Cleanup:"
	@echo "  make setup           - Initial project setup"
	@echo "  make clean           - Clean Docker volumes and caches"

# Start PostgreSQL container
db-up:
	docker compose -f docker-compose.dev.yml up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	@docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U mogipay_user -d mogipay_dev || echo "PostgreSQL is starting..."

# Stop PostgreSQL container
db-down:
	docker compose -f docker-compose.dev.yml down

# Start backend development server
backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend development server
frontend-dev:
	cd frontend && npm run dev

# Run backend tests
test:
	cd backend && uv run pytest

# Run database migrations
migrate:
	cd backend && uv run alembic upgrade head

# Initial project setup
setup: db-up
	@echo "Installing backend dependencies..."
	cd backend && uv sync
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Running database migrations..."
	$(MAKE) migrate
	@echo ""
	@echo "Setup complete! You can now start development servers:"
	@echo "  Terminal 1: make db-up (already running)"
	@echo "  Terminal 2: make backend-dev"
	@echo "  Terminal 3: make frontend-dev"

# Clean Docker volumes and caches
clean:
	docker compose -f docker-compose.dev.yml down -v
	@echo "Docker volumes removed"
	@rm -rf backend/.venv backend/__pycache__ backend/.pytest_cache
	@rm -rf frontend/node_modules frontend/.next
	@echo "Caches cleaned"

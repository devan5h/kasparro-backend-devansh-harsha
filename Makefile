.PHONY: up down test build clean migrate migrate-up migrate-down logs

# Start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Stop and remove volumes
clean:
	docker-compose down -v

# Build images
build:
	docker-compose build

# Run tests
test:
	docker-compose exec api pytest tests/ -v --cov=. --cov-report=html

# Run tests locally (requires local setup)
test-local:
	pytest tests/ -v --cov=. --cov-report=html

# Run database migrations
migrate:
	docker-compose exec api alembic upgrade head

# Create new migration
migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

# Rollback migration
migrate-down:
	docker-compose exec api alembic downgrade -1

# View logs
logs:
	docker-compose logs -f

# View API logs
logs-api:
	docker-compose logs -f api

# View ETL logs
logs-etl:
	docker-compose logs -f etl

# Run ETL once (not continuous)
etl-once:
	docker-compose exec etl python run_etl.py

# Access database shell
db-shell:
	docker-compose exec db psql -U postgres -d kasparoo_db


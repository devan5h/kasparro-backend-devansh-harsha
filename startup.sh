#!/bin/bash
# Startup script that runs migrations and starts the application

echo "Waiting for database to be ready..."
sleep 5

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"


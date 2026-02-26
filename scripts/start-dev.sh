#!/bin/bash
# Development environment startup script

set -e

echo "Starting Navi development environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update .env with your configuration before continuing."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker compose -f docker-compose.dev.yml down

# Start services
echo "Starting services..."
docker compose -f docker-compose.dev.yml up -d postgres redis

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run database migrations
echo "Running database migrations..."
docker compose -f docker-compose.dev.yml exec -T postgres psql -U navi -d navi -c "SELECT 1" > /dev/null 2>&1 || {
    echo "Database not ready yet, waiting..."
    sleep 5
}

# Start backend and frontend
echo "Starting backend and frontend..."
docker compose -f docker-compose.dev.yml up -d backend frontend

echo ""
echo "Development environment started successfully!"
echo ""
echo "Services:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "To view logs: docker compose -f docker-compose.dev.yml logs -f"
echo "To stop: docker compose -f docker-compose.dev.yml down"

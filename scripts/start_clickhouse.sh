#!/bin/bash
# Script to start ClickHouse server using Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.clickhouse.yml"

echo "Starting ClickHouse server with Docker..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if container already exists and is running
if docker ps --format '{{.Names}}' | grep -q "^cleaning_warehouse_clickhouse$"; then
    echo "✓ ClickHouse container is already running"
    echo ""
    echo "Connection details:"
    echo "  Host: localhost"
    echo "  Port: 9000 (native), 8123 (HTTP)"
    echo "  Database: cleaning_warehouse"
    echo "  User: default"
    echo "  Password: (empty)"
    exit 0
fi

# Start the container
cd "$PROJECT_ROOT"
docker-compose -f "$COMPOSE_FILE" up -d

echo ""
echo "✓ ClickHouse server started!"
echo ""
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: 9000 (native), 8123 (HTTP)"
echo "  Database: cleaning_warehouse"
echo "  User: default"
echo "  Password: (empty)"
echo ""
echo "To stop: docker-compose -f $COMPOSE_FILE down"
echo "To view logs: docker-compose -f $COMPOSE_FILE logs -f"


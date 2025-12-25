#!/bin/bash
# Script to stop ClickHouse server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.clickhouse.yml"

echo "Stopping ClickHouse server..."
cd "$PROJECT_ROOT"
docker-compose -f "$COMPOSE_FILE" down
echo "✓ ClickHouse server stopped"


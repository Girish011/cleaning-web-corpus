#!/bin/bash
# Run E2E tests for the Cleaning Workflow Planner API

set -e

echo "Running E2E tests for Cleaning Workflow Planner API..."
echo "=================================================="

# Run pytest with E2E tests
pytest tests/e2e/ -v --tb=short

echo ""
echo "E2E tests completed!"


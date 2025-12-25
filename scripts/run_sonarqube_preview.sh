#!/bin/bash
# Script to run SonarQube analysis locally in PREVIEW mode
# NOTE: Preview mode is DEPRECATED in newer SonarQube versions
# Use run_local_analysis.sh instead for local code quality checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "⚠️  WARNING: Preview mode is deprecated in SonarQube 8.0+"
echo ""
echo "For local code quality analysis, use:"
echo "  ./scripts/run_local_analysis.sh"
echo ""
echo "This script uses pylint, flake8, mypy, and bandit for comprehensive checks."
echo ""
echo "For full SonarQube analysis, push to GitHub and let GitHub Actions run it:"
echo "  https://sonarcloud.io/project/overview?id=Girish011_cleaning-web-corpus"
echo ""
echo "Would you like to run local analysis instead? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    ./scripts/run_local_analysis.sh
else
    echo "Exiting..."
    exit 0
fi


#!/bin/bash
# Script to run SonarQube analysis locally and upload to SonarCloud
# NOTE: This requires Automatic Analysis to be disabled in SonarCloud
# For local-only analysis, use run_sonarqube_preview.sh instead

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Check if token is provided
if [ -z "$SONAR_TOKEN" ]; then
    echo "Error: SONAR_TOKEN environment variable is not set"
    echo ""
    echo "Please set it before running:"
    echo "  export SONAR_TOKEN='your_sonarcloud_token'"
    echo "  export SONAR_ORG='girish11'"
    echo ""
    echo "Or run with:"
    echo "  SONAR_TOKEN='your_token' SONAR_ORG='girish11' $0"
    exit 1
fi

if [ -z "$SONAR_ORG" ]; then
    echo "Error: SONAR_ORG environment variable is not set"
    echo "Please set: export SONAR_ORG='girish11'"
    exit 1
fi

echo "Running SonarQube analysis..."
echo "Project: Girish011_cleaning-web-corpus"
echo "Organization: $SONAR_ORG"
echo ""

# Run sonar-scanner
sonar-scanner \
    -Dsonar.token="$SONAR_TOKEN" \
    -Dsonar.organization="$SONAR_ORG" \
    -Dsonar.host.url=https://sonarcloud.io

echo ""
echo "Analysis complete! Check results at:"
echo "https://sonarcloud.io/project/overview?id=Girish011_cleaning-web-corpus"


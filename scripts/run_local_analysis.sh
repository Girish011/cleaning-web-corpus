#!/bin/bash
# Script to run local static analysis tools
# Alternative to SonarQube preview mode (which is deprecated)
# Uses pylint, flake8, mypy, and bandit for comprehensive code quality checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Running local static analysis..."
echo "=================================="
echo ""

# Check if tools are installed
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "⚠️  $1 not found. Install with: pip install $1"
        return 1
    fi
    return 0
}

# Install tools if not present
install_tools() {
    echo "Installing analysis tools..."
    pip install --quiet pylint flake8 mypy bandit safety || true
}

# Run pylint
run_pylint() {
    if check_tool pylint; then
        echo ""
        echo "🔍 Running pylint..."
        echo "----------------------------------------"
        pylint src/ --output-format=text --reports=yes --score=yes || true
    else
        install_tools
        if check_tool pylint; then
            pylint src/ --output-format=text --reports=yes --score=yes || true
        fi
    fi
}

# Run flake8
run_flake8() {
    if check_tool flake8; then
        echo ""
        echo "🔍 Running flake8..."
        echo "----------------------------------------"
        flake8 src/ --count --statistics --max-line-length=120 --exclude=__pycache__,*.pyc || true
    else
        install_tools
        if check_tool flake8; then
            flake8 src/ --count --statistics --max-line-length=120 --exclude=__pycache__,*.pyc || true
        fi
    fi
}

# Run mypy (type checking)
run_mypy() {
    if check_tool mypy; then
        echo ""
        echo "🔍 Running mypy (type checking)..."
        echo "----------------------------------------"
        mypy src/ --ignore-missing-imports --no-strict-optional || true
    else
        install_tools
        if check_tool mypy; then
            mypy src/ --ignore-missing-imports --no-strict-optional || true
        fi
    fi
}

# Run bandit (security)
run_bandit() {
    if check_tool bandit; then
        echo ""
        echo "🔍 Running bandit (security analysis)..."
        echo "----------------------------------------"
        bandit -r src/ -f json -o bandit-report.json -q || true
        bandit -r src/ -f txt || true
    else
        install_tools
        if check_tool bandit; then
            bandit -r src/ -f json -o bandit-report.json -q || true
            bandit -r src/ -f txt || true
        fi
    fi
}

# Run safety (dependency vulnerabilities)
run_safety() {
    if check_tool safety; then
        echo ""
        echo "🔍 Running safety (dependency check)..."
        echo "----------------------------------------"
        safety check --json --output safety-report.json || true
        safety check || true
    else
        install_tools
        if check_tool safety; then
            safety check --json --output safety-report.json || true
            safety check || true
        fi
    fi
}

# Main execution
echo "Starting local code quality analysis..."
echo ""

# Run all checks
run_pylint
run_flake8
run_mypy
run_bandit
run_safety

echo ""
echo "=================================="
echo "✅ Local analysis complete!"
echo ""
echo "Reports generated:"
echo "  - bandit-report.json (security issues)"
echo "  - safety-report.json (dependency vulnerabilities)"
echo ""
echo "Note: For full SonarQube analysis, push to GitHub and check:"
echo "  https://sonarcloud.io/project/overview?id=Girish011_cleaning-web-corpus"
echo ""


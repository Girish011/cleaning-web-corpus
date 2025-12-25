# Developer Workflow Guide

This document describes the development workflow, tools, and best practices for the Cleaning Web Corpus project.

## Table of Contents

- [SonarQube MCP Integration](#sonarqube-mcp-integration)
- [Development Setup](#development-setup)
- [Code Quality Checks](#code-quality-checks)
- [Testing Workflow](#testing-workflow)

## SonarQube MCP Integration

### Overview

The project uses SonarQube MCP (Model Context Protocol) server integration in Cursor to perform code quality analysis. This provides automated code quality checks, bug detection, code smell identification, and maintainability metrics.

### Configuration

The SonarQube MCP server is configured in Cursor's **Tools & MCP** settings. The configuration uses a Docker-based MCP server.

**Server Command:**
```bash
docker run -i --rm -e SONARQUBE_TOKEN -e SONARQUBE_ORG -e SONARQUBE_HOST_URL mcp/sonarqube
```

**Important:** 
- **Do NOT run this command manually in your terminal** - Cursor executes it automatically
- The `-e VAR` syntax means Docker will use the environment variable from the host
- These variables must be configured in **Cursor Settings > Tools & MCP**, not in your shell
- Cursor will automatically pass the configured environment variables to Docker when it runs the MCP server

**Environment Variables:**
- `SONARQUBE_TOKEN`: Authentication token for SonarQube API access (required)
- `SONARQUBE_ORG`: SonarQube organization key (required for SonarCloud)
- `SONARQUBE_HOST_URL`: Base URL of SonarQube instance (optional, defaults to SonarCloud if not provided)
  - For SonarCloud: Not needed (defaults to https://sonarcloud.io)
  - For self-hosted: e.g., `https://sonarqube.example.com`

**Important:** The `-e` flag in the Docker command tells Docker to pass environment variables from the host. These must be set in Cursor's MCP configuration, not in your terminal shell.

**Setup Instructions:**

1. **Generate a SonarQube Token:**
   - **For SonarCloud:**
     - Go to https://sonarcloud.io
     - Navigate to: User Account > Security
     - Generate a new token
     - Copy the token (it won't be shown again)
   - **For self-hosted SonarQube:**
     - Go to your SonarQube instance
     - Navigate to: User > My Account > Security
     - Generate a new token

2. **Get Organization Key:**
   - **For SonarCloud:** Your organization key (visible in organization settings)
   - **For self-hosted:** Usually not required, or use your organization key if using organizations

3. **Configure in Cursor:**
   - Open Cursor Settings > Tools & MCP
   - Find the "sonarqube" MCP server
   - Click to expand the server configuration
   - In the environment variables section, add:
     - `SONARQUBE_TOKEN`: Your generated token (paste the actual token value)
     - `SONARQUBE_ORG`: Your SonarCloud organization key (paste the actual org key)
     - `SONARQUBE_HOST_URL`: Base URL (only if using self-hosted SonarQube, e.g., `https://sonarqube.example.com`)
   - Save the configuration
   - Cursor will automatically restart the MCP server with the new environment variables

4. **Test Connection:**
   - After configuring and saving, wait a few seconds for Cursor to restart the MCP server
   - Test with: `search_my_sonarqube_projects` MCP tool in Cursor
   - If successful, you should see your projects listed
   - If "Not authorized" error persists, verify:
     - Token is correct and not expired (regenerate if needed)
     - Organization key matches your SonarCloud org exactly
     - For self-hosted: URL is correct and accessible
     - Environment variables are saved in Cursor's MCP settings (not just in your shell)

**Troubleshooting Docker Command Error:**

If you see this error when running the Docker command manually:
```
Exception: SONARQUBE_TOKEN environment variable or property must be set
```

**Solution:**
1. **Don't run the Docker command manually** - Cursor handles this automatically
2. The error occurs because environment variables aren't set in your shell
3. Configure the variables in **Cursor Settings > Tools & MCP > sonarqube**:
   - Click on the "sonarqube" MCP server
   - Add environment variables with actual values:
     - `SONARQUBE_TOKEN=your_actual_token_here`
     - `SONARQUBE_ORG=your_actual_org_key_here`
     - `SONARQUBE_HOST_URL=https://sonarcloud.io` (if needed)
4. Save the configuration
5. Cursor will automatically restart the MCP server with the new variables
6. Test the connection using MCP tools in Cursor (not the Docker command)

**If you must test manually** (not recommended), you would need to:
```bash
export SONARQUBE_TOKEN="your_token"
export SONARQUBE_ORG="your_org"
docker run -i --rm -e SONARQUBE_TOKEN -e SONARQUBE_ORG mcp/sonarqube
```

But this is unnecessary - just configure in Cursor and use the MCP tools directly.

**Security Notes:**
- **Never commit** `SONARQUBE_TOKEN` or `SONARQUBE_ORG` to the repository
- Store tokens in Cursor's secure environment variable configuration
- Tokens should be kept private and rotated periodically

### Analysis Scope

The SonarQube MCP integration analyzes the following directories:

- **`src/`** - Main source code
  - `src/agents/` - Workflow planner agent and tools
  - `src/api/` - FastAPI application and routers
  - `src/db/` - ClickHouse database integration
  - `src/crawlers/` - Web crawling components
  - `src/processors/` - Text processing pipeline
  - `src/enrichment/` - Data enrichment extractors
  - `src/quality/` - Quality filters and metrics
  - `src/pipeline/` - Pipeline orchestration

- **`dbt/`** - dbt models and transformations
  - `dbt/models/` - SQL models (staging, dimensions, facts)
  - `dbt/tests/` - Data quality tests

- **`tests/`** - Test suite
  - `tests/api/` - API integration tests
  - `tests/e2e/` - End-to-end tests
  - Unit tests for individual modules

### Available MCP Tools

The following SonarQube MCP tools are available in Cursor:

**Project Management:**
- `list_enterprises` - List available enterprises in SonarQube Cloud
- `search_my_sonarqube_projects` - List projects in your SonarQube organization
- `list_portfolios` - List enterprise portfolios

**Issue Management:**
- `search_sonar_issues_in_projects` - Search for issues in projects (by severity, file, etc.)
- `change_sonar_issue_status` - Change issue status (accept, false positive, reopen)

**Quality Metrics:**
- `get_component_measures` - Get quality metrics for components (bugs, code smells, vulnerabilities, coverage)
- `get_project_quality_gate_status` - Check quality gate status for a project
- `search_metrics` - Search for available metrics

**Rules & Configuration:**
- `show_rule` - Show detailed information about a SonarQube rule
- `list_rule_repositories` - List available rule repositories
- `list_quality_gates` - List available quality gates
- `list_languages` - List supported programming languages

**Source Code:**
- `get_raw_source` - Get source code as raw text from SonarQube
- `get_scm_info` - Get SCM (source control) information for files

**Webhooks:**
- `create_webhook` - Create a webhook for SonarQube organization or project
- `list_webhooks` - List all webhooks

### Usage

To run SonarQube analysis:

1. **Check Project Status:**
   ```python
   # Use MCP tool in Cursor
   search_my_sonarqube_projects()  # Find your project
   get_project_quality_gate_status(projectKey="your-project-key")  # Check quality gate
   ```

2. **Analyze Issues:**
   ```python
   # Search for issues by severity
   search_sonar_issues_in_projects(
       projects=["your-project-key"],
       severities=["BLOCKER", "CRITICAL", "MAJOR"]
   )
   ```

3. **Get Metrics:**
   ```python
   # Get component measures
   get_component_measures(
       projectKey="your-project-key",
       metricKeys=["bugs", "code_smells", "vulnerabilities", "coverage", "duplicated_lines_density"]
   )
   ```

4. **Before Merging:**
   - Run a scan to ensure no new critical issues
   - Check quality gate status
   - Review and address any blocker or critical issues

### Troubleshooting

**"Not authorized" Error:**
- Verify `SONARQUBE_TOKEN` is set correctly in Cursor MCP settings
- Ensure `SONARQUBE_ORG` matches your SonarCloud organization
- Check that the token has not expired
- Verify Docker is running (required for the MCP server)

**No Projects Found:**
- Ensure your SonarQube Cloud organization has projects configured
- Check that the project key matches your repository
- Verify you have access to the organization

## Development Setup

### Prerequisites

- Python 3.9+
- ClickHouse (via Docker)
- Docker (for SonarQube MCP server)
- Node.js (for dbt, if using dbt-core with Node.js dependencies)

### Initial Setup

1. Create virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start ClickHouse:
   ```bash
   ./scripts/start_clickhouse.sh
   ```

4. Load data:
   ```bash
   python -m src.db.load_to_clickhouse
   ```

5. Run dbt models:
   ```bash
   cd dbt && dbt run && dbt test
   ```

## Code Quality Checks

### Pre-commit Checks

Before committing code:

1. Run linter (if configured):
   ```bash
   # Add linting command here when configured
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

3. Check SonarQube (via MCP):
   - Use `search_sonar_issues_in_projects` to check for new issues
   - Ensure quality gate passes using `get_project_quality_gate_status`

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Document functions and classes with docstrings
- Keep functions focused and under 100 lines when possible

## Testing Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_enrichment.py

# Run with coverage
pytest --cov=src tests/
```

### Test Structure

- Unit tests: `tests/test_*.py`
- Integration tests: `tests/api/`
- End-to-end tests: `tests/e2e/`

## Pre-Release Checklist

Before preparing for demos or releases:

- [ ] Run full test suite: `pytest tests/`
- [ ] Run SonarQube MCP scan and check quality gate status
- [ ] Ensure no critical or blocker issues
- [ ] Review and address major code smells
- [ ] Update documentation if needed
- [ ] Verify API endpoints work correctly
- [ ] Check ClickHouse data is up to date


# SonarQube Setup Guide

This guide explains how to set up and run SonarQube analysis for the cleaning-web-corpus project.

## Prerequisites

1. **SonarCloud Account:**
   - Sign up at https://sonarcloud.io
   - Create or join an organization
   - Note your organization key

2. **SonarQube Token:**
   - Go to User Account > Security
   - Generate a new token
   - Save it securely (you'll need it for analysis)

3. **SonarScanner:**
   - Install SonarScanner (see installation instructions below)
   - Or use GitHub Actions (recommended for CI/CD)

## Project Configuration

The project includes two configuration files:

1. **`sonar-project.properties`** - Main SonarQube configuration
2. **`.sonarcloud.json`** - SonarCloud-specific configuration

### Configuration Details

**Source Directories:**
- `src/` - Main source code (agents, api, db, crawlers, processors, enrichment, quality, pipeline)
- `scripts/` - Utility scripts
- `tests/` - Test suite

**Exclusions:**
- `__pycache__/`, `*.pyc` - Python cache files
- `.venv/`, `venv/`, `env/` - Virtual environments
- `node_modules/` - Node.js dependencies
- `target/`, `build/`, `dist/` - Build artifacts
- `models/` - 3D model files (STL)
- `data/images/` - Image data
- `dbt/target/`, `dbt/logs/` - dbt artifacts

**Test Configuration:**
- Test directory: `tests/`
- Test patterns: `**/test_*.py`, `**/tests/**`

## Installation Methods

### Option 1: Local SonarScanner (for manual analysis)

1. **Install SonarScanner:**
   ```bash
   # macOS (using Homebrew)
   brew install sonar-scanner
   
   # Or download from:
   # https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/
   ```

2. **Set Environment Variables:**
   ```bash
   export SONAR_TOKEN="your_sonarcloud_token"
   export SONAR_ORG="your_organization_key"
   ```

3. **Run Analysis:**
   ```bash
   cd /path/to/cleaning-web-corpus
   sonar-scanner \
     -Dsonar.token=$SONAR_TOKEN \
     -Dsonar.organization=$SONAR_ORG \
     -Dsonar.host.url=https://sonarcloud.io
   ```

### Option 2: GitHub Actions (Recommended)

1. **Create GitHub Actions Workflow:**
   Create `.github/workflows/sonarcloud.yml`:

   ```yaml
   name: SonarCloud Analysis
   
   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main, develop ]
   
   jobs:
     sonarcloud:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0  # Shallow clones should be disabled for better analysis
         
         - name: Set up Python
           uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         
         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements.txt
             pip install pytest pytest-cov
         
         - name: Run tests with coverage
           run: |
             pytest tests/ --cov=src --cov-report=xml --cov-report=html -v
         
         - name: SonarCloud Scan
           uses: SonarSource/sonarcloud-github-action@master
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
             SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
   ```

2. **Configure GitHub Secrets:**
   - Go to your GitHub repository > Settings > Secrets and variables > Actions
   - Add `SONAR_TOKEN` secret with your SonarCloud token

3. **Update sonar-project.properties:**
   Add your organization key:
   ```properties
   sonar.organization=your_organization_key
   ```

### Option 3: Docker (Alternative)

```bash
docker run --rm \
  -v $(pwd):/usr/src \
  -w /usr/src \
  -e SONAR_TOKEN="your_token" \
  -e SONAR_ORG="your_org" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.host.url=https://sonarcloud.io
```

## Creating the Project in SonarCloud

1. **Go to SonarCloud:**
   - Visit https://sonarcloud.io
   - Log in with your GitHub/GitLab/Bitbucket account

2. **Create/Import Project:**
   - Click "Add Project" > "Analyze a new project"
   - Select your organization
   - Choose "Import from GitHub" (or your Git provider)
   - Select the `cleaning-web-corpus` repository
   - SonarCloud will generate a project key (e.g., `your-org_cleaning-web-corpus`)

3. **Update Configuration:**
   - Note the generated project key
   - Update `sonar-project.properties`:
     ```properties
     sonar.projectKey=your-org_cleaning-web-corpus
     sonar.organization=your-org
     ```

## Running Analysis

### First-Time Setup

1. **Get your project key from SonarCloud:**
   - After creating the project, copy the project key
   - Format: `organization_project-name`

2. **Update configuration:**
   ```bash
   # Edit sonar-project.properties
   sonar.projectKey=your-org_cleaning-web-corpus
   sonar.organization=your-org
   ```

3. **Run analysis:**
   ```bash
   sonar-scanner \
     -Dsonar.token=$SONAR_TOKEN \
     -Dsonar.organization=$SONAR_ORG \
     -Dsonar.host.url=https://sonarcloud.io
   ```

### Subsequent Runs

After the first analysis, you can run:
```bash
sonar-scanner
```
(If environment variables are set)

## Test Coverage (Optional but Recommended)

To include test coverage in SonarQube:

1. **Install pytest-cov:**
   ```bash
   pip install pytest pytest-cov
   ```

2. **Run tests with coverage:**
   ```bash
   pytest tests/ --cov=src --cov-report=xml --cov-report=html
   ```

3. **Update sonar-project.properties:**
   ```properties
   sonar.python.coverage.reportPaths=coverage.xml
   ```

4. **Run SonarScanner:**
   ```bash
   sonar-scanner
   ```

## Verifying Analysis

After running analysis:

1. **Check SonarCloud Dashboard:**
   - Go to https://sonarcloud.io
   - Navigate to your project
   - View quality metrics, issues, and coverage

2. **Check Quality Gate:**
   - The "Sonar way" quality gate will be applied automatically
   - Ensure it passes (green status)

3. **Review Issues:**
   - Check for bugs, vulnerabilities, and code smells
   - Review security hotspots

## Troubleshooting

**"Project not found" error:**
- Verify project key matches SonarCloud
- Check organization key is correct
- Ensure project exists in SonarCloud

**"Not authorized" error:**
- Verify token is correct and not expired
- Check token has proper permissions
- Regenerate token if needed

**Coverage not showing:**
- Ensure coverage.xml is generated
- Check sonar.python.coverage.reportPaths is set correctly
- Verify coverage report path is relative to project root

**Analysis takes too long:**
- Check exclusions are working (large directories excluded)
- Verify only source code is analyzed
- Consider excluding more build artifacts

## Next Steps

After successful analysis:

1. **Review Metrics:**
   - Check baseline metrics in `docs/QUALITY_REPORT.md`
   - Identify critical issues

2. **Set Up CI/CD:**
   - Configure GitHub Actions for automatic analysis
   - Add quality gate checks to PR workflow

3. **Address Issues:**
   - Start with blocker and critical issues
   - Work through major code smells
   - Improve test coverage

## References

- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [SonarScanner Documentation](https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/)
- [Python Analysis](https://docs.sonarcloud.io/enriching/test-coverage/python-test-coverage/)


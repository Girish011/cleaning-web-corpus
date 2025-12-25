# SonarQube Local Analysis Guide

## ⚠️ Important: Preview Mode Deprecated

**SonarQube preview mode is no longer supported** in SonarQube 8.0+ and SonarCloud. The error you'll see:

```
ERROR The preview mode, along with the 'sonar.analysis.mode' parameter, is no more supported.
```

## Solution: Use Local Static Analysis Tools

Since preview mode is deprecated, we use **local Python static analysis tools** for pre-commit checks:

- **pylint** - Code quality and style
- **flake8** - Style guide enforcement
- **mypy** - Type checking
- **bandit** - Security vulnerability scanning
- **safety** - Dependency vulnerability checking

## Running Local Analysis

### Quick Start

```bash
./scripts/run_local_analysis.sh
```

This script:
- ✅ Analyzes your code locally
- ✅ Checks for bugs, code smells, security issues
- ✅ Generates reports (JSON and text)
- ✅ Works offline (no SonarCloud connection needed)
- ✅ Doesn't conflict with Automatic Analysis

### What It Checks

1. **Code Quality (pylint):**
   - Code complexity
   - Style violations
   - Potential bugs
   - Best practices

2. **Style Guide (flake8):**
   - PEP 8 compliance
   - Line length
   - Import organization
   - Unused variables

3. **Type Safety (mypy):**
   - Type hints correctness
   - Type mismatches
   - Missing type annotations

4. **Security (bandit):**
   - SQL injection risks
   - Hardcoded secrets
   - Insecure functions
   - Cryptographic issues

5. **Dependencies (safety):**
   - Known vulnerabilities in packages
   - Outdated dependencies
   - Security advisories

## Installation

The script will auto-install tools if missing:

```bash
pip install pylint flake8 mypy bandit safety
```

Or install manually:

```bash
pip install -r requirements-dev.txt  # if you create one
```

## Workflow

### Recommended: Two-Tier Analysis

1. **Local Analysis (Before Committing):**
   ```bash
   ./scripts/run_local_analysis.sh
   ```
   - Quick feedback
   - Fix issues immediately
   - No SonarCloud needed

2. **SonarCloud Analysis (After Pushing):**
   - GitHub Actions runs automatically
   - Full SonarQube analysis
   - Results in SonarCloud dashboard
   - Quality gate enforcement

## Viewing Results

### Console Output
All tools print results to console with:
- Issue counts
- File locations
- Line numbers
- Severity levels

### JSON Reports
- `bandit-report.json` - Security issues
- `safety-report.json` - Dependency vulnerabilities

### Integration with IDE
For real-time feedback, install IDE extensions:
- **VS Code/Cursor:** Pylance, Python, SonarLint
- **PyCharm:** Built-in inspections

## Why This Approach?

### ✅ Advantages
- **Fast:** Runs locally, no network needed
- **Comprehensive:** Multiple tools cover different aspects
- **No Conflicts:** Doesn't interfere with SonarCloud
- **Pre-commit:** Catch issues before pushing
- **Free:** All tools are open-source

### ⚠️ Limitations
- Not exactly the same as SonarQube rules
- No centralized dashboard (use SonarCloud for that)
- Requires manual tool installation

## SonarCloud Integration

For full SonarQube analysis:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **GitHub Actions runs automatically:**
   - Full SonarQube analysis
   - Results uploaded to SonarCloud
   - Quality gate checked

3. **View in SonarCloud:**
   - https://sonarcloud.io/project/overview?id=Girish011_cleaning-web-corpus
   - Issues, metrics, coverage
   - Quality gate status

## Summary

| Analysis Type | Tool | When to Use |
|--------------|------|-------------|
| **Local Pre-commit** | `run_local_analysis.sh` | Before committing |
| **Cloud Analysis** | GitHub Actions + SonarCloud | After pushing |
| **Real-time** | IDE extensions (SonarLint) | While coding |

**Best Practice:**
- Use local analysis for quick checks
- Use SonarCloud for comprehensive analysis and tracking
- Use IDE extensions for real-time feedback

## Troubleshooting

### Tools Not Found
```bash
pip install pylint flake8 mypy bandit safety
```

### Too Many False Positives
- Configure tool settings in `.pylintrc`, `.flake8`, `mypy.ini`
- Add suppressions for known issues

### Slow Analysis
- Exclude large directories in tool configs
- Run specific tools individually:
  ```bash
  pylint src/
  flake8 src/
  ```

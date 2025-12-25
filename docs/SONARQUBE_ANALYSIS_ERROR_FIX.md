# SonarQube Analysis Error Fix

## Error Message

```
ERROR You are running manual analysis while Automatic Analysis is enabled. 
Please consider disabling one or the other.
```

## Cause

Your SonarCloud project has **Automatic Analysis** enabled (likely via GitHub Actions integration). SonarCloud doesn't allow both automatic and manual analysis to run simultaneously.

## Solutions

### Option 1: Disable Automatic Analysis (Recommended for Manual Analysis)

1. **Go to SonarCloud:**
   - Visit https://sonarcloud.io
   - Navigate to your project: `Girish011_cleaning-web-corpus`
   - Go to: **Project Settings** > **Analysis Method**

2. **Disable Automatic Analysis:**
   - Find "Automatic Analysis" section
   - Toggle it OFF or disable it
   - Save changes

3. **Run Manual Analysis Again:**
   ```bash
   ./scripts/run_sonarqube_analysis.sh
   ```

### Option 2: Use GitHub Actions (Recommended for CI/CD)

Instead of manual analysis, use the GitHub Actions workflow:

1. **Ensure GitHub Secrets are set:**
   - `SONAR_TOKEN`: Your SonarCloud token
   - `SONAR_PROJECT_KEY`: `Girish011_cleaning-web-corpus`
   - `SONAR_ORG`: `girish11` (or `girish011` - check which one is correct)

2. **Commit and push:**
   ```bash
   git add sonar-project.properties .github/workflows/sonarcloud.yml
   git commit -m "Add SonarQube configuration"
   git push origin main
   ```

3. **Check GitHub Actions:**
   - Go to: https://github.com/Girish011/cleaning-web-corpus/actions
   - The workflow will run automatically
   - Results will appear in SonarCloud

### Option 3: Use SonarCloud UI to Trigger Analysis

1. **Go to SonarCloud project:**
   - https://sonarcloud.io/project/overview?id=Girish011_cleaning-web-corpus

2. **Trigger from UI:**
   - Some SonarCloud projects allow triggering analysis from the UI
   - Look for "Run Analysis" or similar button

## Verify Organization Name

**Important:** I noticed a discrepancy:
- In `sonar-project.properties`: `sonar.organization=girish11`
- In your terminal: `export SONAR_ORG=girish011`

Make sure these match! Check your SonarCloud organization name:
- Go to https://sonarcloud.io
- Check your organization name (should be either `girish11` or `girish011`)

Update `sonar-project.properties` if needed:
```properties
sonar.organization=girish011  # or girish11, whichever is correct
```

## Recommended Approach

For this project, **Option 2 (GitHub Actions)** is recommended because:
- Automatic analysis on every push/PR
- No need to run manually
- Consistent with CI/CD best practices
- Results are always up to date

If you need manual analysis for testing, use **Option 1** to temporarily disable automatic analysis.


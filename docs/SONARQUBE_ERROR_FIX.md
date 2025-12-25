# SonarQube Analysis Error Fix

## Error Message

```
ERROR You are running manual analysis while Automatic Analysis is enabled. 
Please consider disabling one or the other.
```

## Root Cause

Your SonarCloud project has **Automatic Analysis** enabled (via GitHub Actions integration). SonarCloud doesn't allow both automatic and manual analysis simultaneously.

## Solutions

### Solution 1: Disable Automatic Analysis (For Manual Testing)

1. **Go to SonarCloud:**
   - Visit https://sonarcloud.io
   - Navigate to: Project `Girish011_cleaning-web-corpus`
   - Go to: **Project Settings** > **Analysis Method**

2. **Disable Automatic Analysis:**
   - Find "Automatic Analysis" toggle
   - Turn it OFF
   - Save changes

3. **Run Manual Analysis:**
   ```bash
   export SONAR_TOKEN="your_token"
   export SONAR_ORG="girish011"
   ./scripts/run_sonarqube_analysis.sh
   ```

### Solution 2: Use GitHub Actions (Recommended)

Since you have GitHub Actions configured, use that instead:

1. **Verify GitHub Secrets:**
   - Go to: https://github.com/Girish011/cleaning-web-corpus/settings/secrets/actions
   - Ensure these secrets exist:
     - `SONAR_TOKEN`: Your SonarCloud token
     - `SONAR_PROJECT_KEY`: `Girish011_cleaning-web-corpus`
     - `SONAR_ORG`: `girish011` (or `girish11` - check which is correct)

2. **Commit and Push:**
   ```bash
   git add sonar-project.properties .github/workflows/sonarcloud.yml
   git commit -m "Add SonarQube configuration"
   git push origin main
   ```

3. **Check Results:**
   - GitHub Actions will run automatically
   - View: https://github.com/Girish011/cleaning-web-corpus/actions
   - Results: https://sonarcloud.io/project/overview?id=Girish011_cleaning-web-corpus

### Solution 3: Wait for Automatic Analysis

If Automatic Analysis is enabled, it will run automatically when you push to GitHub. You don't need to run manual analysis.

## Organization Name Fix

**Fixed:** Updated `sonar-project.properties`:
- Changed `sonar.organization=girish11` → `sonar.organization=girish011`
- This matches your terminal export: `export SONAR_ORG=girish011`

## Recommendation

**Use GitHub Actions (Solution 2)** - It's the recommended approach because:
- ✅ Automatic analysis on every push/PR
- ✅ No manual steps needed
- ✅ Results always up to date
- ✅ Integrated with your workflow

Manual analysis is mainly useful for:
- Testing configuration before pushing
- One-off analysis without committing
- Debugging analysis issues

## Next Steps

1. **If using GitHub Actions:**
   - Just commit and push - analysis runs automatically
   - Check GitHub Actions tab for status
   - View results in SonarCloud dashboard

2. **If you need manual analysis:**
   - Disable Automatic Analysis in SonarCloud settings
   - Then run `./scripts/run_sonarqube_analysis.sh`


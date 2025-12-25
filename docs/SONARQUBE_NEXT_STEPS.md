# SonarQube Next Steps

## ✅ Configuration Complete

You have successfully configured:
- ✅ `sonar-project.properties` with project key: `Girish011_cleaning-web-corpus`
- ✅ Organization: `girish11`
- ✅ GitHub secrets added (SONAR_TOKEN, SONAR_PROJECT_KEY, SONAR_ORG)
- ✅ GitHub Actions workflow created

## Next Steps

### Step 1: Verify Project Exists in SonarCloud

1. **Go to SonarCloud:**
   - Visit https://sonarcloud.io
   - Log in with your GitHub account
   - Navigate to organization: `girish11`

2. **Check if project exists:**
   - Look for project: `cleaning-web-corpus`
   - Project key should be: `Girish011_cleaning-web-corpus`
   - If project doesn't exist, create it:
     - Click "Add Project" > "Analyze a new project"
     - Select "Import from GitHub"
     - Choose repository: `Girish011/cleaning-web-corpus`
     - SonarCloud will automatically set up the project

### Step 2: Verify GitHub Secrets

Ensure these secrets are set in GitHub:

1. **Go to GitHub Repository:**
   - https://github.com/Girish011/cleaning-web-corpus
   - Settings > Secrets and variables > Actions

2. **Verify these secrets exist:**
   - `SONAR_TOKEN`: Your SonarCloud token
   - `SONAR_PROJECT_KEY`: `Girish011_cleaning-web-corpus`
   - `SONAR_ORG`: `girish11`

### Step 3: Run First Analysis

You have two options:

#### Option A: Trigger via GitHub Actions (Recommended)

1. **Commit and push your changes:**
   ```bash
   git add sonar-project.properties .github/workflows/sonarcloud.yml
   git commit -m "Add SonarQube configuration and GitHub Actions workflow"
   git push origin main  # or your branch name
   ```

2. **Check GitHub Actions:**
   - Go to: https://github.com/Girish011/cleaning-web-corpus/actions
   - You should see "SonarCloud Analysis" workflow running
   - Wait for it to complete (usually 2-5 minutes)

3. **View Results:**
   - Once complete, click on the workflow run
   - Check the "SonarCloud Scan" step for any errors
   - Visit SonarCloud dashboard to see results

#### Option B: Run Locally (Alternative)

1. **Install SonarScanner:**
   ```bash
   # macOS
   brew install sonar-scanner
   
   # Or download from:
   # https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/
   ```

2. **Set environment variables:**
   ```bash
   export SONAR_TOKEN="your_sonarcloud_token"
   export SONAR_ORG="girish11"
   ```

3. **Run analysis:**
   ```bash
   cd /Users/girish11/cleaning-web-corpus
   sonar-scanner \
     -Dsonar.token=$SONAR_TOKEN \
     -Dsonar.organization=$SONAR_ORG \
     -Dsonar.host.url=https://sonarcloud.io
   ```

### Step 4: Verify Analysis Results

1. **Check SonarCloud Dashboard:**
   - Go to: https://sonarcloud.io/project/overview?id=Girish011_cleaning-web-corpus
   - You should see:
     - Quality gate status
     - Bugs, vulnerabilities, code smells counts
     - Test coverage (if tests were run)
     - Duplicated code percentage

2. **Check Quality Gate:**
   - Should show "Passed" (green) or "Failed" (red)
   - Review any failing conditions

### Step 5: Retrieve Metrics via MCP

Once analysis completes:

1. **Refresh MCP Connection:**
   - The MCP connection might need a refresh
   - Try using the MCP tools in Cursor:
     - `search_my_sonarqube_projects` - Should now show your project
     - `get_component_measures` - Retrieve metrics

2. **Update Quality Report:**
   - Use MCP tools to get actual metrics
   - Update `docs/QUALITY_REPORT.md` with baseline values

## Troubleshooting

### GitHub Actions Fails

**"Project not found" error:**
- Verify project exists in SonarCloud
- Check `SONAR_PROJECT_KEY` secret matches exactly: `Girish011_cleaning-web-corpus`
- Check `SONAR_ORG` secret matches: `girish11`

**"Not authorized" error:**
- Verify `SONAR_TOKEN` is correct and not expired
- Regenerate token in SonarCloud if needed
- Ensure token has proper permissions

**Workflow not triggering:**
- Check branch name matches workflow trigger (main, master, develop)
- Verify workflow file is in `.github/workflows/`
- Check GitHub Actions is enabled for the repository

### MCP Connection Issues

**"Not connected" error:**
- Restart Cursor to refresh MCP connection
- Verify environment variables in Cursor Settings > Tools & MCP > sonarqube:
  - `SONARQUBE_TOKEN` is set
  - `SONARQUBE_ORG` is set to `girish11`
- Check Docker is running (required for MCP server)

### Analysis Takes Too Long

- Check exclusions in `sonar-project.properties` are working
- Verify large directories (data/images, models, dbt/target) are excluded
- Consider excluding more build artifacts if needed

## Quick Checklist

- [ ] Project exists in SonarCloud (https://sonarcloud.io)
- [ ] GitHub secrets configured (SONAR_TOKEN, SONAR_PROJECT_KEY, SONAR_ORG)
- [ ] GitHub Actions workflow file exists (`.github/workflows/sonarcloud.yml`)
- [ ] Committed and pushed configuration files
- [ ] GitHub Actions workflow ran successfully
- [ ] Analysis results visible in SonarCloud dashboard
- [ ] MCP connection working (can retrieve projects)
- [ ] Baseline metrics retrieved and documented

## Expected Timeline

- **First analysis:** 2-5 minutes
- **Subsequent analyses:** 1-3 minutes
- **Results available:** Immediately after analysis completes

## Next Phase

After successful analysis:
1. Review baseline metrics in SonarCloud
2. Retrieve metrics via MCP tools
3. Update `docs/QUALITY_REPORT.md` with actual values
4. Proceed with T71: Classify issues and map to tasks


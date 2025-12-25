# Pre-Commit File Review

## ❌ Files to EXCLUDE from commit

### 1. Analysis Reports & Logs
- `bandit-report.json` - Security analysis report (generated)
- `MUJOCO_LOG.TXT` - Log file (should be in .gitignore)
- `test-reports/` - Test reports (already in .gitignore)

### 2. Generated Evaluation Data
- `data/evaluation/coverage_matrix.csv` - Generated data
- `data/evaluation/dataset_stats.json` - Generated data
- `data/evaluation/dataset_stats.txt` - Generated data
- `data/evaluation/visualizations/*.png` - Generated images (large files)
- `data/seeds_discovered.txt` - Generated data
- `data/seeds_discovered_history.json` - Generated data

**Recommendation:** These should be in `.gitignore` or committed only if they're reference/example data.

### 3. Temporary Documentation Files
These appear to be temporary notes/work-in-progress:
- `GRASP_FIXES.md` - Temporary fix notes
- `LOGGING_IMPROVEMENTS.md` - Temporary notes
- `PICK_PLACE_FIXES.md` - Temporary fix notes
- `SMOOTH_MOTION_IMPROVEMENTS.md` - Temporary notes
- `TESTING.md` - Temporary notes
- `RUN_SONARQUBE_ANALYSIS.md` - Temporary guide (already have better docs)

**Recommendation:** Delete or move to `docs/` if they contain valuable information.

### 4. Build Artifacts
- `dbt/target/` - dbt build artifacts (should be in .gitignore)
- `dbt/logs/` - dbt logs (should be in .gitignore)

### 5. Other Generated Files
- `run_commands.txt` - Temporary command log

## ✅ Files to INCLUDE in commit

### 1. Source Code (All Modified)
- All `src/` files - Code quality fixes
- All `tests/` files - Test code
- `requirements.txt` - Dependencies

### 2. Configuration Files
- `.github/workflows/sonarcloud.yml` - CI/CD workflow
- `sonar-project.properties` - SonarQube config
- `docker-compose.clickhouse.yml` - Docker config
- `pytest.ini` - Test configuration
- `configs/default.yaml` - App configuration
- `.gitignore` - Updated ignore rules

### 3. Documentation (Keep)
- `docs/CODE_QUALITY_ISSUES.md` - Quality report
- `docs/VERIFICATION_REPORT.md` - Verification results
- `docs/SONARQUBE_*.md` - SonarQube setup guides
- `docs/DEV_WORKFLOW.md` - Developer workflow
- `docs/QUALITY_REPORT.md` - Quality metrics
- All other `docs/*.md` files - Project documentation

### 4. Scripts
- `scripts/run_local_analysis.sh` - Local analysis script
- `scripts/run_sonarqube_analysis.sh` - SonarQube script
- `scripts/run_sonarqube_preview.sh` - Preview script (deprecated but kept for reference)
- All other `scripts/*.py` and `scripts/*.sh` - Utility scripts

### 5. Project Structure
- `dbt/` project files (models, profiles.yml, dbt_project.yml) - But NOT target/ or logs/
- `data/seeds.txt` - Seed URLs (if modified intentionally)
- `models/` - 3D model files (if needed for robot simulation)

## 📝 Recommendations

### Update .gitignore
Add these patterns:
```
# Analysis reports
bandit-report.json
safety-report.json
*.log
MUJOCO_LOG.TXT

# Generated evaluation data
data/evaluation/*.csv
data/evaluation/*.json
data/evaluation/*.txt
data/evaluation/visualizations/*.png
data/seeds_discovered.txt
data/seeds_discovered_history.json

# Temporary notes
GRASP_FIXES.md
LOGGING_IMPROVEMENTS.md
PICK_PLACE_FIXES.md
SMOOTH_MOTION_IMPROVEMENTS.md
TESTING.md
RUN_SONARQUBE_ANALYSIS.md
run_commands.txt
```

### Clean Up Before Commit
1. Remove temporary markdown files or move valuable content to `docs/`
2. Ensure `.gitignore` excludes generated files
3. Review if evaluation data should be committed (usually no)

## 🎯 Recommended Commit Strategy

**Option 1: Clean commit (Recommended)**
- Only commit source code, configs, docs, and scripts
- Exclude all generated files and temporary notes

**Option 2: Include evaluation data**
- If evaluation data is needed as reference, commit it
- But exclude large image files



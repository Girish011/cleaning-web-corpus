# Code Quality Issues Summary

## Analysis Date: 2025-12-25

## Overview

Local static analysis found issues across multiple categories. This document summarizes findings and provides a plan for fixes.

## Issue Categories

### 1. Style Issues (Most Common)

**Trailing Whitespace (W293):**
- **Count:** Hundreds of instances
- **Severity:** Low
- **Files Affected:** Most Python files
- **Fix:** Remove trailing whitespace from all lines

**Line Too Long (E501):**
- **Count:** ~100+ instances
- **Severity:** Low
- **Files Affected:** Multiple files, especially `src/robot/mujoco_simulator.py`
- **Fix:** Break long lines (max 120 characters)

**Unused Imports (F401):**
- **Count:** ~10 instances
- **Severity:** Low
- **Fix:** Remove unused imports

**Blank Lines at End of File (W391):**
- **Count:** ~5 instances
- **Severity:** Low
- **Fix:** Remove extra blank lines at end of files

### 2. Code Quality Issues

**Bare Except Clauses (E722):**
- **Count:** ~10 instances
- **Severity:** Medium
- **Files:** `src/robot/mujoco_simulator.py`
- **Fix:** Specify exception types (e.g., `except Exception:`)

**Unused Variables (F841):**
- **Count:** ~5 instances
- **Severity:** Low
- **Fix:** Remove or use variables

**F-strings Without Placeholders (F541):**
- **Count:** ~10 instances
- **Severity:** Low
- **Fix:** Use regular strings instead of f-strings

### 3. Security Issues (Bandit)

**SQL Injection Risks (B608):**
- **Count:** 28 instances
- **Severity:** Medium (but using escape functions)
- **Files:** `src/agents/tools/`, `src/api/routers/`
- **Status:** Using `_escape_sql_string()` - likely safe, but consider parameterized queries
- **Fix Priority:** Medium - Review and potentially refactor to parameterized queries

**Weak Hash Functions (B324):**
- **Count:** 3 instances
- **Severity:** High (but for non-security purposes)
- **Files:** `src/crawlers/pipelines.py`, `src/enrichment/llm_extractor.py`
- **Status:** Used for hashing URLs/cache keys, not security
- **Fix:** Add `usedforsecurity=False` parameter

**HuggingFace Unsafe Downloads (B615):**
- **Count:** 4 instances
- **Severity:** Medium
- **Files:** `src/enrichment/captioner.py`, `src/quality/alignment.py`
- **Fix:** Pin model revisions

**Try/Except Pass (B110):**
- **Count:** 7 instances
- **Severity:** Low
- **Files:** `src/robot/mujoco_simulator.py`
- **Fix:** Add logging or specific exception handling

### 4. Dependency Vulnerabilities

**Scrapy CVE-2017-14158:**
- **Severity:** Medium (old CVE from 2017)
- **Status:** Likely not critical for this use case
- **Fix:** Consider upgrading Scrapy or accepting risk

## Fix Priority

### High Priority (Security & Critical Bugs)
1. ✅ Fix weak hash functions (add `usedforsecurity=False`)
2. ✅ Review SQL injection risks (consider parameterized queries)
3. ✅ Pin HuggingFace model revisions

### Medium Priority (Code Quality)
1. ✅ Fix bare except clauses
2. ✅ Remove unused imports/variables
3. ✅ Fix f-strings without placeholders

### Low Priority (Style)
1. ✅ Remove trailing whitespace (automated)
2. ✅ Fix line length issues
3. ✅ Remove blank lines at end of files

## Automated Fixes

Many style issues can be fixed automatically using:
- `autopep8` - Auto-format Python code
- `black` - Opinionated code formatter
- `isort` - Sort imports

## Next Steps

1. **Run automated formatter:**
   ```bash
   pip install autopep8 black isort
   autopep8 --in-place --recursive src/
   black src/
   isort src/
   ```

2. **Fix security issues manually:**
   - Add `usedforsecurity=False` to hash functions
   - Review SQL queries
   - Pin HuggingFace model versions

3. **Review and fix code quality issues:**
   - Replace bare except clauses
   - Remove unused code

4. **Re-run analysis:**
   ```bash
   ./scripts/run_local_analysis.sh
   ```

5. **Commit and push:**
   - GitHub Actions will run SonarQube analysis
   - Review results in SonarCloud


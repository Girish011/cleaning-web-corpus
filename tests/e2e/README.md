# End-to-End (E2E) Tests

## Overview

E2E tests validate the complete workflow from API request to response, including all data quality improvements implemented in Phase 10.

## Test Coverage

### Data Quality Improvements (Phase 10)
- **T53**: Step quality filtering - Only actionable steps are returned
- **T54**: Method relevance selection - Method selection prioritizes relevance over document count
- **T55**: Source document deduplication - Each document appears only once
- **T56**: Step relevance filtering - Steps match query intent
- **T57**: Minimum step count - Workflows have at least 3 steps
- **T58**: Corpus step extraction - Better extraction at source (tested indirectly)

### API Endpoints
- `POST /api/v1/plan_workflow` - Full workflow planning
- `GET /api/v1/search_procedures` - Procedure search
- `GET /api/v1/stats/coverage` - Coverage statistics

### Error Handling
- Validation errors (400/422)
- Not found errors (404)
- Service unavailable errors (503)
- Internal server errors (500)

## Running Tests

### Run all E2E tests:
```bash
pytest tests/e2e/ -v
```

### Run specific test:
```bash
pytest tests/e2e/test_full_workflow.py::TestFullWorkflowE2E::test_e2e_workflow_planning_with_quality_improvements -v
```

### Run with coverage:
```bash
pytest tests/e2e/ --cov=src.api --cov=src.agents -v
```

## Test Structure

Tests use mocks for ClickHouse and the agent to ensure:
- Fast execution
- Deterministic results
- No external dependencies
- Easy debugging

For integration with real ClickHouse, see `tests/api/` integration tests.

## Expected Behavior

### Workflow Planning
- Returns 3+ actionable steps
- Method selection prioritizes relevance (spot_clean for stains)
- Source documents are deduplicated
- Steps are relevant to query intent
- No informational steps included

### Procedure Search
- Returns matching procedures with steps and tools
- Pagination works correctly
- Filters apply correctly

### Coverage Stats
- Returns complete coverage summary
- Distributions are accurate
- Gaps are identified correctly
- Coverage matrices are computed correctly


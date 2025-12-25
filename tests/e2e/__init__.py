"""
End-to-end tests for the Cleaning Workflow Planner API.

Tests the full workflow from API request to response, including:
- All three endpoints (/plan_workflow, /search_procedures, /stats/coverage)
- Data quality improvements (step filtering, method selection, etc.)
- Error handling and edge cases
- Response schema validation
"""


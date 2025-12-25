# Testing Data Quality Improvements via Swagger UI

## Quick Start

1. **Install missing dependency:**
   ```bash
   pip install httpx
   ```

2. **Start the FastAPI server:**
   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Open Swagger UI:**
   - Navigate to: http://localhost:8000/docs

## Testing Data Quality Improvements

### T53: Step Quality Filtering

**Test Query:**
```json
{
  "query": "Remove red wine stain from wool carpet"
}
```

**Expected Results:**
- ✅ All steps should contain action verbs (blot, apply, mix, rinse, etc.)
- ✅ No informational steps like "Health Benefits: Carpets can trap..."
- ✅ No steps longer than 200 words
- ✅ All steps have confidence >= 0.5

**Check:**
- Look at `workflow.steps[]` in the response
- Verify each step's `description` contains action verbs
- Verify no steps mention "benefits", "prolongs", "extends"

### T54: Method Relevance Selection

**Test Query:**
```json
{
  "query": "Remove red wine stain from wool carpet"
}
```

**Expected Results:**
- ✅ `scenario.cleaning_method` should be `"spot_clean"` (not `"vacuum"`)
- ✅ Even if vacuum has more documents, spot_clean should be selected for stain removal

**Check:**
- Look at `scenario.cleaning_method` in the response
- Should be `"spot_clean"` for stain removal queries
- Check `metadata.method_selection.selection_reason` for relevance-based selection

**Compare with:**
```json
{
  "query": "Regular maintenance vacuuming of carpet"
}
```
- This should select `"vacuum"` (maintenance query)

### T55: Source Document Deduplication

**Test Query:**
```json
{
  "query": "Remove stain from carpet"
}
```

**Expected Results:**
- ✅ Each `document_id` appears only once in `source_documents[]`
- ✅ No duplicate documents even if referenced by multiple steps

**Check:**
- Look at `source_documents[]` in the response
- Count unique `document_id` values
- Should equal the length of the array (no duplicates)

### T56: Step Relevance Filtering

**Test Query:**
```json
{
  "query": "Remove red wine stain from wool carpet"
}
```

**Expected Results:**
- ✅ Steps should contain stain-related keywords (blot, remove, treat, clean, rinse)
- ✅ No general maintenance steps like "Health Benefits" or "Prolongs Carpet Life"
- ✅ Steps should match query intent (stain removal, not general maintenance)

**Check:**
- Look at `workflow.steps[]` in the response
- Verify steps contain stain-related keywords
- Verify no maintenance-focused steps

### T57: Minimum Step Count

**Test Query:**
```json
{
  "query": "Remove stain from rare surface type"
}
```

**Expected Results:**
- ✅ If insufficient steps found, should return 404 with message "Insufficient steps found"
- ✅ If steps found, should have at least 3 steps
- ✅ System should try to find additional steps from similar scenarios

**Check:**
- For valid queries: `workflow.steps[]` should have length >= 3
- For invalid queries: Should get 404 error with "Insufficient steps" message

### T58: Corpus Step Extraction (Indirect)

**Note:** T58 improvements are at the corpus extraction level. Test indirectly by:
- Verifying steps returned are actionable (not informational)
- Checking step quality in responses

## Test Scenarios

### Scenario 1: Stain Removal (Tests T53, T54, T56)
```json
POST /api/v1/plan_workflow
{
  "query": "Remove red wine stain from wool carpet",
  "constraints": {
    "no_bleach": true,
    "gentle_only": true
  }
}
```

**Validations:**
- Method: `spot_clean` (T54)
- Steps: 3+ actionable steps (T53, T57)
- Step relevance: Stain-related keywords (T56)
- Documents: Unique document_ids (T55)

### Scenario 2: Maintenance Query (Tests T54)
```json
POST /api/v1/plan_workflow
{
  "query": "Regular maintenance vacuuming of carpet"
}
```

**Validations:**
- Method: `vacuum` (T54 - maintenance keyword)
- Steps: 3+ steps (T57)

### Scenario 3: Search Procedures (Tests T53 indirectly)
```json
GET /api/v1/search_procedures?surface_type=carpets_floors&dirt_type=stain&include_steps=true
```

**Validations:**
- Steps in procedures should be actionable
- No informational steps

### Scenario 4: Coverage Stats
```json
GET /api/v1/stats/coverage?include_matrix=true&matrix_type=full
```

**Validations:**
- Returns complete coverage summary
- Distributions are accurate
- Gaps are identified

## Error Cases to Test

### Insufficient Steps (T57)
```json
POST /api/v1/plan_workflow
{
  "query": "Clean impossible surface with impossible dirt"
}
```

**Expected:** 404 with "Insufficient steps found" message

### Invalid Parameters
```json
GET /api/v1/search_procedures?surface_type=invalid_type
```

**Expected:** 400 with validation error

## Tips

1. **Use Swagger UI's "Try it out" feature** - Click on any endpoint, then "Try it out"
2. **Check response structure** - Expand the response to see all fields
3. **Compare responses** - Test same query multiple times to verify consistency
4. **Check logs** - Server logs will show step filtering, method selection, etc.

## Quick Validation Checklist

For any workflow response, verify:
- [ ] At least 3 steps (T57)
- [ ] All steps contain action verbs (T53)
- [ ] No informational steps (T53, T56)
- [ ] Method matches query intent (T54)
- [ ] Source documents are unique (T55)
- [ ] Steps are relevant to query (T56)


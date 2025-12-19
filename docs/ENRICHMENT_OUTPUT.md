# Enrichment Output - Where to Check Results

## ✅ Test Fix Applied

The bullet point pattern issue has been **fixed**. The pattern now handles leading whitespace correctly.

**Fix**: Updated regex pattern from `^[-•*]\s+(.+)$` to `^\s*[-•*]\s+(.+)$` to allow leading whitespace before bullet points.

**Verification**: The test now passes - bullet points are correctly extracted.

## 📁 Output File Location

After running the text processor, enriched documents are written to:

```
data/processed/cleaning_docs.jsonl
```

This is a JSONL file (one JSON object per line) containing all processed and enriched documents.

## 🔍 How to Check Enriched Output

### Quick Check (Command Line)

```bash
# View first document with enriched fields
head -1 data/processed/cleaning_docs.jsonl | python3 -m json.tool | grep -A 10 "surface_type\|tools\|steps"

# Count documents with tools extracted
python3 -c "
import json
count = 0
with open('data/processed/cleaning_docs.jsonl', 'r') as f:
    for line in f:
        doc = json.loads(line)
        if doc.get('tools'):
            count += 1
print(f'Documents with tools: {count}')
"

# Count documents with steps extracted
python3 -c "
import json
count = 0
with open('data/processed/cleaning_docs.jsonl', 'r') as f:
    for line in f:
        doc = json.loads(line)
        if doc.get('steps'):
            count += 1
print(f'Documents with steps: {count}')
"
```

### View Full Enriched Document

```bash
# Pretty print first document
head -1 data/processed/cleaning_docs.jsonl | python3 -m json.tool

# View specific fields
python3 -c "
import json
with open('data/processed/cleaning_docs.jsonl', 'r') as f:
    doc = json.loads(f.readline())
    print('URL:', doc.get('url'))
    print('Surface Type:', doc.get('surface_type'))
    print('Dirt Type:', doc.get('dirt_type'))
    print('Cleaning Method:', doc.get('cleaning_method'))
    print('Tools:', doc.get('tools'))
    print('Steps:', doc.get('steps'))
    print('Extraction Metadata:', doc.get('extraction_metadata'))
"
```

### Python Script to Analyze Enrichment

```python
import json
from collections import Counter

# Analyze enrichment coverage
surface_types = Counter()
dirt_types = Counter()
tools_found = Counter()
steps_count = 0
total_docs = 0

with open('data/processed/cleaning_docs.jsonl', 'r') as f:
    for line in f:
        doc = json.loads(line)
        total_docs += 1
        
        surface_types[doc.get('surface_type', 'unknown')] += 1
        dirt_types[doc.get('dirt_type', 'unknown')] += 1
        
        if doc.get('tools'):
            for tool in doc['tools']:
                tools_found[tool] += 1
        
        if doc.get('steps'):
            steps_count += 1

print(f"Total documents: {total_docs}")
print(f"\nSurface types distribution:")
for st, count in surface_types.most_common():
    print(f"  {st}: {count}")

print(f"\nDirt types distribution:")
for dt, count in dirt_types.most_common():
    print(f"  {dt}: {count}")

print(f"\nMost common tools:")
for tool, count in tools_found.most_common(10):
    print(f"  {tool}: {count}")

print(f"\nDocuments with steps: {steps_count}/{total_docs} ({steps_count/total_docs*100:.1f}%)")
```

## 📊 Enriched Fields in Output

Each document in `data/processed/cleaning_docs.jsonl` now includes:

### Required Fields (Always Present)
- `surface_type`: Enhanced surface type (8 categories)
- `dirt_type`: Enhanced dirt type (8 categories)  
- `cleaning_method`: Enhanced cleaning method (8 methods)

### New Fields (Phase 4.1)
- `tools`: List of cleaning tools/equipment (e.g., `["vinegar", "microfiber_cloth"]`)
- `steps`: List of cleaning procedure steps (e.g., `["Mix solution", "Apply to stain"]`)
- `tools_detailed`: Tools with confidence scores
- `steps_detailed`: Steps with order and confidence
- `extraction_metadata`: Extraction method and confidence scores

### Example Output Structure

```json
{
  "url": "https://example.com/clean-carpet",
  "title": "How to Clean Carpet Stains",
  "main_text": "...",
  "surface_type": "carpets_floors",
  "dirt_type": "stain",
  "cleaning_method": "spot_clean",
  "tools": ["vinegar", "baking_soda", "microfiber_cloth", "spray_bottle"],
  "steps": [
    "Blot excess liquid with paper towel",
    "Mix equal parts vinegar and water",
    "Spray solution onto stain",
    "Let sit for 10 minutes"
  ],
  "tools_detailed": [
    {"name": "vinegar", "confidence": 0.85},
    {"name": "microfiber_cloth", "confidence": 0.90}
  ],
  "steps_detailed": [
    {"step": "...", "order": 1, "confidence": 0.85},
    {"step": "...", "order": 2, "confidence": 0.80}
  ],
  "extraction_metadata": {
    "extraction_method": "rule_based",
    "confidence": {
      "surface_type": 0.90,
      "dirt_type": 0.85,
      "cleaning_method": 0.75,
      "tools": 0.82,
      "steps": 0.78
    }
  }
}
```

## 🧪 Running Tests

After the fix, all tests should pass:

```bash
# Run all enrichment tests
pytest tests/test_enrichment.py -v

# Run specific test that was failing
pytest tests/test_enrichment.py::TestRuleBasedExtractor::test_extract_steps_bullet_points -v
```

## 📝 Notes

- **File Format**: JSONL (one JSON object per line)
- **File Location**: `data/processed/cleaning_docs.jsonl`
- **File Size**: Can be large depending on number of processed documents
- **Encoding**: UTF-8

## 🔄 Re-running Processing

To regenerate enriched output:

```bash
python -m src.processors.text_processor
```

This will:
1. Read from `data/raw/seed_pages.jsonl`
2. Apply quality filters
3. Apply enrichment (Phase 4.1)
4. Write to `data/processed/cleaning_docs.jsonl`

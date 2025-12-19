# Repetition Filter Troubleshooting Guide

## Problem: All URLs Failing with High Word Repetition

When you see all URLs being filtered out with high word repetition ratios (e.g., 0.45-0.78), here's what to do:

## Step 1: Diagnose the Issue

### Analyze a Failed URL

```bash
# Analyze a specific URL to see what's causing high repetition
python scripts/analyze_repetition_failures.py --url "https://www.maidbrigade.com/blog/green-cleaning-tips/how-to-clean-pillows-and-bedding/"
```

This will show you:
- What words are being repeated most
- If it's common words (the, a, an) causing the issue
- If boilerplate content is included
- Sample of the extracted text

### Analyze All Failures

```bash
# Analyze all failed URLs (shows first 3 in detail)
python scripts/analyze_repetition_failures.py --all
```

## Step 2: Identify the Root Cause

Common causes of high word repetition:

### 1. **Boilerplate Content**
- Navigation menus
- Footer content
- Cookie notices
- Privacy policy links
- Social media buttons

**Solution**: Improve text extraction (trafilatura should handle this, but may need tuning)

### 2. **Common Words Over-counting**
- Articles (the, a, an) appearing frequently
- Prepositions (in, on, at, to, for)
- Conjunctions (and, or, but)

**Solution**: Adjust the word repetition calculation to exclude common words

### 3. **Legitimate Repetition**
- Technical terms repeated (e.g., "cleaning", "stain", "carpet")
- This is actually normal for domain-specific content

**Solution**: Increase the threshold or adjust the calculation

### 4. **Short Text with Repetition**
- Very short articles with repeated phrases
- This might be legitimate but looks like repetition

**Solution**: Check if text is too short (repetition check should skip short texts)

## Step 3: Apply Fixes

### Fix Option 1: Adjust Threshold (Quick Fix)

If the repetition is legitimate (domain terms), increase the threshold:

```yaml
# configs/default.yaml
quality:
  text:
    max_word_repetition_ratio: 0.3  # Increase from 0.2 to 0.3
    # Or even higher if needed:
    # max_word_repetition_ratio: 0.4
```

### Fix Option 2: Exclude Common Words (Better Fix)

Modify the word repetition calculation to exclude common English words:

**File**: `src/quality/text_filters.py`

In `_check_word_repetition()`, add common word exclusion:

```python
# Common words to exclude from repetition calculation
COMMON_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
    'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
}

def _check_word_repetition(self, text: str) -> Tuple[float, Dict]:
    words = self._split_words(text)
    
    # Filter out common words
    content_words = [w for w in words if w not in COMMON_WORDS]
    
    if len(content_words) < 5:
        return 0.0, {"word_repetition_ratio": 0.0, "reason": "too_few_content_words"}
    
    # Count word frequencies (only for content words)
    word_counts = {}
    for word in content_words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Rest of the calculation...
```

### Fix Option 3: Improve Text Extraction

If boilerplate is the issue, improve text extraction:

```python
# In text_processor.py, process_url()
# Add options to trafilatura for better extraction
main_text = trafilatura.extract(
    html,
    include_comments=False,
    include_tables=False,
    include_images=False,
    include_links=False,
    favor_recall=False,  # Favor precision over recall
    favor_precision=True
)
```

### Fix Option 4: Pre-filter Boilerplate

Add a boilerplate removal step before repetition check:

```python
def remove_boilerplate(text: str) -> str:
    """Remove common boilerplate patterns."""
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line_lower = line.lower().strip()
        # Skip common boilerplate patterns
        if any(pattern in line_lower for pattern in [
            'cookie', 'privacy policy', 'terms of service',
            'subscribe', 'newsletter', 'follow us', 'share this'
        ]):
            continue
        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)
```

## Step 4: Test the Fix

After applying a fix:

```bash
# Test with a single URL
python scripts/test_repetition_integration.py --url "https://www.maidbrigade.com/blog/green-cleaning-tips/how-to-clean-pillows-and-bedding/"

# Run full processor
python -m src.processors.text_processor

# Check results
echo "Processed URLs:"
wc -l data/processed/cleaning_docs.jsonl
```

## Recommended Action Plan

1. **First**: Run analysis script to understand the issue
   ```bash
   python scripts/analyze_repetition_failures.py --url <one-failed-url>
   ```

2. **If it's common words**: Implement Fix Option 2 (exclude common words)

3. **If it's boilerplate**: Implement Fix Option 3 or 4 (improve extraction)

4. **If it's legitimate repetition**: Implement Fix Option 1 (adjust threshold)

5. **Test**: Verify the fix works with your data

## Quick Decision Tree

```
High word repetition detected
│
├─ Is it common words (the, a, an, etc.)?
│  └─ YES → Exclude common words from calculation (Fix Option 2)
│
├─ Is it boilerplate (navigation, footer, etc.)?
│  └─ YES → Improve text extraction (Fix Option 3 or 4)
│
└─ Is it legitimate domain terms (cleaning, stain, etc.)?
   └─ YES → Increase threshold (Fix Option 1)
```

## Current Configuration

Check your current settings:

```bash
python << EOF
from src.config import get_config
config = get_config()
print(f"Max word repetition ratio: {config.quality.text.max_word_repetition_ratio}")
print(f"Max char repetition ratio: {config.quality.text.max_char_repetition_ratio}")
print(f"Max n-gram repetition: {config.quality.text.max_ngram_repetition}")
EOF
```

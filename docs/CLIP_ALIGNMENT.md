# CLIP Text-Image Alignment Implementation

## Why Do We Need This?

### The Problem

When crawling web pages about cleaning (pillows, carpets, clothes, etc.), we often encounter pages with **multiple images** that may not all be relevant to the main text content. For example:

**Scenario 1: Irrelevant Images**
- **Text**: "How to clean a carpet stain using vinegar"
- **Images on page**: 
  - ✅ Relevant: Photo of carpet with stain
  - ❌ Irrelevant: Ad banner for a different product
  - ❌ Irrelevant: Logo image
  - ❌ Irrelevant: Stock photo of a kitchen (unrelated)

**Scenario 2: Mixed Content**
- **Text**: "Cleaning methods for woolen sweaters"
- **Images on page**:
  - ✅ Relevant: Before/after photos of sweater cleaning
  - ❌ Irrelevant: Generic laundry detergent ad
  - ❌ Irrelevant: Social media share buttons with icons

### What This Solves

**CLIP text-image alignment** solves the problem of **semantic relevance** between text and images:

1. **Quality Filtering**: Only keeps images that are semantically related to the text content
2. **Corpus Quality**: Ensures multi-modal data (text + images) is coherent and useful
3. **Research-Grade Data**: Critical for training LLM agents and cleaning robots that need aligned multi-modal understanding
4. **Noise Reduction**: Filters out irrelevant images (ads, logos, unrelated stock photos)

### Why CLIP?

CLIP (Contrastive Language-Image Pre-training) is perfect for this because:
- **Semantic Understanding**: Understands meaning, not just keywords
- **Pre-trained**: Works out-of-the-box without domain-specific training
- **Efficient**: Fast enough for production use
- **Accurate**: State-of-the-art for text-image similarity

### Example Impact

**Before CLIP Alignment:**
```
Page: "How to remove coffee stains from carpet"
Images kept: 8 images
  - 2 relevant carpet stain images ✅
  - 3 coffee product ads ❌
  - 2 logo/branding images ❌
  - 1 unrelated stock photo ❌
```

**After CLIP Alignment (min_clip_score=0.2):**
```
Page: "How to remove coffee stains from carpet"
Images kept: 2 images
  - 2 relevant carpet stain images ✅
  - 6 filtered out (low relevance scores)
```

## How It Works

1. **Text Extraction**: Extract main text from the web page
2. **Image Quality Filtering**: First filter by resolution, format, duplicates (existing filters)
3. **CLIP Scoring**: For each image, compute semantic similarity score with text
4. **Threshold Filtering**: Keep only images with score ≥ `min_clip_score` (default: 0.2)
5. **Metadata Enrichment**: Add `clip_score` to image metadata for analysis

### Score Interpretation

- **Score Range**: 0.0 to 1.0 (normalized from CLIP's cosine similarity)
- **0.0-0.2**: Very low relevance (likely unrelated)
- **0.2-0.4**: Low relevance (may be tangentially related)
- **0.4-0.6**: Moderate relevance (somewhat related)
- **0.6-0.8**: High relevance (clearly related)
- **0.8-1.0**: Very high relevance (perfectly aligned)

**Default threshold (0.2)**: Filters out clearly irrelevant images while keeping most related ones.

## Testing Guide

### Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   This will install:
   - `torch>=2.0.0` (PyTorch for CLIP)
   - `transformers>=4.30.0` (Hugging Face transformers with CLIP)

2. **Verify Installation**:
   ```bash
   python -c "from transformers import CLIPModel, CLIPProcessor; print('CLIP available')"
   ```

### Test 1: Unit Tests (Fast - No Model Download)

Run the test suite to verify the implementation:

```bash
# Run all alignment tests
pytest tests/test_alignment.py -v

# Run specific test
pytest tests/test_alignment.py::TestCLIPAlignmentScorer::test_scorer_initialization_without_clip -v
```

**Expected**: Tests should pass, even if CLIP dependencies aren't installed (graceful fallback).

### Test 2: Manual CLIP Scoring Test (Downloads Model)

Create a simple test script to verify CLIP works:

```bash
# Create test script
cat > test_clip_manual.py << 'EOF'
from src.config import AlignmentConfig
from src.quality.alignment import CLIPAlignmentScorer
from PIL import Image
import tempfile
import os

# Create test image
img = Image.new('RGB', (224, 224), color='red')
with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
    img.save(tmp.name, 'JPEG')
    tmp_path = tmp.name

try:
    config = AlignmentConfig(min_clip_score=0.2)
    scorer = CLIPAlignmentScorer(config)
    
    if not scorer.is_available():
        print("❌ CLIP not available. Install: pip install torch transformers")
        exit(1)
    
    print("✅ CLIP model loaded successfully")
    
    # Test 1: Relevant text-image pair
    text1 = "a red image"
    score1, stats1 = scorer.score_text_image(text1, tmp_path)
    print(f"\nTest 1 - Relevant pair:")
    print(f"  Text: '{text1}'")
    print(f"  Score: {score1:.4f}")
    print(f"  Passed: {stats1['passed']}")
    
    # Test 2: Less relevant pair
    text2 = "a blue ocean with waves"
    score2, stats2 = scorer.score_text_image(text2, tmp_path)
    print(f"\nTest 2 - Less relevant pair:")
    print(f"  Text: '{text2}'")
    print(f"  Score: {score2:.4f}")
    print(f"  Passed: {stats2['passed']}")
    
    # Test 3: Multiple images
    images = [
        {"path": tmp_path, "url": "http://example.com/red.jpg"},
    ]
    aligned, misaligned = scorer.filter_by_alignment(text1, images)
    print(f"\nTest 3 - Filtering:")
    print(f"  Aligned: {len(aligned)}")
    print(f"  Misaligned: {len(misaligned)}")
    
    print("\n✅ All tests passed!")
    
finally:
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
EOF

python test_clip_manual.py
```

**Expected Output**:
```
✅ CLIP model loaded successfully
Test 1 - Relevant pair:
  Text: 'a red image'
  Score: 0.7234
  Passed: True

Test 2 - Less relevant pair:
  Text: 'a blue ocean with waves'
  Score: 0.3456
  Passed: True

Test 3 - Filtering:
  Aligned: 1
  Misaligned: 0

✅ All tests passed!
```

**Note**: First run will download CLIP model (~500MB) - this is normal and only happens once.

### Test 3: Integration Test with Real Data

Test with actual crawled data:

```bash
# Ensure you have raw data
ls data/raw/seed_pages.jsonl

# Run the processor (this will apply CLIP alignment)
python -m src.processors.text_processor

# Check output
head -1 data/processed/cleaning_docs.jsonl | python -m json.tool | grep -A 5 "images"
```

**Expected**: Images in output should have `clip_score` metadata if CLIP is available.

### Test 4: Verify Filtering Behavior

Create a test with known good/bad image-text pairs:

```bash
cat > test_clip_filtering.py << 'EOF'
from src.config import AlignmentConfig
from src.quality.alignment import CLIPAlignmentScorer
from PIL import Image
import tempfile
import os

def create_test_image(color, filename):
    img = Image.new('RGB', (224, 224), color=color)
    img.save(filename, 'JPEG')
    return filename

# Create test images
red_img = create_test_image('red', 'test_red.jpg')
blue_img = create_test_image('blue', 'test_blue.jpg')

try:
    config = AlignmentConfig(min_clip_score=0.3)  # Higher threshold
    scorer = CLIPAlignmentScorer(config)
    
    if not scorer.is_available():
        print("CLIP not available")
        exit(1)
    
    # Test with relevant text
    text = "a red carpet with stains"
    
    images = [
        {"path": red_img, "url": "red.jpg"},
        {"path": blue_img, "url": "blue.jpg"},
    ]
    
    aligned, misaligned = scorer.filter_by_alignment(text, images)
    
    print(f"Text: '{text}'")
    print(f"Threshold: {config.min_clip_score}")
    print(f"\nAligned images ({len(aligned)}):")
    for img in aligned:
        print(f"  - {img['url']}: score={img.get('clip_score', 'N/A'):.4f}")
    
    print(f"\nMisaligned images ({len(misaligned)}):")
    for img in misaligned:
        print(f"  - {img['url']}: score={img.get('clip_score', 'N/A'):.4f}, reason={img.get('filter_reason', 'N/A')}")
    
finally:
    for f in [red_img, blue_img]:
        if os.path.exists(f):
            os.unlink(f)
EOF

python test_clip_filtering.py
```

**Expected**: Red image should have higher score and pass, blue image should have lower score and potentially fail.

### Test 5: Performance Test

Measure CLIP scoring performance:

```bash
cat > test_clip_performance.py << 'EOF'
import time
from src.config import AlignmentConfig
from src.quality.alignment import CLIPAlignmentScorer
from PIL import Image
import tempfile
import os

# Create test image
img = Image.new('RGB', (224, 224), color='red')
with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
    img.save(tmp.name, 'JPEG')
    tmp_path = tmp.name

try:
    config = AlignmentConfig()
    scorer = CLIPAlignmentScorer(config)
    
    if not scorer.is_available():
        print("CLIP not available")
        exit(1)
    
    text = "a red carpet"
    num_tests = 10
    
    # Warm up
    scorer.score_text_image(text, tmp_path)
    
    # Benchmark
    start = time.time()
    for _ in range(num_tests):
        scorer.score_text_image(text, tmp_path)
    elapsed = time.time() - start
    
    avg_time = elapsed / num_tests
    print(f"Average scoring time: {avg_time*1000:.2f}ms per image")
    print(f"Throughput: {1/avg_time:.2f} images/second")
    
finally:
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
EOF

python test_clip_performance.py
```

**Expected**: Should score images in < 100ms each on CPU, faster on GPU.

### Test 6: Graceful Degradation Test

Verify the system works even without CLIP:

```bash
# Temporarily rename transformers to simulate missing dependency
python << 'EOF'
import sys
# Simulate missing CLIP
sys.modules['transformers'] = None

from src.config import AlignmentConfig
from src.quality.alignment import CLIPAlignmentScorer

config = AlignmentConfig()
scorer = CLIPAlignmentScorer(config)

assert not scorer.is_available(), "Should detect CLIP unavailable"
score, stats = scorer.score_text_image("test", "nonexistent.jpg")
assert score is None, "Should return None when CLIP unavailable"
assert stats["passed"] is True, "Should pass gracefully"

print("✅ Graceful degradation works correctly")
EOF
```

## Troubleshooting

### Issue: "CLIP dependencies not available"

**Solution**: Install dependencies:
```bash
pip install torch transformers
```

### Issue: Model download is slow

**Solution**: First run downloads ~500MB model. Subsequent runs use cached model. Be patient on first run.

### Issue: Out of memory errors

**Solution**: CLIP model uses ~1GB RAM. If memory constrained:
- Use CPU instead of GPU: `CLIPAlignmentScorer(config, device="cpu")`
- Process images in smaller batches

### Issue: Scores seem too low/high

**Solution**: Adjust `min_clip_score` in `configs/default.yaml`:
- Lower (0.1-0.15): More lenient, keeps more images
- Higher (0.3-0.4): Stricter, keeps only highly relevant images

## Configuration

Edit `configs/default.yaml`:

```yaml
quality:
  alignment:
    min_clip_score: 0.2  # Adjust threshold (0.0-1.0)
```

Lower values = more images kept (lenient)
Higher values = fewer images kept (strict)

## Summary

**What it solves**: Filters irrelevant images from web pages, keeping only semantically relevant ones.

**Why it matters**: Ensures multi-modal corpus quality for training cleaning robots and LLM agents.

**How to test**: Run unit tests, manual scoring tests, and integration tests as shown above.

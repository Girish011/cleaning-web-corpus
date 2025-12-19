# Phase 4.3: Image Caption Generation (BLIP-2) - Implementation Summary

## ✅ Implementation Complete

Phase 4.3 has been successfully implemented! This adds automatic image caption generation using BLIP-2 to enrich the multi-modal corpus with detailed image descriptions.

## What Was Implemented

### 1. BLIP-2 Captioner (`src/enrichment/captioner.py`)

**Features:**
- Uses BLIP-2 (Bootstrapping Language-Image Pre-training) for image captioning
- Better than CLIP for detailed descriptions
- Supports multiple BLIP-2 models:
  - `Salesforce/blip2-opt-2.7b` (default, smaller, faster)
  - `Salesforce/blip2-opt-6.7b` (larger, better quality)
  - `Salesforce/blip2-flan-t5-xl` (alternative architecture)
- Automatic device detection (GPU/CPU)
- Batch processing support
- Custom prompts for guided captioning
- Graceful fallback if BLIP-2 unavailable

**How it works:**
1. Loads BLIP-2 model (downloads on first use)
2. Processes images through BLIP-2
3. Generates descriptive captions
4. Adds captions to image metadata
5. Falls back gracefully if model unavailable

### 2. Configuration Updates

**config.py:**
- Added `CaptioningConfig` class with all settings

**default.yaml:**
```yaml
enrichment:
  captioning:
    enable: true
    model: "Salesforce/blip2-opt-2.7b"
    device: "auto"  # "auto", "cuda", "cpu"
    max_length: 50
    min_confidence: 0.5
    prompt: null  # Optional prompt (e.g., "a photo of")
```

### 3. Integration

**text_processor.py:**
- Captioner initialized once (model loading is expensive)
- Captions generated after CLIP alignment
- Only captions images that passed all quality filters
- Captions added to image metadata

### 4. Tests (`tests/test_captioning.py`)
- Comprehensive test suite covering:
  - Configuration validation
  - Caption generation (with/without BLIP-2)
  - Batch processing
  - Error handling
  - Different models and devices

## Output Schema

Images in the output now include caption fields:

```json
{
  "images": [
    {
      "url": "https://example.com/image.jpg",
      "path": "data/images/example_com/abc123/def456.jpg",
      "width": 800,
      "height": 600,
      "caption": "A beige carpet with a dark red wine stain in the center",
      "caption_metadata": {
        "caption": "A beige carpet with a dark red wine stain in the center",
        "model": "Salesforce/blip2-opt-2.7b",
        "prompt": "a photo of",
        "max_length": 50,
        "generated_at": "2024-01-15T10:30:00Z",
        "device": "cuda"
      }
    }
  ]
}
```

## Usage

### Basic Usage

Captioning is **automatically enabled** by default. Just run:

```bash
python -m src.processors.text_processor
```

All images that pass quality filters will get captions.

### Disable Captioning

Edit `configs/default.yaml`:
```yaml
enrichment:
  captioning:
    enable: false
```

### Use Different Model

```yaml
enrichment:
  captioning:
    model: "Salesforce/blip2-opt-6.7b"  # Larger, better quality
```

### Use Custom Prompt

```yaml
enrichment:
  captioning:
    prompt: "a detailed photo showing"  # Guide caption style
```

### Force CPU Usage

```yaml
enrichment:
  captioning:
    device: "cpu"  # Use CPU instead of GPU
```

## Model Comparison

| Model | Size | Speed | Quality | Memory |
|-------|------|-------|---------|--------|
| `blip2-opt-2.7b` | Small | Fast | Good | ~6GB |
| `blip2-opt-6.7b` | Large | Slow | Excellent | ~12GB |
| `blip2-flan-t5-xl` | Medium | Medium | Good | ~8GB |

**Recommendation**: Start with `blip2-opt-2.7b` for faster processing, upgrade to `blip2-opt-6.7b` for better quality.

## Performance

- **First run**: Downloads model (~5-10GB) - only happens once
- **GPU (CUDA)**: ~200-500ms per image
- **CPU**: ~2-5 seconds per image
- **Batch processing**: More efficient for multiple images

## Dependencies

BLIP-2 uses:
- `torch>=2.0.0` (already in requirements)
- `transformers>=4.30.0` (already in requirements)
- `accelerate>=0.20.0` (recommended, improves performance)

**Install accelerate (optional but recommended):**
```bash
pip install accelerate
```

## Testing

### Test Captioner

```bash
# Run captioning tests
pytest tests/test_captioning.py -v
```

### Manual Test

```bash
python3 -c "
from src.enrichment.captioner import BLIP2Captioner
from PIL import Image
import tempfile

# Create test image
img = Image.new('RGB', (224, 224), color='red')
with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
    img.save(tmp.name, 'JPEG')
    tmp_path = tmp.name

try:
    captioner = BLIP2Captioner()
    if captioner.is_available():
        caption, metadata = captioner.generate_caption(tmp_path)
        print(f'✅ Caption: {caption}')
    else:
        print('⚠️  BLIP-2 not available (install dependencies)')
finally:
    import os
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
"
```

## Troubleshooting

### Issue: "BLIP-2 dependencies not available"

**Solution**: Dependencies are already in requirements.txt. Just ensure they're installed:
```bash
pip install torch transformers accelerate
```

### Issue: Model download is slow

**Solution**: First run downloads ~5-10GB model. Be patient. Subsequent runs use cached model.

### Issue: Out of memory errors

**Solutions**:
1. Use smaller model: `blip2-opt-2.7b` instead of `blip2-opt-6.7b`
2. Use CPU: `device: "cpu"` (slower but uses less memory)
3. Process fewer images at once

### Issue: Captions are generic

**Solutions**:
1. Use larger model: `blip2-opt-6.7b`
2. Use custom prompt: `prompt: "a detailed photo showing"`
3. Increase max_length: `max_length: 100`

## Example Captions

**Input Image**: Carpet with stain

**Caption**: "A beige carpet with a dark red wine stain in the center"

**Input Image**: Pillow being cleaned

**Caption**: "A person vacuuming a white pillow on a bed"

**Input Image**: Cleaning supplies

**Caption**: "A collection of cleaning supplies including spray bottles, cloths, and brushes on a counter"

## Integration with Pipeline

Captioning happens **after**:
1. Image quality filtering (resolution, format, duplicates)
2. CLIP text-image alignment

This ensures we only caption:
- High-quality images
- Images relevant to the text content

## Files Created/Modified

### New Files
- `src/enrichment/captioner.py` - BLIP-2 captioner implementation
- `tests/test_captioning.py` - Comprehensive test suite
- `docs/PHASE4_3_IMPLEMENTATION.md` - This document

### Modified Files
- `src/config.py` - Added CaptioningConfig
- `configs/default.yaml` - Added captioning settings
- `src/processors/text_processor.py` - Integrated captioning
- `src/enrichment/__init__.py` - Exported BLIP2Captioner
- `requirements.txt` - Added accelerate recommendation

## Next Steps

- Fine-tune BLIP-2 on cleaning domain (optional)
- Add caption quality scoring
- Support for video captioning (future)

## Notes

- **Model Size**: BLIP-2 models are large (~5-10GB). First download takes time.
- **GPU Recommended**: Much faster on GPU. CPU works but is slower.
- **Batch Processing**: More efficient for multiple images.
- **Graceful Fallback**: Works even if BLIP-2 unavailable (skips captioning).

# Phase 4.3: BLIP-2 Captioning Setup Guide

## Quick Setup

### 1. Install Dependencies

BLIP-2 uses transformers (already in requirements), but you may want to install accelerate for better performance:

```bash
pip install accelerate
```

**Note**: `torch` and `transformers` are already in requirements.txt, so they should be installed.

### 2. Verify Installation

```bash
python3 -c "
from src.enrichment.captioner import BLIP2Captioner
captioner = BLIP2Captioner()
print('✅ BLIP2Captioner initialized')
print(f'Available: {captioner.is_available()}')
"
```

**Expected Output:**
- If BLIP-2 available: `Available: True` (after model downloads)
- If not available: `Available: False` (will skip captioning gracefully)

### 3. First Run (Model Download)

On first use, BLIP-2 will download the model (~5-10GB). This only happens once:

```bash
python -m src.processors.text_processor
```

**First run output:**
```
Loading BLIP-2 model: Salesforce/blip2-opt-2.7b on cuda
Downloading model files... (this may take a few minutes)
BLIP-2 model loaded successfully
```

### 4. Check Captions in Output

```bash
# View captions in processed data
python3 -c "
import json
with open('data/processed/cleaning_docs.jsonl', 'r') as f:
    for line in f:
        doc = json.loads(line)
        images = doc.get('images', [])
        if images:
            print(f'URL: {doc.get(\"url\", \"unknown\")}')
            for img in images[:2]:  # First 2 images
                caption = img.get('caption')
                if caption:
                    print(f'  ✅ Caption: {caption}')
                else:
                    print(f'  ⚠️  No caption (BLIP-2 may not be available)')
            break
"
```

## Configuration

### Enable/Disable Captioning

Edit `configs/default.yaml`:

```yaml
enrichment:
  captioning:
    enable: true  # Set to false to disable
```

### Change Model

```yaml
enrichment:
  captioning:
    model: "Salesforce/blip2-opt-6.7b"  # Larger, better quality
```

### Use CPU Instead of GPU

```yaml
enrichment:
  captioning:
    device: "cpu"  # Force CPU usage
```

### Custom Prompt

```yaml
enrichment:
  captioning:
    prompt: "a detailed photo showing"  # Guide caption style
```

## Performance Tips

1. **Use GPU if available**: Much faster (~10x)
2. **Use smaller model**: `blip2-opt-2.7b` is faster than `blip2-opt-6.7b`
3. **Batch processing**: Already implemented, processes multiple images efficiently
4. **Disable if not needed**: Set `enable: false` to skip captioning

## Troubleshooting

### "ModuleNotFoundError: No module named 'PIL'"

**Solution**: Install Pillow:
```bash
pip install Pillow
```

### "BLIP-2 dependencies not available"

**Solution**: Install transformers and torch:
```bash
pip install torch transformers
```

### Model download fails

**Solutions**:
1. Check internet connection
2. Try again (downloads can be interrupted)
3. Manually download model (see Hugging Face docs)

### Out of memory

**Solutions**:
1. Use smaller model: `blip2-opt-2.7b`
2. Use CPU: `device: "cpu"`
3. Process fewer images at once

### Captions are None

**Check**:
1. Is captioning enabled? (`enable: true`)
2. Is BLIP-2 available? (check logs)
3. Do images have valid paths?
4. Are images passing quality filters?

## Example Workflow

```bash
# 1. Ensure dependencies installed
pip install -r requirements.txt
pip install accelerate  # Optional but recommended

# 2. Run processor (will download model on first run)
python -m src.processors.text_processor

# 3. Check output
python3 -c "
import json
with open('data/processed/cleaning_docs.jsonl', 'r') as f:
    doc = json.loads(f.readline())
    for img in doc.get('images', []):
        if img.get('caption'):
            print(f'Image: {img.get(\"url\", \"unknown\")}')
            print(f'Caption: {img[\"caption\"]}')
            break
"
```

## Model Options

| Model | Size | Best For |
|-------|------|----------|
| `Salesforce/blip2-opt-2.7b` | Small | Fast processing, good quality |
| `Salesforce/blip2-opt-6.7b` | Large | Best quality, slower |
| `Salesforce/blip2-flan-t5-xl` | Medium | Alternative architecture |

**Default**: `blip2-opt-2.7b` (good balance of speed and quality)

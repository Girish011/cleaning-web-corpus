# KenLM Perplexity Filter Setup Guide

## Overview

The perplexity filter uses KenLM language models to detect gibberish and low-quality text. Perplexity measures how "surprised" a language model is by the text - lower perplexity indicates higher quality.

## What is Perplexity?

- **Low perplexity (50-500)**: High-quality, predictable text
- **Medium perplexity (500-1000)**: Acceptable quality text
- **High perplexity (>1000)**: Potentially gibberish, spam, or very low-quality text

## Installation

### Step 1: Install KenLM Python Package

```bash
pip install kenlm
```

Or if that doesn't work:

```bash
pip install https://github.com/kpu/kenlm/archive/master.zip
```

**Note**: KenLM requires C++ compilation. On some systems, you may need:
- `g++` compiler
- `cmake`
- `boost` libraries

### Step 2: Download or Train a Language Model

You have two options:

#### Option A: Use a Pre-trained Model (Recommended)

Download a pre-trained English language model:

1. **Hugging Face Models**:
   - Visit: https://huggingface.co/models?search=kenlm
   - Download a model (look for `.arpa` or `.bin` files)
   - Example: https://huggingface.co/edugp/kenlm

2. **Common Crawl Models**:
   - Large models trained on Common Crawl data
   - Usually available as `.arpa` or `.bin` files

3. **Place the model file** in your project:
   ```bash
   mkdir -p models
   # Download model to models/ directory
   # Example: models/en.arpa or models/en.bin
   ```

#### Option B: Train Your Own Model

If you have domain-specific text, you can train a model:

```bash
# Install KenLM tools
git clone https://github.com/kpu/kenlm.git
cd kenlm
mkdir build && cd build
cmake ..
make -j4

# Train a model from your text corpus
./bin/lmplz -o 3 < your_corpus.txt > model.arpa

# Convert to binary format (faster loading)
./bin/build_binary model.arpa model.bin
```

## Configuration

### Step 1: Update Config File

Edit `configs/default.yaml`:

```yaml
quality:
  text:
    # ... other settings ...
    enable_perplexity_filter: true
    kenlm_model_path: "models/en.arpa"  # Path to your model file
    max_perplexity: 1000.0  # Adjust based on your needs
    min_text_length_for_perplexity: 20
```

### Step 2: Model Path Options

The model path can be:
- **Relative**: `"models/en.arpa"` (relative to project root)
- **Absolute**: `"/path/to/model.arpa"`

### Step 3: Adjust Threshold

The `max_perplexity` threshold depends on your use case:

- **Strict (50-200)**: Only very high-quality text passes
- **Moderate (200-500)**: Good quality text passes
- **Lenient (500-1000)**: Most legitimate text passes, filters only gibberish
- **Very Lenient (>1000)**: Only extreme gibberish is filtered

**Recommendation**: Start with `1000.0` and adjust based on your data.

## Testing

### Test Without Model (Graceful Fallback)

The filter works even without a model - it just skips the perplexity check:

```python
from src.config import get_config
from src.quality.text_filters import TextQualityFilter

config = get_config()
filter_instance = TextQualityFilter(config.quality.text)

text = "This is a test sentence."
result = filter_instance.filter(text)
# Will pass (perplexity check skipped if model not available)
```

### Test With Model

```python
from src.config import get_config, TextQualityConfig
from src.quality.text_filters import TextQualityFilter

config = TextQualityConfig(
    min_words=10,
    max_words=1000,
    enable_perplexity_filter=True,
    kenlm_model_path="models/en.arpa",  # Your model path
    max_perplexity=1000.0
)
filter_instance = TextQualityFilter(config.quality.text)

# Good quality text
good_text = "This is a comprehensive cleaning guide with detailed instructions."
result = filter_instance.check_perplexity(good_text)
print(f"Perplexity: {result[1].get('perplexity')}")
print(f"Passed: {result[0]}")

# Potentially gibberish text
bad_text = "asdfghjkl qwertyuiop zxcvbnm random words without meaning"
result = filter_instance.check_perplexity(bad_text)
print(f"Perplexity: {result[1].get('perplexity')}")
print(f"Passed: {result[0]}")
```

## Troubleshooting

### Issue: "kenlm not available"

**Solution**: Install KenLM:
```bash
pip install kenlm
```

If installation fails, you may need system dependencies:
- Ubuntu/Debian: `sudo apt-get install build-essential cmake libboost-all-dev`
- macOS: `brew install cmake boost`

### Issue: "KenLM model file not found"

**Solution**: 
1. Check the path in `configs/default.yaml`
2. Ensure the file exists
3. Use absolute path if relative path doesn't work

### Issue: "Failed to load KenLM model"

**Solution**:
1. Verify the model file is valid (`.arpa` or `.bin` format)
2. Check file permissions
3. Try converting `.arpa` to `.bin` for faster loading:
   ```bash
   build_binary model.arpa model.bin
   ```

### Issue: Perplexity values seem wrong

**Solution**:
- Different models have different perplexity ranges
- Adjust `max_perplexity` threshold based on your model
- Test with known good/bad text to calibrate

## Performance Considerations

- **Binary models (`.bin`)**: Load faster, use less memory
- **ARPA models (`.arpa`)**: Text format, slower to load
- **Model size**: Larger models = better accuracy but slower
- **Caching**: The model is loaded once and reused

## Integration

The perplexity filter is automatically integrated into the text processing pipeline:

```python
# In text_processor.py, it's called automatically:
filter_result = text_filter.filter(main_text)
# This includes perplexity check if model is available
```

## Disabling the Filter

To disable perplexity filtering:

```yaml
quality:
  text:
    enable_perplexity_filter: false
```

Or set `kenlm_model_path: null` in the config.

## Example Model Sources

1. **Hugging Face**: https://huggingface.co/models?search=kenlm
2. **Common Crawl**: Pre-trained models on large web corpora
3. **Domain-specific**: Train on your own corpus for better domain matching

## Next Steps

1. Install KenLM: `pip install kenlm`
2. Download a pre-trained model
3. Update `configs/default.yaml` with model path
4. Test with your data
5. Adjust `max_perplexity` threshold as needed

The filter will gracefully skip if the model is not available, so you can use it optionally.

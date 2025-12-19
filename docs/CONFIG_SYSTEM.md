# Configuration System

## Overview

The configuration system uses **Pydantic v2** for type-safe, validated configuration management. This provides:

- ✅ **Type Safety** - Catch configuration errors at load time
- ✅ **Validation** - Ensure all values are within valid ranges
- ✅ **IDE Support** - Autocomplete and type hints
- ✅ **Defaults** - Sensible defaults for all fields
- ✅ **Documentation** - Field descriptions available

## Usage

### Basic Usage

```python
from src.config import get_config

# Load config (cached singleton)
config = get_config()

# Type-safe access
min_words = config.quality.text.min_words  # int
log_level = config.logging.level  # Literal["DEBUG", "INFO", ...]
```

### Loading from Custom Path

```python
from src.config import load_config
import pathlib

custom_config = load_config(pathlib.Path("configs/custom.yaml"))
```

### Reloading Config

```python
from src.config import reload_config

# Force reload (clears cache)
config = reload_config()
```

## Configuration Structure

### Project Config
```yaml
project:
  name: "cleaning-corpus"
  version: "0.2.0"
```

### Crawler Config
```yaml
crawler:
  seeds_file: "data/seeds.txt"
  download_images: true
  max_images_per_page: 20
  respect_robots: true
  delay_seconds: 1.0
```

### Quality Config
```yaml
quality:
  text:
    min_words: 500
    max_words: 50000
    min_avg_word_length: 3.0
    language: "en"
  image:
    min_resolution: [224, 224]
    max_aspect_ratio: 3.0
    allowed_formats: ["jpg", "jpeg", "png", "webp"]
  alignment:
    min_clip_score: 0.2
```

### Processing Config
```yaml
processing:
  batch_size: 100
  num_workers: 4
```

### Logging Config
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
```

## Validation Rules

### Text Quality
- `min_words >= 1`
- `max_words >= min_words`
- `min_avg_word_length >= 0.0`

### Image Quality
- `min_resolution` must be `[width, height]` with positive values
- `max_aspect_ratio > 0.0`

### Alignment
- `min_clip_score` must be between `0.0` and `1.0`

### Logging
- `level` must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Error Handling

Invalid configurations raise `ValidationError` with detailed error messages:

```python
from pydantic import ValidationError
from src.config import load_config

try:
    config = load_config(pathlib.Path("invalid.yaml"))
except ValidationError as e:
    print(f"Config validation failed: {e}")
```

## Testing

Run the config tests:

```bash
pytest tests/test_config.py -v
```

Or use the validation test script:

```bash
python scripts/test_config_validation.py
```

## Migration from JSON

The old `config.json` has been migrated to `configs/default.yaml`. The new system:

1. **Backward Compatible** - All existing config values work
2. **Type Safe** - Access via attributes instead of dict keys
3. **Validated** - Invalid values caught at load time
4. **Extensible** - Easy to add new fields with validation

### Old Way (dict access)
```python
min_words = CONFIG.get("quality", {}).get("text", {}).get("min_words", 500)
```

### New Way (type-safe)
```python
min_words = config.quality.text.min_words  # int, validated
```

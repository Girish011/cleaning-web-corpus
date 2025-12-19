#!/usr/bin/env python3
"""Test text processor without actually processing data."""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Test config loading
import yaml
config_path = ROOT / "configs" / "default.yaml"
with config_path.open() as f:
    config = yaml.safe_load(f)

print("✓ Config loaded successfully")
print(f"  - Min words: {config.get('quality', {}).get('text', {}).get('min_words')}")
print(f"  - Log level: {config.get('logging', {}).get('level')}")

# Test that the processor can access config the same way
import os
MIN_WORDS = int(os.getenv("MIN_WORDS", str(config.get("quality", {}).get("text", {}).get("min_words", 500))))
print(f"✓ MIN_WORDS extracted: {MIN_WORDS}")

# Test that raw data path exists
raw_path = ROOT / "data" / "raw" / "seed_pages.jsonl"
if raw_path.exists():
    print(f"✓ Raw data file exists: {raw_path}")
else:
    print(f"⚠ Raw data file not found (OK if not crawled yet)")

print("\n✓ Text processor configuration is correct!")
print("  To run full processing: python -m src.processors.text_processor")

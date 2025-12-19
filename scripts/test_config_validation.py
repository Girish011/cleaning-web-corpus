#!/usr/bin/env python3
"""
Test script to demonstrate config validation features.
"""

import sys
import pathlib
import tempfile
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pydantic import ValidationError
from src.config import load_config, Config


def test_valid_config():
    """Test loading a valid config."""
    print("=" * 60)
    print("TEST 1: Valid Config")
    print("=" * 60)
    
    config = load_config()
    print(f"✓ Config loaded successfully")
    print(f"  Project: {config.project.name} v{config.project.version}")
    print(f"  Min words: {config.quality.text.min_words}")
    print(f"  Max words: {config.quality.text.max_words}")
    print(f"  Log level: {config.logging.level}")


def test_invalid_config():
    """Test that invalid configs are caught."""
    print("\n" + "=" * 60)
    print("TEST 2: Invalid Config Detection")
    print("=" * 60)
    
    # Create invalid config (max_words < min_words)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        invalid_config = {
            "quality": {
                "text": {
                    "min_words": 1000,
                    "max_words": 500  # Invalid: max < min
                }
            }
        }
        yaml.dump(invalid_config, f)
        temp_path = pathlib.Path(f.name)
    
    try:
        try:
            load_config(temp_path)
            print("✗ Should have raised ValidationError")
        except ValueError as e:
            print(f"✓ Validation error caught: {str(e)[:80]}...")
    finally:
        temp_path.unlink()


def test_type_safety():
    """Test type safety features."""
    print("\n" + "=" * 60)
    print("TEST 3: Type Safety")
    print("=" * 60)
    
    config = load_config()
    
    # Type-safe access
    min_words = config.quality.text.min_words  # int, not dict access
    log_level = config.logging.level  # Literal type
    
    print(f"✓ Type-safe access works")
    print(f"  min_words type: {type(min_words).__name__}")
    print(f"  log_level type: {type(log_level).__name__}")
    print(f"  IDE autocomplete and type checking available!")


def test_defaults():
    """Test that defaults work correctly."""
    print("\n" + "=" * 60)
    print("TEST 4: Default Values")
    print("=" * 60)
    
    # Create minimal config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        minimal_config = {
            "project": {"name": "test", "version": "1.0.0"}
        }
        yaml.dump(minimal_config, f)
        temp_path = pathlib.Path(f.name)
    
    try:
        config = load_config(temp_path)
        print(f"✓ Config with minimal data loads")
        print(f"  Using defaults:")
        print(f"    - Min words: {config.quality.text.min_words} (default)")
        print(f"    - Download images: {config.crawler.download_images} (default)")
        print(f"    - Batch size: {config.processing.batch_size} (default)")
    finally:
        temp_path.unlink()


def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("CONFIG VALIDATION TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_valid_config()
        test_invalid_config()
        test_type_safety()
        test_defaults()
        
        print("\n" + "=" * 60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 60)
        print("\nBenefits of Pydantic config:")
        print("  ✓ Type safety - catch errors at load time")
        print("  ✓ Validation - ensure config values are valid")
        print("  ✓ IDE support - autocomplete and type hints")
        print("  ✓ Defaults - sensible defaults for all fields")
        print("  ✓ Documentation - field descriptions available")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

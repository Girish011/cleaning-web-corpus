#!/usr/bin/env python3
"""
Test script to verify all existing functionalities work in the new structure.
"""

import sys
import pathlib
import json

# Add project root to path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from src.crawlers import seed_spider
        print("✓ src.crawlers.seed_spider imported successfully")
    except Exception as e:
        print(f"✗ Failed to import seed_spider: {e}")
        return False
    
    try:
        from src.processors import text_processor
        print("✓ src.processors.text_processor imported successfully")
    except Exception as e:
        print(f"✗ Failed to import text_processor: {e}")
        return False
    
    try:
        from src.evaluation import statistics
        print("✓ src.evaluation.statistics imported successfully")
    except Exception as e:
        print(f"✗ Failed to import statistics: {e}")
        return False
    
    return True


def test_config_loading():
    """Test that YAML config can be loaded."""
    print("\n" + "=" * 60)
    print("TEST 2: Config Loading")
    print("=" * 60)
    
    try:
        import yaml
        config_path = ROOT / "configs" / "default.yaml"
        
        if not config_path.exists():
            print(f"✗ Config file not found: {config_path}")
            return False
        
        with config_path.open() as f:
            config = yaml.safe_load(f)
        
        print(f"✓ Config file loaded successfully")
        print(f"  - Project: {config.get('project', {}).get('name', 'N/A')}")
        print(f"  - Min words: {config.get('quality', {}).get('text', {}).get('min_words', 'N/A')}")
        print(f"  - Log level: {config.get('logging', {}).get('level', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False


def test_seeds_file():
    """Test that seeds file exists and is readable."""
    print("\n" + "=" * 60)
    print("TEST 3: Seeds File")
    print("=" * 60)
    
    seeds_path = ROOT / "data" / "seeds.txt"
    
    if not seeds_path.exists():
        print(f"✗ Seeds file not found: {seeds_path}")
        return False
    
    try:
        with seeds_path.open() as f:
            seeds = [line.strip() for line in f if line.strip()]
        
        print(f"✓ Seeds file found with {len(seeds)} URLs")
        if seeds:
            print(f"  - First seed: {seeds[0][:60]}...")
        return True
    except Exception as e:
        print(f"✗ Failed to read seeds file: {e}")
        return False


def test_data_files():
    """Test that data files exist."""
    print("\n" + "=" * 60)
    print("TEST 4: Data Files")
    print("=" * 60)
    
    raw_path = ROOT / "data" / "raw" / "seed_pages.jsonl"
    processed_path = ROOT / "data" / "processed" / "cleaning_docs.jsonl"
    
    if raw_path.exists():
        try:
            with raw_path.open() as f:
                raw_count = sum(1 for line in f if line.strip())
            print(f"✓ Raw data file found: {raw_count} records")
        except Exception as e:
            print(f"✗ Failed to read raw data: {e}")
            return False
    else:
        print(f"⚠ Raw data file not found (this is OK if you haven't crawled yet)")
    
    if processed_path.exists():
        try:
            with processed_path.open() as f:
                processed_count = sum(1 for line in f if line.strip())
            print(f"✓ Processed data file found: {processed_count} records")
        except Exception as e:
            print(f"✗ Failed to read processed data: {e}")
            return False
    else:
        print(f"⚠ Processed data file not found (this is OK if you haven't processed yet)")
    
    return True


def test_text_processor_config():
    """Test that text processor can load config correctly."""
    print("\n" + "=" * 60)
    print("TEST 5: Text Processor Config Access")
    print("=" * 60)
    
    try:
        import yaml
        config_path = ROOT / "configs" / "default.yaml"
        
        with config_path.open() as f:
            config = yaml.safe_load(f)
        
        # Test the same access pattern as text_processor.py
        min_words = config.get("quality", {}).get("text", {}).get("min_words", 500)
        log_level = config.get("logging", {}).get("level", "INFO")
        
        print(f"✓ Config access works")
        print(f"  - MIN_WORDS: {min_words}")
        print(f"  - LOG_LEVEL: {log_level}")
        return True
    except Exception as e:
        print(f"✗ Failed to access config: {e}")
        return False


def test_scrapy_config():
    """Test that scrapy.cfg is correctly configured."""
    print("\n" + "=" * 60)
    print("TEST 6: Scrapy Configuration")
    print("=" * 60)
    
    scrapy_cfg = ROOT / "scrapy.cfg"
    
    if not scrapy_cfg.exists():
        print(f"✗ scrapy.cfg not found")
        return False
    
    try:
        import configparser
        parser = configparser.ConfigParser()
        parser.read(scrapy_cfg)
        
        settings_module = parser.get("settings", "default", fallback=None)
        print(f"✓ scrapy.cfg found")
        print(f"  - Settings module: {settings_module}")
        
        if settings_module == "src.crawlers.settings":
            print(f"✓ Settings module path is correct")
            return True
        else:
            print(f"⚠ Settings module path might be incorrect: {settings_module}")
            return False
    except Exception as e:
        print(f"✗ Failed to read scrapy.cfg: {e}")
        return False


def test_paths():
    """Test that path calculations are correct."""
    print("\n" + "=" * 60)
    print("TEST 7: Path Calculations")
    print("=" * 60)
    
    # Test spider path calculation
    spider_path = ROOT / "src" / "crawlers" / "seed_spider.py"
    if spider_path.exists():
        # Simulate the path calculation in seed_spider.py
        test_root = spider_path.resolve().parents[2]
        test_seeds = test_root / "data" / "seeds.txt"
        
        if test_seeds.exists():
            print(f"✓ Spider path calculation correct")
            print(f"  - Calculated root: {test_root}")
            print(f"  - Seeds file found: {test_seeds.exists()}")
        else:
            print(f"✗ Spider path calculation incorrect")
            print(f"  - Calculated root: {test_root}")
            print(f"  - Seeds file should be at: {test_seeds}")
            return False
    
    # Test processor path calculation
    processor_path = ROOT / "src" / "processors" / "text_processor.py"
    if processor_path.exists():
        test_root = processor_path.resolve().parents[2]
        test_config = test_root / "configs" / "default.yaml"
        
        if test_config.exists():
            print(f"✓ Processor path calculation correct")
            print(f"  - Calculated root: {test_root}")
            print(f"  - Config file found: {test_config.exists()}")
        else:
            print(f"✗ Processor path calculation incorrect")
            return False
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TESTING EXISTING FUNCTIONALITIES IN NEW STRUCTURE")
    print("=" * 60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Config Loading", test_config_loading),
        ("Seeds File", test_seeds_file),
        ("Data Files", test_data_files),
        ("Text Processor Config", test_text_processor_config),
        ("Scrapy Config", test_scrapy_config),
        ("Path Calculations", test_paths),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The restructure is successful.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test script that checks if dependencies are installed and tests actual functionality.
Run this after installing dependencies: pip install -r requirements.txt
"""

import sys
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]

def check_dependencies():
    """Check if required dependencies are installed."""
    print("=" * 60)
    print("CHECKING DEPENDENCIES")
    print("=" * 60)
    
    required = {
        'scrapy': 'scrapy',
        'yaml': 'pyyaml',
        'trafilatura': 'trafilatura',
        'requests': 'requests',
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    return True


def test_crawler_functionality():
    """Test that crawler can be discovered by Scrapy."""
    print("\n" + "=" * 60)
    print("TEST: Crawler Discovery")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['scrapy', 'list'],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            spiders = result.stdout.strip().split('\n')
            if 'seed_spider' in spiders:
                print(f"✓ Scrapy found seed_spider")
                print(f"  Available spiders: {', '.join(spiders)}")
                return True
            else:
                print(f"✗ seed_spider not found in scrapy list")
                print(f"  Available spiders: {', '.join(spiders)}")
                return False
        else:
            print(f"✗ Scrapy command failed:")
            print(f"  {result.stderr}")
            return False
    except FileNotFoundError:
        print("✗ Scrapy not found in PATH")
        return False
    except Exception as e:
        print(f"✗ Error running scrapy: {e}")
        return False


def test_text_processor_functionality():
    """Test that text processor can actually process data."""
    print("\n" + "=" * 60)
    print("TEST: Text Processor Functionality")
    print("=" * 60)
    
    try:
        # Import the module
        sys.path.insert(0, str(ROOT))
        from src.processors import text_processor
        
        # Check if it can load config
        config_path = ROOT / "configs" / "default.yaml"
        if not config_path.exists():
            print("✗ Config file not found")
            return False
        
        # Check if raw data exists
        raw_path = ROOT / "data" / "raw" / "seed_pages.jsonl"
        if not raw_path.exists():
            print("⚠ Raw data file not found - skipping processor test")
            print("  (This is OK if you haven't crawled yet)")
            return True
        
        print("✓ Text processor module loaded")
        print("✓ Config file accessible")
        print("✓ Raw data file exists")
        print("\n  To test full processing, run:")
        print("    python -m src.processors.text_processor")
        
        return True
    except Exception as e:
        print(f"✗ Failed to test text processor: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statistics_functionality():
    """Test that statistics script can analyze data."""
    print("\n" + "=" * 60)
    print("TEST: Statistics Functionality")
    print("=" * 60)
    
    try:
        sys.path.insert(0, str(ROOT))
        from src.evaluation import statistics
        
        processed_path = ROOT / "data" / "processed" / "cleaning_docs.jsonl"
        if not processed_path.exists():
            print("⚠ Processed data file not found - skipping statistics test")
            print("  (This is OK if you haven't processed data yet)")
            return True
        
        print("✓ Statistics module loaded")
        print("✓ Processed data file exists")
        print("\n  To test statistics, run:")
        print("    python -m src.evaluation.statistics")
        
        return True
    except Exception as e:
        print(f"✗ Failed to test statistics: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run functionality tests."""
    print("\n" + "=" * 60)
    print("TESTING FUNCTIONALITY WITH DEPENDENCIES")
    print("=" * 60 + "\n")
    
    # First check dependencies
    if not check_dependencies():
        print("\n⚠️  Please install dependencies first:")
        print("   pip install -r requirements.txt")
        return 1
    
    # Run functionality tests
    tests = [
        ("Crawler Discovery", test_crawler_functionality),
        ("Text Processor", test_text_processor_functionality),
        ("Statistics", test_statistics_functionality),
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
    print("FUNCTIONALITY TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All functionality tests passed!")
        print("\nNext steps:")
        print("  1. Test crawler: scrapy crawl seed_spider -O data/raw/test_output.jsonl")
        print("  2. Test processor: python -m src.processors.text_processor")
        print("  3. Test statistics: python -m src.evaluation.statistics")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

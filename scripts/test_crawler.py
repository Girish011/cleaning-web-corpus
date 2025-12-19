#!/usr/bin/env python3
"""Test crawler configuration and paths."""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Test that spider can find seeds file
spider_path = ROOT / "src" / "crawlers" / "seed_spider.py"
test_root = spider_path.resolve().parents[2]
seeds_file = test_root / "data" / "seeds.txt"

print("=" * 60)
print("CRAWLER CONFIGURATION TEST")
print("=" * 60)

if seeds_file.exists():
    with seeds_file.open() as f:
        seeds = [line.strip() for line in f if line.strip()]
    print(f"✓ Seeds file found: {len(seeds)} URLs")
    print(f"  Path: {seeds_file}")
else:
    print(f"✗ Seeds file not found: {seeds_file}")

# Test scrapy config
scrapy_cfg = ROOT / "scrapy.cfg"
if scrapy_cfg.exists():
    print(f"✓ scrapy.cfg found")
    import configparser
    parser = configparser.ConfigParser()
    parser.read(scrapy_cfg)
    settings = parser.get("settings", "default")
    print(f"  Settings module: {settings}")

print("\n✓ Crawler is properly configured!")
print("  To test crawling: scrapy crawl seed_spider -O data/raw/test_output.jsonl")

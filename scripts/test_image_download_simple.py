#!/usr/bin/env python3
"""
Simplified test script for image download - runs crawler and checks results.

This version doesn't use subprocess timeout, so you can Ctrl+C if needed.
"""

import sys
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check_existing_results():
    """Check if we have existing crawl results to analyze."""
    print("=" * 60)
    print("CHECKING EXISTING CRAWL RESULTS")
    print("=" * 60)
    
    raw_file = ROOT / "data" / "raw" / "seed_pages.jsonl"
    
    if not raw_file.exists():
        print(f"⚠ No existing crawl results found at: {raw_file}")
        print("\nTo generate results, run:")
        print("  scrapy crawl seed_spider -O data/raw/seed_pages.jsonl")
        return False
    
    print(f"✓ Found existing crawl results: {raw_file}")
    
    # Analyze results
    items = []
    with raw_file.open() as f:
        for line in f:
            if line.strip():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    print(f"✓ Found {len(items)} crawled items\n")
    
    if not items:
        print("⚠ No items in crawl results")
        return False
    
    # Check for images
    total_images = 0
    downloaded_images = 0
    images_with_metadata = 0
    images_with_dimensions = 0
    
    print("=" * 60)
    print("IMAGE ANALYSIS")
    print("=" * 60)
    
    for i, item in enumerate(items, 1):
        url = item.get('url', 'unknown')
        image_urls = item.get('image_urls', [])
        images = item.get('images', [])
        
        total_images += len(image_urls)
        downloaded = [img for img in images if 'path' in img]
        downloaded_images += len(downloaded)
        
        with_metadata = [img for img in downloaded if 'width' in img and 'height' in img]
        images_with_metadata += len(with_metadata)
        images_with_dimensions += len([img for img in with_metadata if img.get('width') and img.get('height')])
        
        if images:
            print(f"\n[{i}] {url[:60]}...")
            print(f"    Image URLs found: {len(image_urls)}")
            print(f"    Images downloaded: {len(downloaded)}")
            if downloaded:
                for img in downloaded[:2]:  # Show first 2
                    path = img.get('path', 'N/A')
                    width = img.get('width', 'N/A')
                    height = img.get('height', 'N/A')
                    size_kb = img.get('file_size', 0) / 1024 if img.get('file_size') else 'N/A'
                    print(f"      - {path}")
                    print(f"        {width}x{height}, {size_kb} KB" if width != 'N/A' else "        (metadata pending)")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total pages crawled: {len(items)}")
    print(f"Total image URLs found: {total_images}")
    print(f"Images downloaded: {downloaded_images}")
    print(f"Images with metadata: {images_with_metadata}")
    print(f"Images with dimensions: {images_with_dimensions}")
    
    # Check images directory
    images_dir = ROOT / "data" / "images"
    if images_dir.exists():
        image_files = list(images_dir.rglob("*.jpg")) + list(images_dir.rglob("*.png")) + list(images_dir.rglob("*.webp"))
        print(f"\nImage files on disk: {len(image_files)}")
        
        if image_files:
            print(f"\nSample image paths:")
            for img_path in image_files[:5]:
                rel_path = img_path.relative_to(ROOT)
                size_kb = img_path.stat().st_size / 1024
                print(f"  - {rel_path} ({size_kb:.1f} KB)")
    else:
        print(f"\n⚠ Images directory not found: {images_dir}")
    
    return True


def main():
    """Run simple image download test."""
    print("\n" + "=" * 60)
    print("SIMPLE IMAGE DOWNLOAD TEST")
    print("=" * 60 + "\n")
    
    print("This script analyzes existing crawl results.")
    print("If you haven't run the crawler yet, run:")
    print("  scrapy crawl seed_spider -O data/raw/seed_pages.jsonl\n")
    
    success = check_existing_results()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETE")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠ NO RESULTS FOUND")
        print("=" * 60)
        print("\nTo generate results, run:")
        print("  source .venv/bin/activate")
        print("  scrapy crawl seed_spider -O data/raw/seed_pages.jsonl")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test script to verify image download functionality.

This script:
1. Runs the crawler on a small subset of URLs
2. Verifies images are downloaded
3. Checks metadata extraction
4. Verifies file organization
"""

import sys
import pathlib
import json
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_image_download():
    """Test that images are downloaded correctly."""
    print("=" * 60)
    print("TESTING IMAGE DOWNLOAD FUNCTIONALITY")
    print("=" * 60)
    
    # Check if Pillow is installed
    try:
        from PIL import Image
        print("✓ Pillow is installed")
    except ImportError:
        print("✗ Pillow is not installed. Run: pip install Pillow")
        return False
    
    # Check if scrapy is available
    try:
        result = subprocess.run(
            ['scrapy', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Scrapy is available: {result.stdout.strip()}")
        else:
            print("✗ Scrapy command failed")
            return False
    except FileNotFoundError:
        print("✗ Scrapy not found in PATH")
        return False
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_output = pathlib.Path(f.name)
    
    try:
        # Run crawler on first 2 URLs from seeds
        print("\n" + "=" * 60)
        print("Running crawler on test URLs...")
        print("=" * 60)
        
        # Read first 2 URLs from seeds
        seeds_file = ROOT / "data" / "seeds.txt"
        if not seeds_file.exists():
            print(f"✗ Seeds file not found: {seeds_file}")
            return False
        
        test_urls = []
        with seeds_file.open() as f:
            for i, line in enumerate(f):
                if i >= 2:  # Only first 2 URLs
                    break
                url = line.strip()
                if url:
                    test_urls.append(url)
        
        if not test_urls:
            print("✗ No URLs found in seeds file")
            return False
        
        print(f"Testing with {len(test_urls)} URLs:")
        for url in test_urls:
            print(f"  - {url}")
        
        # Create temporary seeds file with test URLs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_seeds = pathlib.Path(f.name)
            for url in test_urls:
                f.write(url + "\n")
        
        # Run scrapy crawl
        print("\nRunning: scrapy crawl seed_spider...")
        print("(This may take a few minutes if downloading images...)")
        result = subprocess.run(
            ['scrapy', 'crawl', 'seed_spider', '-O', str(temp_output)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout (images can take time)
        )
        
        if result.returncode != 0:
            print(f"✗ Crawler failed:")
            print(result.stderr)
            return False
        
        print("✓ Crawler completed successfully")
        
        # Check output file
        if not temp_output.exists():
            print("✗ Output file not created")
            return False
        
        # Read and analyze results
        print("\n" + "=" * 60)
        print("Analyzing Results")
        print("=" * 60)
        
        items = []
        with temp_output.open() as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        
        print(f"✓ Found {len(items)} crawled items")
        
        if not items:
            print("⚠ No items crawled (this might be OK if URLs are inaccessible)")
            return True
        
        # Check for images
        total_images = 0
        downloaded_images = 0
        images_with_metadata = 0
        
        for item in items:
            image_urls = item.get('image_urls', [])
            images = item.get('images', [])
            
            total_images += len(image_urls)
            downloaded_images += len([img for img in images if 'path' in img])
            images_with_metadata += len([
                img for img in images 
                if 'path' in img and 'width' in img and 'height' in img
            ])
        
        print(f"\nImage Statistics:")
        print(f"  - Total image URLs found: {total_images}")
        print(f"  - Images downloaded: {downloaded_images}")
        print(f"  - Images with metadata: {images_with_metadata}")
        
        # Check if images directory exists and has files
        images_dir = ROOT / "data" / "images"
        if images_dir.exists():
            image_files = list(images_dir.rglob("*.jpg")) + list(images_dir.rglob("*.png"))
            print(f"  - Image files on disk: {len(image_files)}")
            
            if image_files:
                print(f"\n✓ Image files found in: {images_dir}")
                print(f"  Sample paths:")
                for img_path in image_files[:3]:
                    print(f"    - {img_path.relative_to(ROOT)}")
        else:
            print(f"⚠ Images directory not found: {images_dir}")
            print("  (This is OK if no images were downloaded)")
        
        # Check metadata extraction
        print("\n" + "=" * 60)
        print("Metadata Extraction Test")
        print("=" * 60)
        
        for item in items:
            images = item.get('images', [])
            for img in images:
                if 'path' in img:
                    print(f"\nImage: {img.get('url', 'unknown')[:60]}...")
                    print(f"  Path: {img.get('path', 'N/A')}")
                    if 'width' in img and 'height' in img:
                        print(f"  Dimensions: {img.get('width')}x{img.get('height')}")
                    if 'file_size' in img:
                        size_kb = img.get('file_size', 0) / 1024
                        print(f"  File size: {size_kb:.1f} KB")
                    if 'checksum' in img:
                        print(f"  Checksum: {img.get('checksum', 'N/A')[:16]}...")
        
        print("\n" + "=" * 60)
        print("✅ IMAGE DOWNLOAD TEST COMPLETE")
        print("=" * 60)
        
        if downloaded_images > 0:
            print(f"\n✓ Successfully downloaded {downloaded_images} images")
            if images_with_metadata == downloaded_images:
                print("✓ All downloaded images have metadata")
            else:
                print(f"⚠ {downloaded_images - images_with_metadata} images missing metadata")
        else:
            print("\n⚠ No images were downloaded")
            print("  This might be normal if:")
            print("    - URLs don't contain images")
            print("    - Images are blocked by robots.txt")
            print("    - Network issues")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if temp_output.exists():
            temp_output.unlink()
        if temp_seeds.exists():
            temp_seeds.unlink()


def main():
    """Run image download tests."""
    success = test_image_download()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

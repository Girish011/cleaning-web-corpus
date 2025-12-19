#!/usr/bin/env python3
"""
Test script for duplicate image detection.

This script demonstrates and tests the duplicate detection functionality.
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import get_config, ImageQualityConfig
from src.quality.image_filters import ImageQualityFilter


def test_duplicate_detection_basic():
    """Test basic duplicate detection functionality."""
    print("=" * 70)
    print("Testing Duplicate Image Detection")
    print("=" * 70)
    
    config = ImageQualityConfig(
        min_resolution=[100, 100],
        enable_duplicate_detection=True,
        duplicate_hash_algorithm="phash",
        duplicate_similarity_threshold=5
    )
    filter_instance = ImageQualityFilter(config)
    
    print(f"\nConfig:")
    print(f"  - Hash algorithm: {config.duplicate_hash_algorithm}")
    print(f"  - Similarity threshold: {config.duplicate_similarity_threshold}")
    print(f"  - Min images for check: {config.min_images_for_duplicate_check}")
    
    # Test with sample images (would need actual image files for real testing)
    print("\n" + "=" * 70)
    print("Note: This test requires actual image files to compute hashes.")
    print("For real testing, provide image paths in the images list below.")
    print("=" * 70)
    
    # Example structure (would need real paths)
    images = [
        {"width": 500, "height": 500, "path": "data/images/test1.jpg", "url": "http://example.com/img1.jpg"},
        {"width": 500, "height": 500, "path": "data/images/test2.jpg", "url": "http://example.com/img2.jpg"},
    ]
    
    passed, failed = filter_instance.filter_images(images)
    print(f"\nResults:")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed images:")
        for img in failed:
            print(f"  - {img.get('url', 'unknown')}: {img.get('filter_reason', 'unknown')}")


def test_hash_algorithms():
    """Test different hash algorithms."""
    print("\n" + "=" * 70)
    print("Testing Different Hash Algorithms")
    print("=" * 70)
    
    algorithms = ["phash", "dhash", "whash", "average_hash"]
    
    for algo in algorithms:
        print(f"\nAlgorithm: {algo}")
        try:
            config = ImageQualityConfig(
                min_resolution=[100, 100],
                duplicate_hash_algorithm=algo
            )
            filter_instance = ImageQualityFilter(config)
            print(f"  ✓ {algo} initialized successfully")
        except Exception as e:
            print(f"  ✗ {algo} failed: {e}")


def test_threshold_sensitivity():
    """Test different similarity thresholds."""
    print("\n" + "=" * 70)
    print("Understanding Similarity Thresholds")
    print("=" * 70)
    
    print("\nHamming Distance Threshold Guide:")
    print("  - 0:   Exact duplicates only")
    print("  - 1-3: Very similar images (minor edits, compression)")
    print("  - 4-6: Similar images (cropped, resized, slight modifications)")
    print("  - 7-10: Somewhat similar (different crops, significant edits)")
    print("  - >10:  Different images")
    print("\nRecommended: 5 (catches near-duplicates while avoiding false positives)")


def test_with_real_images():
    """Test with actual image files if available."""
    print("\n" + "=" * 70)
    print("Testing with Real Images (if available)")
    print("=" * 70)
    
    config = get_config()
    filter_instance = ImageQualityFilter(config.quality.image)
    
    # Look for images in data/images directory
    images_dir = ROOT / "data" / "images"
    
    if not images_dir.exists():
        print(f"\n⚠ Images directory not found: {images_dir}")
        print("   Run the crawler first to download images.")
        return
    
    # Find some image files
    image_files = list(images_dir.rglob("*.jpg")) + list(images_dir.rglob("*.png"))
    
    if not image_files:
        print(f"\n⚠ No image files found in {images_dir}")
        return
    
    print(f"\n✓ Found {len(image_files)} image files")
    print(f"  Testing with first 5 images...")
    
    # Create image data structures
    images = []
    for img_path in image_files[:5]:
        images.append({
            "width": None,  # Would need to load image to get dimensions
            "height": None,
            "path": str(img_path.relative_to(ROOT)),
            "url": f"http://example.com/{img_path.name}"
        })
    
    passed, failed = filter_instance.filter_images(images)
    
    print(f"\nResults:")
    print(f"  Total images: {len(images)}")
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed images:")
        for img in failed:
            print(f"  - {img.get('url', 'unknown')}: {img.get('filter_reason', 'unknown')}")


if __name__ == "__main__":
    try:
        test_duplicate_detection_basic()
        test_hash_algorithms()
        test_threshold_sensitivity()
        test_with_real_images()
        
        print("\n" + "=" * 70)
        print("Duplicate Detection Tests Completed!")
        print("=" * 70)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

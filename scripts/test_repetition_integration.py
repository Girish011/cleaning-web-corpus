#!/usr/bin/env python3
"""
End-to-end integration test for repetition filter with actual URL processing.

This script tests the repetition filter as part of the full URL ingestion pipeline.
"""

import sys
import json
import pathlib
import logging
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import get_config
from src.processors.text_processor import process_url
from src.quality.text_filters import TextQualityFilter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


def test_with_raw_data():
    """Test repetition filter with actual raw crawled data."""
    print("=" * 70)
    print("Testing Repetition Filter Integration with Real URL Data")
    print("=" * 70)
    
    config = get_config()
    raw_path = ROOT / "data" / "raw" / "seed_pages.jsonl"
    
    if not raw_path.exists():
        print(f"\n⚠ Raw data file not found: {raw_path}")
        print("   Run the crawler first to generate raw data.")
        print("   Or use test_with_sample_urls() for testing with sample URLs.")
        return
    
    print(f"\n✓ Found raw data file: {raw_path}")
    
    # Statistics
    stats = {
        "total": 0,
        "kept": 0,
        "failed": 0,
        "repetition_failures": defaultdict(int),
        "other_failures": defaultdict(int),
        "repetition_stats": []
    }
    
    text_filter = TextQualityFilter(config.quality.text)
    
    print(f"\nProcessing URLs from raw data...")
    print(f"Repetition filter config:")
    print(f"  - Max char repetition: {config.quality.text.max_char_repetition_ratio}")
    print(f"  - Max word repetition: {config.quality.text.max_word_repetition_ratio}")
    print(f"  - Max n-gram repetition: {config.quality.text.max_ngram_repetition}")
    print(f"  - N-gram size: {config.quality.text.ngram_size}")
    print()
    
    with raw_path.open() as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                obj = json.loads(line)
                url = obj.get("url")
                title = obj.get("title", "")
                image_urls = obj.get("image_urls", [])
                video_urls = obj.get("video_urls", [])
                image_details = obj.get("image_details", [])
                video_metadata = obj.get("video_metadata", [])
                
                if not url:
                    continue
                
                stats["total"] += 1
                
                # Process URL (this will apply all filters including repetition)
                record = process_url(url, title, image_urls, video_urls, image_details, video_metadata)
                
                if record is None:
                    stats["failed"] += 1
                    # Check why it failed by testing the filter directly
                    # (We need to fetch the text again to check)
                    try:
                        import requests
                        resp = requests.get(url, timeout=10)
                        import trafilatura
                        main_text = trafilatura.extract(resp.text) or ""
                        
                        if main_text:
                            filter_result = text_filter.filter(main_text)
                            reason = filter_result.get('reason', 'unknown')
                            
                            if 'repetition' in reason.lower():
                                stats["repetition_failures"][reason] += 1
                                # Store detailed stats
                                rep_stats = filter_result.get('stats', {})
                                stats["repetition_stats"].append({
                                    "url": url,
                                    "reason": reason,
                                    "char_ratio": rep_stats.get('char_repetition_ratio'),
                                    "word_ratio": rep_stats.get('word_repetition_ratio'),
                                    "max_ngram": rep_stats.get('max_ngram_repetition'),
                                })
                            else:
                                stats["other_failures"][reason] += 1
                    except Exception as e:
                        logger.debug(f"Could not analyze failure for {url}: {e}")
                
                else:
                    stats["kept"] += 1
                    # Check if it passed repetition (for reporting)
                    main_text = record.get("main_text", "")
                    if main_text:
                        filter_result = text_filter.filter(main_text)
                        rep_stats = filter_result.get('stats', {})
                        if any(k in rep_stats for k in ['char_repetition_ratio', 'word_repetition_ratio', 'max_ngram_repetition']):
                            # Text passed but we can see repetition metrics
                            pass
                
                # Print progress every 10 URLs
                if stats["total"] % 10 == 0:
                    print(f"  Processed {stats['total']} URLs... (kept: {stats['kept']}, failed: {stats['failed']})")
                
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                continue
    
    # Print summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total URLs processed: {stats['total']}")
    print(f"Kept (passed all filters): {stats['kept']}")
    print(f"Failed (rejected by filters): {stats['failed']}")
    print(f"Success rate: {stats['kept']/stats['total']*100:.1f}%" if stats['total'] > 0 else "N/A")
    
    if stats['repetition_failures']:
        print(f"\nRepetition Filter Failures: {sum(stats['repetition_failures'].values())}")
        for reason, count in stats['repetition_failures'].items():
            print(f"  - {reason}: {count}")
    
    if stats['other_failures']:
        print(f"\nOther Filter Failures: {sum(stats['other_failures'].values())}")
        for reason, count in list(stats['other_failures'].items())[:5]:  # Show top 5
            print(f"  - {reason}: {count}")
        if len(stats['other_failures']) > 5:
            print(f"  ... and {len(stats['other_failures']) - 5} more failure types")
    
    if stats['repetition_stats']:
        print(f"\nDetailed Repetition Failures (showing first 5):")
        for i, rep_stat in enumerate(stats['repetition_stats'][:5], 1):
            print(f"\n  {i}. URL: {rep_stat['url'][:60]}...")
            print(f"     Reason: {rep_stat['reason']}")
            if rep_stat['char_ratio'] is not None:
                print(f"     Char repetition ratio: {rep_stat['char_ratio']:.3f}")
            if rep_stat['word_ratio'] is not None:
                print(f"     Word repetition ratio: {rep_stat['word_ratio']:.3f}")
            if rep_stat['max_ngram'] is not None:
                print(f"     Max n-gram repetition: {rep_stat['max_ngram']}")


def test_with_sample_urls():
    """Test repetition filter with sample URLs (doesn't require raw data)."""
    print("=" * 70)
    print("Testing Repetition Filter with Sample URLs")
    print("=" * 70)
    
    config = get_config()
    text_filter = TextQualityFilter(config.quality.text)
    
    # Sample URLs to test (you can add real URLs here)
    sample_urls = [
        # Add your test URLs here
        # Example:
        # "https://example.com/cleaning-guide",
    ]
    
    if not sample_urls:
        print("\n⚠ No sample URLs provided.")
        print("   Add URLs to the sample_urls list in this script to test.")
        print("   Or run test_with_raw_data() if you have crawled data.")
        return
    
    print(f"\nTesting {len(sample_urls)} sample URLs...")
    
    for url in sample_urls:
        print(f"\nTesting: {url}")
        try:
            record = process_url(url, "Test Title")
            if record:
                main_text = record.get("main_text", "")
                filter_result = text_filter.filter(main_text)
                
                print(f"  Status: {'PASSED' if filter_result['passed'] else 'FAILED'}")
                if not filter_result['passed']:
                    print(f"  Reason: {filter_result['reason']}")
                
                stats = filter_result.get('stats', {})
                if 'char_repetition_ratio' in stats:
                    print(f"  Char repetition: {stats['char_repetition_ratio']:.3f}")
                if 'word_repetition_ratio' in stats:
                    print(f"  Word repetition: {stats['word_repetition_ratio']:.3f}")
                if 'max_ngram_repetition' in stats:
                    print(f"  Max n-gram repetition: {stats['max_ngram_repetition']}")
            else:
                print(f"  Status: FAILED (could not process URL)")
        except Exception as e:
            print(f"  Error: {e}")


def test_single_url(url: str):
    """Test repetition filter with a single URL."""
    print("=" * 70)
    print(f"Testing Single URL: {url}")
    print("=" * 70)
    
    config = get_config()
    text_filter = TextQualityFilter(config.quality.text)
    
    print("\nProcessing URL...")
    record = process_url(url, "Test Title")
    
    if record is None:
        print("❌ URL processing failed (filtered out or error)")
        return
    
    print("✓ URL processed successfully")
    main_text = record.get("main_text", "")
    
    # Apply filter to see detailed stats
    filter_result = text_filter.filter(main_text)
    
    print(f"\nFilter Result: {'PASSED' if filter_result['passed'] else 'FAILED'}")
    print(f"Reason: {filter_result['reason']}")
    
    stats = filter_result.get('stats', {})
    print(f"\nDetailed Statistics:")
    print(f"  Word count: {stats.get('word_count', 'N/A')}")
    print(f"  Avg word length: {stats.get('avg_word_length', 'N/A')}")
    
    # Repetition stats
    if 'char_repetition_ratio' in stats:
        print(f"  Char repetition ratio: {stats['char_repetition_ratio']:.3f} (max: {config.quality.text.max_char_repetition_ratio})")
    if 'word_repetition_ratio' in stats:
        print(f"  Word repetition ratio: {stats['word_repetition_ratio']:.3f} (max: {config.quality.text.max_word_repetition_ratio})")
        if 'most_repeated_word' in stats:
            print(f"    Most repeated word: '{stats['most_repeated_word']}' ({stats.get('most_repeated_count', 0)} times)")
    if 'max_ngram_repetition' in stats:
        print(f"  Max n-gram repetition: {stats['max_ngram_repetition']} (max: {config.quality.text.max_ngram_repetition})")
        if 'most_repeated_ngram' in stats:
            print(f"    Most repeated n-gram: '{stats['most_repeated_ngram']}' ({stats.get('most_repeated_ngram_count', 0)} times)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test repetition filter integration")
    parser.add_argument("--url", type=str, help="Test a single URL")
    parser.add_argument("--raw-data", action="store_true", help="Test with raw crawled data")
    parser.add_argument("--sample", action="store_true", help="Test with sample URLs")
    
    args = parser.parse_args()
    
    try:
        if args.url:
            test_single_url(args.url)
        elif args.raw_data:
            test_with_raw_data()
        elif args.sample:
            test_with_sample_urls()
        else:
            # Default: try raw data, fallback to sample
            print("No arguments provided. Trying raw data first...\n")
            test_with_raw_data()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

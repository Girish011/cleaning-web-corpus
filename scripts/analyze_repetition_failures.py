#!/usr/bin/env python3
"""
Analyze why URLs are failing repetition filter.

This script helps diagnose high repetition ratios by:
1. Extracting text from failed URLs
2. Showing what words/phrases are being repeated
3. Analyzing if it's legitimate content or boilerplate
"""

import sys
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import requests
import trafilatura
from src.config import get_config
from src.quality.text_filters import TextQualityFilter

def analyze_url(url: str):
    """Analyze a single URL to understand repetition patterns."""
    print("=" * 70)
    print(f"Analyzing: {url}")
    print("=" * 70)
    
    try:
        resp = requests.get(url, timeout=20)
        html = resp.text
        
        # Extract text
        main_text = trafilatura.extract(html) or ""
        
        if not main_text:
            print("❌ Could not extract text")
            return
        
        print(f"\nExtracted text length: {len(main_text)} characters")
        print(f"Text preview (first 200 chars):")
        print(f"  {main_text[:200]}...")
        
        # Analyze with filter
        config = get_config()
        filter_instance = TextQualityFilter(config.quality.text)
        result = filter_instance.filter(main_text)
        
        stats = result.get('stats', {})
        word_ratio = stats.get('word_repetition_ratio', 0)
        
        print(f"\n📊 Repetition Statistics:")
        print(f"  Word repetition ratio: {word_ratio:.3f} (max allowed: {config.quality.text.max_word_repetition_ratio})")
        print(f"  Total words: {stats.get('total_words', 'N/A')}")
        print(f"  Unique words: {stats.get('unique_words', 'N/A')}")
        print(f"  Duplicate word count: {stats.get('duplicate_word_count', 'N/A')}")
        
        # Show most repeated words
        if 'most_repeated_word' in stats:
            print(f"\n🔝 Most Repeated Word:")
            print(f"  Word: '{stats['most_repeated_word']}'")
            print(f"  Count: {stats.get('most_repeated_count', 0)} times")
        
        # Analyze word frequencies
        words = filter_instance._split_words(main_text)
        word_counts = Counter(words)
        
        print(f"\n📈 Top 10 Most Frequent Words:")
        for word, count in word_counts.most_common(10):
            percentage = (count / len(words)) * 100
            print(f"  '{word}': {count} times ({percentage:.1f}%)")
        
        # Check if common words are causing the issue
        common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        common_word_count = sum(word_counts.get(word, 0) for word in common_words)
        common_word_ratio = common_word_count / len(words) if words else 0
        
        print(f"\n🔤 Common Words Analysis:")
        print(f"  Common words (the, a, an, etc.): {common_word_count} ({common_word_ratio*100:.1f}%)")
        
        # Check for boilerplate patterns
        print(f"\n🔍 Boilerplate Detection:")
        boilerplate_patterns = [
            ('cookie', 'cookie policy'),
            ('privacy', 'privacy policy'),
            ('terms', 'terms of service'),
            ('subscribe', 'newsletter/subscribe'),
            ('menu', 'navigation menu'),
            ('footer', 'footer content'),
        ]
        
        text_lower = main_text.lower()
        for pattern, description in boilerplate_patterns:
            if pattern in text_lower:
                count = text_lower.count(pattern)
                print(f"  Found '{description}' pattern: {count} times")
        
        # Show sample of repeated content
        print(f"\n📝 Sample Repeated Phrases (if any):")
        ngram_size = config.quality.text.ngram_size
        max_ngram_rep = stats.get('max_ngram_repetition', 0)
        if max_ngram_rep > config.quality.text.max_ngram_repetition:
            most_repeated_ngram = stats.get('most_repeated_ngram', '')
            print(f"  Most repeated {ngram_size}-gram: '{most_repeated_ngram}' ({stats.get('most_repeated_ngram_count', 0)} times)")
        
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Error analyzing URL: {e}")
        import traceback
        traceback.print_exc()


def analyze_all_failures():
    """Analyze all URLs that failed repetition filter."""
    raw_path = ROOT / "data" / "raw" / "seed_pages.jsonl"
    
    if not raw_path.exists():
        print(f"❌ Raw data file not found: {raw_path}")
        return
    
    print("Analyzing all URLs that failed repetition filter...\n")
    
    failed_urls = []
    with raw_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            url = obj.get("url")
            if url:
                failed_urls.append(url)
    
    print(f"Found {len(failed_urls)} URLs to analyze\n")
    
    for i, url in enumerate(failed_urls, 1):
        print(f"\n[{i}/{len(failed_urls)}]")
        analyze_url(url)
        
        if i >= 3:  # Limit to first 3 for detailed analysis
            print("\n... (showing first 3 URLs in detail)")
            print("Run with specific URL to analyze more: python scripts/analyze_repetition_failures.py --url <URL>")
            break


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze repetition filter failures")
    parser.add_argument("--url", type=str, help="Analyze a specific URL")
    parser.add_argument("--all", action="store_true", help="Analyze all failed URLs")
    
    args = parser.parse_args()
    
    if args.url:
        analyze_url(args.url)
    elif args.all:
        analyze_all_failures()
    else:
        print("Usage:")
        print("  python scripts/analyze_repetition_failures.py --url <URL>  # Analyze specific URL")
        print("  python scripts/analyze_repetition_failures.py --all       # Analyze all failed URLs")
        print("\nExample:")
        print("  python scripts/analyze_repetition_failures.py --url 'https://www.maidbrigade.com/blog/green-cleaning-tips/how-to-clean-pillows-and-bedding/'")

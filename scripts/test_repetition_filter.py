#!/usr/bin/env python3
"""
Manual test script for repetition filter.

This script demonstrates and tests the repetition filter functionality
with various examples.
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import get_config, TextQualityConfig
from src.quality.text_filters import TextQualityFilter


def test_character_repetition():
    """Test character-level repetition detection."""
    print("=" * 60)
    print("Testing Character-Level Repetition Filter")
    print("=" * 60)
    
    config = TextQualityConfig(
        min_words=1,
        max_words=1000,
        min_avg_word_length=2.0,
        max_char_repetition_ratio=0.2  # Max 20% repeated chars
    )
    filter_instance = TextQualityFilter(config)
    
    test_cases = [
        ("Normal text", "This is a normal text with no excessive repetition."),
        ("High char repetition", "This has aaa bbb ccc ddd eee fff ggg hhh iii jjj kkk repeated sequences."),
        ("Very high repetition", "aaaa bbbb cccc dddd eeee ffff gggg hhhh iiii jjjj kkkk llll mmmm nnnn."),
    ]
    
    for name, text in test_cases:
        print(f"\nTest: {name}")
        print(f"Text: {text[:60]}...")
        result = filter_instance.filter(text)
        print(f"  Passed: {result['passed']}")
        print(f"  Reason: {result['reason']}")
        if 'char_repetition_ratio' in result.get('stats', {}):
            ratio = result['stats']['char_repetition_ratio']
            print(f"  Char repetition ratio: {ratio:.3f} (max: {config.max_char_repetition_ratio})")


def test_word_repetition():
    """Test word-level repetition detection."""
    print("\n" + "=" * 60)
    print("Testing Word-Level Repetition Filter")
    print("=" * 60)
    
    config = TextQualityConfig(
        min_words=50,
        max_words=1000,
        max_word_repetition_ratio=0.2  # Max 20% duplicate words
    )
    filter_instance = TextQualityFilter(config)
    
    test_cases = [
        ("Normal varied text", 
         "This is a comprehensive cleaning guide. The guide covers various surfaces. Each section provides detailed instructions." * 5),
        ("High word repetition", 
         " ".join(["cleaning"] * 40) + " This guide explains proper techniques."),
        ("Very high repetition", 
         " ".join(["word"] * 60)),
    ]
    
    for name, text in test_cases:
        print(f"\nTest: {name}")
        print(f"Text preview: {text[:60]}...")
        result = filter_instance.filter(text)
        print(f"  Passed: {result['passed']}")
        print(f"  Reason: {result['reason']}")
        if 'word_repetition_ratio' in result.get('stats', {}):
            ratio = result['stats']['word_repetition_ratio']
            print(f"  Word repetition ratio: {ratio:.3f} (max: {config.max_word_repetition_ratio})")
            if 'most_repeated_word' in result['stats']:
                print(f"  Most repeated word: '{result['stats']['most_repeated_word']}' ({result['stats'].get('most_repeated_count', 0)} times)")


def test_ngram_repetition():
    """Test n-gram repetition detection."""
    print("\n" + "=" * 60)
    print("Testing N-gram Repetition Filter")
    print("=" * 60)
    
    config = TextQualityConfig(
        min_words=50,
        max_words=1000,
        max_ngram_repetition=3,  # N-grams can appear max 3 times
        ngram_size=3
    )
    filter_instance = TextQualityFilter(config)
    
    test_cases = [
        ("Normal text", 
         "This is a comprehensive cleaning guide. The guide covers various surfaces. Each section provides detailed instructions for different cleaning methods." * 3),
        ("Repeated phrase (within limit)", 
         "how to clean how to clean how to clean " + " ".join(["surface"] * 30)),
        ("Excessive phrase repetition", 
         "how to clean how to clean how to clean how to clean how to clean " + " ".join(["surface"] * 30)),
    ]
    
    for name, text in test_cases:
        print(f"\nTest: {name}")
        print(f"Text preview: {text[:60]}...")
        result = filter_instance.filter(text)
        print(f"  Passed: {result['passed']}")
        print(f"  Reason: {result['reason']}")
        if 'max_ngram_repetition' in result.get('stats', {}):
            max_rep = result['stats']['max_ngram_repetition']
            print(f"  Max n-gram repetition: {max_rep} (max allowed: {config.max_ngram_repetition})")
            if 'most_repeated_ngram' in result['stats']:
                print(f"  Most repeated n-gram: '{result['stats']['most_repeated_ngram']}' ({result['stats'].get('most_repeated_ngram_count', 0)} times)")


def test_combined_filters():
    """Test repetition filter with other filters."""
    print("\n" + "=" * 60)
    print("Testing Combined Filters (Repetition + Others)")
    print("=" * 60)
    
    config = get_config()  # Use default config
    filter_instance = TextQualityFilter(config.quality.text)
    
    print(f"\nConfig values:")
    print(f"  - Max char repetition: {config.quality.text.max_char_repetition_ratio}")
    print(f"  - Max word repetition: {config.quality.text.max_word_repetition_ratio}")
    print(f"  - Max n-gram repetition: {config.quality.text.max_ngram_repetition}")
    print(f"  - N-gram size: {config.quality.text.ngram_size}")
    
    test_cases = [
        ("Good quality text", 
         "This is a comprehensive guide on cleaning various surfaces in your home. It includes detailed instructions for carpets, floors, and upholstery. The methods described are proven to be effective and safe for regular use. Follow these steps carefully to achieve the best results." * 5),
        ("Text with some repetition", 
         "Cleaning is important. Cleaning requires effort. Cleaning takes time. " * 20 + "This guide explains proper techniques."),
    ]
    
    for name, text in test_cases:
        print(f"\nTest: {name}")
        result = filter_instance.filter(text)
        print(f"  Passed: {result['passed']}")
        print(f"  Reason: {result['reason']}")
        if result['passed']:
            stats = result['stats']
            print(f"  Stats summary:")
            print(f"    - Word count: {stats.get('word_count', 'N/A')}")
            print(f"    - Char repetition: {stats.get('char_repetition_ratio', 'N/A')}")
            print(f"    - Word repetition: {stats.get('word_repetition_ratio', 'N/A')}")
            print(f"    - Max n-gram repetition: {stats.get('max_ngram_repetition', 'N/A')}")


def test_individual_methods():
    """Test individual repetition check methods."""
    print("\n" + "=" * 60)
    print("Testing Individual Repetition Methods")
    print("=" * 60)
    
    config = TextQualityConfig(
        min_words=1,
        max_words=1000,
        max_char_repetition_ratio=0.3,
        max_word_repetition_ratio=0.2,
        max_ngram_repetition=3,
        ngram_size=3
    )
    filter_instance = TextQualityFilter(config)
    
    test_text = "This is a test with some repetition. This is a test. This is a test. aaa bbb ccc"
    
    print(f"\nTest text: {test_text}\n")
    
    # Character repetition
    ratio, stats = filter_instance._check_character_repetition(test_text)
    print(f"Character Repetition:")
    print(f"  Ratio: {ratio:.3f}")
    print(f"  Stats: {stats}")
    
    # Word repetition
    ratio, stats = filter_instance._check_word_repetition(test_text)
    print(f"\nWord Repetition:")
    print(f"  Ratio: {ratio:.3f}")
    print(f"  Stats: {stats}")
    
    # N-gram repetition
    max_rep, stats = filter_instance._check_ngram_repetition(test_text)
    print(f"\nN-gram Repetition:")
    print(f"  Max repetition: {max_rep}")
    print(f"  Stats: {stats}")


if __name__ == "__main__":
    try:
        test_character_repetition()
        test_word_repetition()
        test_ngram_repetition()
        test_combined_filters()
        test_individual_methods()
        
        print("\n" + "=" * 60)
        print("All repetition filter tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


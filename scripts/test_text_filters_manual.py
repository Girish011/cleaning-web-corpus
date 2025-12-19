#!/usr/bin/env python3
"""
Manual test script for text quality filters.

This script allows you to test the text quality filters interactively
or with sample text.
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import get_config, TextQualityConfig
from src.quality.text_filters import TextQualityFilter


def test_with_config():
    """Test filters using default config."""
    print("=" * 60)
    print("Testing Text Quality Filters with Default Config")
    print("=" * 60)
    
    config = get_config()
    filter_instance = TextQualityFilter(config.quality.text)
    
    print(f"\nConfig:")
    print(f"  - Min words: {config.quality.text.min_words}")
    print(f"  - Max words: {config.quality.text.max_words}")
    print(f"  - Min avg word length: {config.quality.text.min_avg_word_length}")
    print(f"  - Language: {config.quality.text.language}")
    
    # Test cases
    test_cases = [
        ("Empty text", ""),
        ("Too short", "This is too short."),
        ("Valid text", """
        This is a comprehensive guide on how to clean various surfaces in your home.
        It includes detailed instructions for cleaning carpets, floors, and upholstery.
        The methods described here are proven to be effective and safe for regular use.
        Follow these steps carefully to achieve the best results.
        """),
        ("Text with short words", "a b c d e f g h i j k l m n o p q r s t u v w x y z"),
        ("Very long text", " ".join(["word"] * 1000)),
    ]
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, text in test_cases:
        print(f"\nTest: {name}")
        print(f"Text preview: {text[:50]}..." if len(text) > 50 else f"Text: {text}")
        result = filter_instance.filter(text)
        
        print(f"  Passed: {result['passed']}")
        print(f"  Reason: {result['reason']}")
        
        if result['stats']:
            print(f"  Stats:")
            for key, value in result['stats'].items():
                print(f"    - {key}: {value}")


def test_custom_config():
    """Test filters with custom config."""
    print("\n" + "=" * 60)
    print("Testing with Custom Config (min_words=5, max_words=20)")
    print("=" * 60)
    
    custom_config = TextQualityConfig(
        min_words=5,
        max_words=20,
        min_avg_word_length=3.0,
        language="en"
    )
    filter_instance = TextQualityFilter(custom_config)
    
    test_text = "This is a sample text with enough words to test the filter."
    result = filter_instance.filter(test_text)
    
    print(f"\nText: {test_text}")
    print(f"Passed: {result['passed']}")
    print(f"Reason: {result['reason']}")
    print(f"Stats: {result['stats']}")


def test_individual_filters():
    """Test individual filter methods."""
    print("\n" + "=" * 60)
    print("Testing Individual Filter Methods")
    print("=" * 60)
    
    config = TextQualityConfig(min_words=10, max_words=100, min_avg_word_length=3.0)
    filter_instance = TextQualityFilter(config)
    
    test_text = "This is a comprehensive cleaning guide with detailed instructions."
    
    print(f"\nTest text: {test_text}\n")
    
    # Word count
    passed, stats = filter_instance.check_word_count(test_text)
    print(f"Word Count Check:")
    print(f"  Passed: {passed}")
    print(f"  Stats: {stats}")
    
    # Avg word length
    passed, stats = filter_instance.check_avg_word_length(test_text)
    print(f"\nAvg Word Length Check:")
    print(f"  Passed: {passed}")
    print(f"  Stats: {stats}")
    
    # Language
    passed, stats = filter_instance.check_language(test_text)
    print(f"\nLanguage Check:")
    print(f"  Passed: {passed}")
    print(f"  Stats: {stats}")


if __name__ == "__main__":
    try:
        test_with_config()
        test_custom_config()
        test_individual_filters()
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

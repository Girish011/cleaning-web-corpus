"""
Text quality filtering module.

This module provides text quality filters to ensure crawled content
meets minimum quality standards before being included in the corpus.
"""

import logging
import re
from typing import Dict, Tuple

from src.config import TextQualityConfig

logger = logging.getLogger(__name__)

# Common English stop words to exclude from repetition calculation
# These are function words that naturally appear frequently in any text
COMMON_WORDS = {
    # Articles
    'a', 'an', 'the',
    # Pronouns
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
    # Prepositions
    'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into',
    'through', 'during', 'including', 'against', 'among', 'throughout', 'despite',
    'towards', 'upon', 'concerning', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
    # Conjunctions
    'and', 'or', 'but', 'if', 'because', 'as', 'since', 'while', 'although', 'though',
    # Common verbs (forms of be, have, do)
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'done',
    # Modal verbs
    'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'cannot',
    # Common adverbs
    'not', 'no', 'yes', 'very', 'too', 'also', 'just', 'only', 'even', 'still', 'yet',
    'more', 'most', 'less', 'least', 'so', 'such', 'well', 'much', 'many', 'more',
    # Question words
    'what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose', 'whom',
    # Other common words
    'all', 'each', 'every', 'both', 'few', 'other', 'another', 'some', 'any', 'same',
    'own', 'than', 'then', 'there', 'here', 'where', 'when', 'why', 'how',
}

# Minimum content words required for meaningful repetition check
MIN_CONTENT_WORDS = 10


class TextQualityFilter:
    """
    Text quality filter that applies multiple quality checks.
    
    Filters include:
    - Word count (min/max)
    - Average word length
    - Language detection
    - Repetition detection (character, word, n-gram)
    - Perplexity filter (KenLM) - detects gibberish/low-quality text
    """

    def __init__(self, config: TextQualityConfig):
        """
        Initialize the text quality filter.
        
        Args:
            config: TextQualityConfig instance with filter parameters
        """
        self.config = config
        self._init_language_detector()
        self._init_kenlm_model()

    def _init_language_detector(self):
        """Initialize language detector with seed for reproducibility."""
        try:
            from langdetect import DetectorFactory
            DetectorFactory.seed = 0
            self._langdetect_available = True
        except ImportError:
            logger.warning("langdetect not available, language filtering will be skipped")
            self._langdetect_available = False

    def _init_kenlm_model(self):
        """Initialize KenLM language model for perplexity calculation."""
        self._kenlm_available = False
        self._kenlm_model = None

        if not self.config.enable_perplexity_filter:
            logger.debug("Perplexity filter is disabled in config")
            return

        if not self.config.kenlm_model_path:
            logger.debug("KenLM model path not specified, perplexity filter will be skipped")
            return

        try:
            import kenlm
            import pathlib

            model_path = pathlib.Path(self.config.kenlm_model_path)

            # Support both absolute and relative paths
            if not model_path.is_absolute():
                # Try relative to project root
                project_root = pathlib.Path(__file__).resolve().parents[2]
                model_path = project_root / model_path

            if not model_path.exists():
                logger.warning(f"KenLM model file not found: {model_path}, perplexity filter will be skipped")
                return

            self._kenlm_model = kenlm.Model(str(model_path))
            self._kenlm_available = True
            logger.info(f"KenLM model loaded successfully: {model_path}")

        except ImportError:
            logger.warning("kenlm not available, perplexity filtering will be skipped. Install with: pip install kenlm")
            self._kenlm_available = False
        except Exception as e:
            logger.warning(f"Failed to load KenLM model: {e}, perplexity filter will be skipped")
            self._kenlm_available = False

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for processing.
        
        Args:
            text: Raw text input
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        # Strip whitespace and normalize
        return text.strip()

    def _split_words(self, text: str) -> list[str]:
        """
        Split text into words, handling punctuation.
        
        Args:
            text: Input text
            
        Returns:
            List of words (non-empty strings)
        """
        # Use regex to split on whitespace and punctuation
        # Keep only alphanumeric sequences
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w]  # Filter out empty strings

    def check_word_count(self, text: str) -> Tuple[bool, Dict]:
        """
        Check if text meets word count requirements.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        words = self._split_words(text)
        word_count = len(words)

        passed = self.config.min_words <= word_count <= self.config.max_words

        stats = {
            "word_count": word_count,
            "min_words": self.config.min_words,
            "max_words": self.config.max_words,
        }

        return passed, stats

    def check_avg_word_length(self, text: str) -> Tuple[bool, Dict]:
        """
        Check if text meets average word length requirements.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        words = self._split_words(text)

        if not words:
            return False, {
                "avg_word_length": 0.0,
                "min_required": self.config.min_avg_word_length,
                "reason": "no_words"
            }

        total_chars = sum(len(word) for word in words)
        avg_length = total_chars / len(words)

        passed = avg_length >= self.config.min_avg_word_length

        stats = {
            "avg_word_length": round(avg_length, 2),
            "min_required": self.config.min_avg_word_length,
        }

        return passed, stats

    def check_language(self, text: str) -> Tuple[bool, Dict]:
        """
        Check if text matches the expected language.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        if not self._langdetect_available:
            # If langdetect is not available, skip this check (pass)
            return True, {
                "detected_language": "unknown",
                "expected_language": self.config.language,
                "reason": "langdetect_not_available"
            }

        # Need minimum text length for reliable detection
        words = self._split_words(text)
        if len(words) < 10:
            # Too short for reliable detection, pass it
            return True, {
                "detected_language": "unknown",
                "expected_language": self.config.language,
                "reason": "text_too_short_for_detection"
            }

        try:
            from langdetect import detect

            detected_lang = detect(text)
            passed = detected_lang == self.config.language

            stats = {
                "detected_language": detected_lang,
                "expected_language": self.config.language,
            }

            return passed, stats

        except Exception as e:
            # If detection fails, be lenient and pass
            logger.debug(f"Language detection failed: {e}")
            return True, {
                "detected_language": "unknown",
                "expected_language": self.config.language,
                "error": str(e),
                "reason": "detection_failed"
            }

    def _check_character_repetition(self, text: str) -> Tuple[float, Dict]:
        """
        Check for excessive character-level repetition.
        
        Detects patterns like "aaaaaa" or "!!!!!!" that indicate low-quality text.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (repetition_ratio: float, stats: dict)
        """
        if len(text) < 10:
            return 0.0, {"char_repetition_ratio": 0.0, "reason": "text_too_short"}

        # Find sequences of 3+ repeated characters
        # Pattern matches: aaa, !!!, 111, etc.
        repeated_char_pattern = re.compile(r'(.)\1{2,}')
        matches = repeated_char_pattern.findall(text)

        # Calculate total length of repeated sequences
        total_repeated_chars = sum(len(match.group(0)) for match in repeated_char_pattern.finditer(text))
        total_chars = len(text)
        repetition_ratio = total_repeated_chars / total_chars if total_chars > 0 else 0.0

        stats = {
            "char_repetition_ratio": round(repetition_ratio, 3),
            "repeated_char_sequences": len(matches),
            "total_repeated_chars": total_repeated_chars,
        }

        return repetition_ratio, stats

    def _check_word_repetition(self, text: str) -> Tuple[float, Dict]:
        """
        Check for excessive word-level repetition.
        
        Detects when too many content words are duplicates (e.g., "word word word...").
        Excludes common English stop words from the calculation to focus on meaningful repetition.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (repetition_ratio: float, stats: dict)
        """
        words = self._split_words(text)

        if len(words) < 5:
            return 0.0, {"word_repetition_ratio": 0.0, "reason": "too_few_words"}

        # Filter out common words (stop words) - only analyze content words
        content_words = [w for w in words if w not in COMMON_WORDS]
        common_word_count = len(words) - len(content_words)

        if len(content_words) < MIN_CONTENT_WORDS:
            # Too few content words for meaningful analysis
            return 0.0, {
                "word_repetition_ratio": 0.0,
                "reason": "too_few_content_words",
                "content_words": len(content_words),
                "total_words": len(words)
            }

        # Count word frequencies (only for content words)
        word_counts = {}
        for word in content_words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Count duplicate content words (words that appear more than once)
        duplicate_words = sum(count - 1 for count in word_counts.values() if count > 1)
        total_content_words = len(content_words)
        repetition_ratio = duplicate_words / total_content_words if total_content_words > 0 else 0.0

        # Find most repeated content word
        most_repeated = max(word_counts.items(), key=lambda x: x[1]) if word_counts else ("", 0)

        stats = {
            "word_repetition_ratio": round(repetition_ratio, 3),
            "unique_words": len(word_counts),
            "total_words": len(words),
            "content_words": total_content_words,
            "common_words": common_word_count,
            "duplicate_word_count": duplicate_words,
            "most_repeated_word": most_repeated[0],
            "most_repeated_count": most_repeated[1],
        }

        return repetition_ratio, stats

    def _check_ngram_repetition(self, text: str) -> Tuple[int, Dict]:
        """
        Check for excessive n-gram repetition.
        
        Detects repeated phrases (e.g., "how to clean how to clean").
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (max_repetition_count: int, stats: dict)
        """
        words = self._split_words(text)
        ngram_size = self.config.ngram_size

        if len(words) < ngram_size * 2:
            return 0, {"max_ngram_repetition": 0, "reason": "too_few_words_for_ngrams"}

        # Generate n-grams
        ngrams = []
        for i in range(len(words) - ngram_size + 1):
            ngram = tuple(words[i:i + ngram_size])
            ngrams.append(ngram)

        # Count n-gram frequencies
        ngram_counts = {}
        for ngram in ngrams:
            ngram_counts[ngram] = ngram_counts.get(ngram, 0) + 1

        # Find maximum repetition count
        max_repetition = max(ngram_counts.values()) if ngram_counts else 0

        # Find most repeated n-gram
        most_repeated_ngram = max(ngram_counts.items(), key=lambda x: x[1]) if ngram_counts else ((), 0)

        stats = {
            "max_ngram_repetition": max_repetition,
            "ngram_size": ngram_size,
            "total_ngrams": len(ngrams),
            "unique_ngrams": len(ngram_counts),
            "most_repeated_ngram": " ".join(most_repeated_ngram[0]) if most_repeated_ngram[0] else "",
            "most_repeated_ngram_count": most_repeated_ngram[1],
        }

        return max_repetition, stats

    def check_repetition(self, text: str) -> Tuple[bool, Dict]:
        """
        Check for excessive repetition at multiple levels.
        
        Combines character, word, and n-gram repetition checks.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        words = self._split_words(text)

        # Skip repetition check for very short texts
        if len(words) < self.config.min_text_length_for_repetition_check:
            return True, {
                "repetition_check_skipped": True,
                "reason": f"text_too_short: {len(words)} words (min: {self.config.min_text_length_for_repetition_check})"
            }

        all_stats = {}

        # Check character repetition
        char_repetition_ratio, char_stats = self._check_character_repetition(text)
        all_stats.update(char_stats)
        if char_repetition_ratio > self.config.max_char_repetition_ratio:
            return False, {
                **all_stats,
                "reason": f"char_repetition_too_high: {char_repetition_ratio:.3f} (max: {self.config.max_char_repetition_ratio:.3f})"
            }

        # Check word repetition
        word_repetition_ratio, word_stats = self._check_word_repetition(text)
        all_stats.update(word_stats)
        if word_repetition_ratio > self.config.max_word_repetition_ratio:
            return False, {
                **all_stats,
                "reason": f"word_repetition_too_high: {word_repetition_ratio:.3f} (max: {self.config.max_word_repetition_ratio:.3f})"
            }

        # Check n-gram repetition
        max_ngram_repetition, ngram_stats = self._check_ngram_repetition(text)
        all_stats.update(ngram_stats)
        if max_ngram_repetition > self.config.max_ngram_repetition:
            return False, {
                **all_stats,
                "reason": f"ngram_repetition_too_high: {max_ngram_repetition} (max: {self.config.max_ngram_repetition})"
            }

        # All repetition checks passed
        return True, all_stats

    def check_perplexity(self, text: str) -> Tuple[bool, Dict]:
        """
        Check text quality using perplexity score from KenLM language model.
        
        Perplexity measures how "surprised" the language model is by the text.
        Lower perplexity = more predictable = higher quality text
        Higher perplexity = less predictable = potentially gibberish/low-quality
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        if not self.config.enable_perplexity_filter:
            return True, {
                "perplexity": None,
                "reason": "perplexity_filter_disabled"
            }

        if not self._kenlm_available or self._kenlm_model is None:
            # Graceful fallback: if model not available, skip this check
            return True, {
                "perplexity": None,
                "reason": "kenlm_model_not_available"
            }

        words = self._split_words(text)

        if len(words) < self.config.min_text_length_for_perplexity:
            return True, {
                "perplexity": None,
                "reason": f"text_too_short: {len(words)} words (min: {self.config.min_text_length_for_perplexity})"
            }

        try:
            # Calculate perplexity using KenLM
            # KenLM expects text as a string with words separated by spaces
            text_for_kenlm = " ".join(words)

            # Calculate perplexity
            perplexity = self._kenlm_model.perplexity(text_for_kenlm)

            # Check if perplexity is within acceptable range
            passed = perplexity <= self.config.max_perplexity

            stats = {
                "perplexity": round(perplexity, 2),
                "max_perplexity": self.config.max_perplexity,
            }

            return passed, stats

        except Exception as e:
            logger.warning(f"Error calculating perplexity: {e}, skipping perplexity check")
            # On error, be lenient and pass
            return True, {
                "perplexity": None,
                "error": str(e),
                "reason": "perplexity_calculation_failed"
            }

    def filter(self, text: str) -> Dict:
        """
        Apply all text quality filters.
        
        Args:
            text: Text to filter
            
        Returns:
            Dictionary with keys:
            - passed: bool - Whether all filters passed
            - reason: str - Failure reason or "passed"
            - stats: dict - All filter statistics
        """
        # Normalize text
        normalized_text = self._normalize_text(text)

        # Check for empty text
        if not normalized_text:
            return {
                "passed": False,
                "reason": "empty_text",
                "stats": {}
            }

        all_stats = {}

        # Check word count
        word_count_passed, word_stats = self.check_word_count(normalized_text)
        all_stats.update(word_stats)
        if not word_count_passed:
            word_count = word_stats.get("word_count", 0)
            min_words = word_stats.get("min_words", 0)
            max_words = word_stats.get("max_words", 0)

            if word_count < min_words:
                reason = f"word_count_too_low: {word_count} words (required: >= {min_words})"
            else:
                reason = f"word_count_too_high: {word_count} words (required: <= {max_words})"

            return {
                "passed": False,
                "reason": reason,
                "stats": all_stats
            }

        # Check average word length
        avg_length_passed, length_stats = self.check_avg_word_length(normalized_text)
        all_stats.update(length_stats)
        if not avg_length_passed:
            avg_length = length_stats.get("avg_word_length", 0.0)
            min_required = length_stats.get("min_required", 0.0)
            return {
                "passed": False,
                "reason": f"avg_word_length_failed: {avg_length:.2f} (required: >= {min_required:.2f})",
                "stats": all_stats
            }

        # Check language
        lang_passed, lang_stats = self.check_language(normalized_text)
        all_stats.update(lang_stats)
        if not lang_passed:
            detected = lang_stats.get("detected_language", "unknown")
            expected = lang_stats.get("expected_language", "unknown")
            return {
                "passed": False,
                "reason": f"language_failed: detected '{detected}' (expected: '{expected}')",
                "stats": all_stats
            }

        # Check repetition
        repetition_passed, repetition_stats = self.check_repetition(normalized_text)
        all_stats.update(repetition_stats)
        if not repetition_passed:
            reason = repetition_stats.get("reason", "repetition_failed")
            return {
                "passed": False,
                "reason": reason,
                "stats": all_stats
            }

        # Check perplexity (KenLM)
        perplexity_passed, perplexity_stats = self.check_perplexity(normalized_text)
        all_stats.update(perplexity_stats)
        if not perplexity_passed:
            perplexity = perplexity_stats.get("perplexity", 0.0)
            max_perplexity = perplexity_stats.get("max_perplexity", 0.0)
            return {
                "passed": False,
                "reason": f"perplexity_too_high: {perplexity:.2f} (max: {max_perplexity:.2f})",
                "stats": all_stats
            }

        # All checks passed
        return {
            "passed": True,
            "reason": "passed",
            "stats": all_stats
        }

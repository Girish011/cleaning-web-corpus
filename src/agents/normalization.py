"""
Normalization utilities for mapping free-text terms to canonical values.

Maps user input terms (e.g., "sofa", "couch", "settee") to canonical
surface/dirt/method values used in the data warehouse.
"""

import logging
from typing import Dict, List, Optional, Tuple

from src.enrichment.patterns import (
    SURFACE_KEYWORDS,
    DIRT_KEYWORDS,
    METHOD_KEYWORDS,
)

logger = logging.getLogger(__name__)


class Normalizer:
    """
    Normalizes free-text terms to canonical values for surface, dirt, and method types.
    
    Uses keyword lookup tables from patterns.py to map user input to canonical values.
    """

    def __init__(self):
        """Initialize the normalizer with keyword mappings."""
        # Build reverse lookup: keyword -> canonical value
        self._surface_map = self._build_keyword_map(SURFACE_KEYWORDS)
        self._dirt_map = self._build_keyword_map(DIRT_KEYWORDS)
        self._method_map = self._build_keyword_map(METHOD_KEYWORDS)

        # Canonical values (for validation)
        self._canonical_surfaces = set(SURFACE_KEYWORDS.keys())
        self._canonical_dirt_types = set(DIRT_KEYWORDS.keys())
        self._canonical_methods = set(METHOD_KEYWORDS.keys())

    def _build_keyword_map(self, keyword_dict: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Build reverse lookup map from keywords to canonical values.
        
        Args:
            keyword_dict: Dictionary mapping canonical values to keyword lists
            
        Returns:
            Dictionary mapping keywords (lowercase) to canonical values
        """
        mapping = {}
        for canonical, keywords in keyword_dict.items():
            for keyword in keywords:
                mapping[keyword.lower()] = canonical
        return mapping

    def normalize_surface(self, term: str) -> Optional[str]:
        """
        Normalize a surface term to canonical value.
        
        Args:
            term: Free-text surface term (e.g., "sofa", "couch", "settee")
            
        Returns:
            Canonical surface type or None if not found
        """
        if not term:
            return None

        term_lower = term.lower().strip()

        # Direct lookup
        if term_lower in self._surface_map:
            return self._surface_map[term_lower]

        # Check if term is already canonical
        if term_lower in self._canonical_surfaces:
            return term_lower

        # Try partial matching (e.g., "upholstered furniture" contains "upholstery")
        for keyword, canonical in self._surface_map.items():
            if keyword in term_lower or term_lower in keyword:
                return canonical

        logger.debug(f"Could not normalize surface term: {term}")
        return None

    def normalize_dirt(self, term: str) -> Optional[str]:
        """
        Normalize a dirt type term to canonical value.
        
        Args:
            term: Free-text dirt term (e.g., "red wine", "coffee", "ink")
            
        Returns:
            Canonical dirt type or None if not found
        """
        if not term:
            return None

        term_lower = term.lower().strip()

        # Direct lookup
        if term_lower in self._dirt_map:
            return self._dirt_map[term_lower]

        # Check if term is already canonical
        if term_lower in self._canonical_dirt_types:
            return term_lower

        # Try partial matching
        for keyword, canonical in self._dirt_map.items():
            if keyword in term_lower or term_lower in keyword:
                return canonical

        logger.debug(f"Could not normalize dirt term: {term}")
        return None

    def normalize_method(self, term: str) -> Optional[str]:
        """
        Normalize a cleaning method term to canonical value.
        
        Args:
            term: Free-text method term (e.g., "spot treat", "spot clean")
            
        Returns:
            Canonical method or None if not found
        """
        if not term:
            return None

        term_lower = term.lower().strip().replace(" ", "_")

        # Direct lookup
        if term_lower in self._method_map:
            return self._method_map[term_lower]

        # Check if term is already canonical
        if term_lower in self._canonical_methods:
            return term_lower

        # Try partial matching
        for keyword, canonical in self._method_map.items():
            if keyword in term_lower or term_lower in keyword:
                return canonical

        logger.debug(f"Could not normalize method term: {term}")
        return None

    def extract_and_normalize(
        self, text: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract and normalize surface, dirt, and method from free text.
        
        Args:
            text: Free-text query or description
            
        Returns:
            Tuple of (surface_type, dirt_type, cleaning_method) or None for each
        """
        text_lower = text.lower()

        # Find best matches using keyword matching
        surface = None
        dirt = None
        method = None

        # Try to find surface
        for keyword, canonical in self._surface_map.items():
            if keyword in text_lower:
                surface = canonical
                break

        # Try to find dirt type
        for keyword, canonical in self._dirt_map.items():
            if keyword in text_lower:
                dirt = canonical
                break

        # Try to find method
        for keyword, canonical in self._method_map.items():
            if keyword in text_lower:
                method = canonical
                break

        return surface, dirt, method

    def detect_wool_nuance(self, text: str) -> bool:
        """
        Detect if query mentions wool material (wool carpet, wool rug, woolen rug, etc.).
        
        Args:
            text: Free-text query or description
            
        Returns:
            True if wool is mentioned, False otherwise
        """
        if not text:
            return False

        text_lower = text.lower()
        wool_keywords = ["wool", "woolen", "woollen"]

        # Check for wool keywords
        for keyword in wool_keywords:
            if keyword in text_lower:
                return True

        return False

    def is_valid_surface(self, value: str) -> bool:
        """Check if a surface value is canonical."""
        return value.lower() in self._canonical_surfaces

    def is_valid_dirt(self, value: str) -> bool:
        """Check if a dirt type value is canonical."""
        return value.lower() in self._canonical_dirt_types

    def is_valid_method(self, value: str) -> bool:
        """Check if a method value is canonical."""
        return value.lower() in self._canonical_methods

    def get_canonical_surfaces(self) -> List[str]:
        """Get list of all canonical surface types."""
        return sorted(list(self._canonical_surfaces))

    def get_canonical_dirt_types(self) -> List[str]:
        """Get list of all canonical dirt types."""
        return sorted(list(self._canonical_dirt_types))

    def get_canonical_methods(self) -> List[str]:
        """Get list of all canonical cleaning methods."""
        return sorted(list(self._canonical_methods))


# Global normalizer instance
_normalizer: Optional[Normalizer] = None


def get_normalizer() -> Normalizer:
    """Get or create the global normalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = Normalizer()
    return _normalizer


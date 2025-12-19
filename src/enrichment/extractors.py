"""
Rule-based extraction classes for structured information extraction.

This module provides rule-based extractors that use pattern matching
and keyword detection to extract structured information from text.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

from src.enrichment.patterns import (
    SURFACE_KEYWORDS,
    DIRT_KEYWORDS,
    METHOD_KEYWORDS,
    TOOL_KEYWORDS,
    STEP_PATTERNS,
    STEP_INDICATORS,
    ACTION_VERBS,
    find_keywords_in_text,
    extract_best_match,
    extract_all_matches,
)

logger = logging.getLogger(__name__)


class RuleBasedExtractor:
    """
    Rule-based extractor for structured information from cleaning-related text.
    
    Extracts:
    - surface_type: Type of surface being cleaned
    - dirt_type: Type of dirt/stain/issue
    - cleaning_method: Method used for cleaning
    - tools: List of cleaning tools/equipment mentioned
    - steps: List of structured cleaning procedure steps
    """
    
    def __init__(
        self,
        enable_tools_extraction: bool = True,
        enable_steps_extraction: bool = True,
        min_steps_confidence: float = 0.5,
    ):
        """
        Initialize the rule-based extractor.
        
        Args:
            enable_tools_extraction: Whether to extract tools
            enable_steps_extraction: Whether to extract steps
            min_steps_confidence: Minimum confidence for step extraction
        """
        self.enable_tools_extraction = enable_tools_extraction
        self.enable_steps_extraction = enable_steps_extraction
        self.min_steps_confidence = min_steps_confidence
    
    def extract_surface_type(self, text: str, url: str = "") -> Tuple[str, float]:
        """
        Extract surface type from text.
        
        Args:
            text: Text content
            url: URL (optional, for context)
            
        Returns:
            Tuple of (surface_type, confidence_score)
        """
        matches = find_keywords_in_text(text, SURFACE_KEYWORDS)
        surface_type, confidence = extract_best_match(matches, default="other")
        
        # Boost confidence if URL contains relevant keywords
        if url:
            url_lower = url.lower()
            for category, keywords in SURFACE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in url_lower:
                        if category == surface_type:
                            confidence = min(1.0, confidence + 0.2)
                        break
        
        return surface_type, confidence
    
    def extract_dirt_type(self, text: str) -> Tuple[str, float]:
        """
        Extract dirt type from text.
        
        Args:
            text: Text content
            
        Returns:
            Tuple of (dirt_type, confidence_score)
        """
        matches = find_keywords_in_text(text, DIRT_KEYWORDS)
        dirt_type, confidence = extract_best_match(matches, default="general")
        return dirt_type, confidence
    
    def extract_cleaning_method(self, text: str) -> Tuple[str, float]:
        """
        Extract cleaning method from text.
        
        Args:
            text: Text content
            
        Returns:
            Tuple of (cleaning_method, confidence_score)
        """
        matches = find_keywords_in_text(text, METHOD_KEYWORDS)
        method, confidence = extract_best_match(matches, default="other")
        return method, confidence
    
    def extract_tools(self, text: str) -> List[Dict[str, any]]:
        """
        Extract cleaning tools/equipment mentioned in text.
        
        Args:
            text: Text content
            
        Returns:
            List of tool dictionaries with 'name' and 'confidence' keys
        """
        if not self.enable_tools_extraction:
            return []
        
        matches = find_keywords_in_text(text, TOOL_KEYWORDS)
        
        # Get all tools above threshold
        tool_matches = extract_all_matches(matches, threshold=0.1)
        
        tools = []
        for tool_name, confidence in tool_matches:
            tools.append({
                "name": tool_name,
                "confidence": round(confidence, 3)
            })
        
        return tools
    
    def extract_steps(self, text: str) -> List[Dict[str, any]]:
        """
        Extract structured cleaning procedure steps from text.
        
        Args:
            text: Text content
            
        Returns:
            List of step dictionaries with 'step', 'order', and 'confidence' keys
        """
        if not self.enable_steps_extraction:
            return []
        
        steps = []
        text_lower = text.lower()
        
        # Try each pattern to find steps
        for pattern_idx, pattern in enumerate(STEP_PATTERNS):
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Pattern with groups (e.g., step number and content)
                    if len(match) == 2:
                        step_num, step_text = match
                        step_text = step_text.strip()
                    else:
                        step_text = match[0].strip() if match else ""
                else:
                    step_text = match.strip() if match else ""
                
                if step_text and len(step_text) > 10:  # Minimum step length
                    # Calculate confidence based on pattern type and content
                    confidence = self._calculate_step_confidence(step_text, pattern_idx)
                    
                    if confidence >= self.min_steps_confidence:
                        steps.append({
                            "step": step_text,
                            "order": len(steps) + 1,
                            "confidence": round(confidence, 3)
                        })
        
        # If no structured steps found, try to extract from sentences
        if not steps:
            steps = self._extract_steps_from_sentences(text)
        
        # Remove duplicates (similar steps)
        steps = self._deduplicate_steps(steps)
        
        return steps
    
    def _calculate_step_confidence(self, step_text: str, pattern_idx: int) -> float:
        """
        Calculate confidence score for a step.
        
        Args:
            step_text: Step text
            pattern_idx: Index of pattern that matched
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Boost confidence for numbered steps (pattern 0)
        if pattern_idx == 0:
            confidence += 0.2
        
        # Boost confidence if step starts with action verb
        step_lower = step_text.lower()
        for verb in ACTION_VERBS:
            if step_lower.startswith(verb):
                confidence += 0.2
                break
        
        # Boost confidence if step contains cleaning-related keywords
        cleaning_keywords = ["clean", "remove", "apply", "rinse", "dry", "wipe", "scrub"]
        for keyword in cleaning_keywords:
            if keyword in step_lower:
                confidence += 0.1
                break
        
        # Penalize very short or very long steps
        if len(step_text) < 20:
            confidence -= 0.1
        elif len(step_text) > 200:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _extract_steps_from_sentences(self, text: str) -> List[Dict[str, any]]:
        """
        Extract steps from sentences when structured patterns don't match.
        
        Args:
            text: Text content
            
        Returns:
            List of step dictionaries
        """
        steps = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 20:
                continue
            
            sentence_lower = sentence.lower()
            
            # Check if sentence looks like a step
            is_step = False
            confidence = 0.3
            
            # Check for step indicators
            for indicator in STEP_INDICATORS:
                if indicator in sentence_lower:
                    is_step = True
                    confidence += 0.2
                    break
            
            # Check if starts with action verb
            for verb in ACTION_VERBS:
                if sentence_lower.startswith(verb):
                    is_step = True
                    confidence += 0.3
                    break
            
            # Check for imperative structure (no subject, starts with verb)
            if is_step and confidence >= self.min_steps_confidence:
                steps.append({
                    "step": sentence,
                    "order": len(steps) + 1,
                    "confidence": round(confidence, 3)
                })
        
        return steps[:10]  # Limit to 10 steps
    
    def _deduplicate_steps(self, steps: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Remove duplicate or very similar steps.
        
        Args:
            steps: List of step dictionaries
            
        Returns:
            Deduplicated list of steps
        """
        if not steps:
            return []
        
        unique_steps = []
        seen_texts = set()
        
        for step in steps:
            step_text_lower = step["step"].lower()
            
            # Check for exact duplicates
            if step_text_lower in seen_texts:
                continue
            
            # Check for similar steps (simple word overlap)
            is_duplicate = False
            step_words = set(step_text_lower.split())
            
            for seen_text in seen_texts:
                seen_words = set(seen_text.split())
                # If >80% word overlap, consider duplicate
                if len(step_words) > 0 and len(seen_words) > 0:
                    overlap = len(step_words & seen_words) / max(len(step_words), len(seen_words))
                    if overlap > 0.8:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_steps.append(step)
                seen_texts.add(step_text_lower)
        
        # Reorder steps
        for idx, step in enumerate(unique_steps, 1):
            step["order"] = idx
        
        return unique_steps
    
    def extract_all(self, text: str, url: str = "") -> Dict[str, any]:
        """
        Extract all structured information from text.
        
        Args:
            text: Text content
            url: URL (optional, for context)
            
        Returns:
            Dictionary with all extracted information and metadata
        """
        surface_type, surface_confidence = self.extract_surface_type(text, url)
        dirt_type, dirt_confidence = self.extract_dirt_type(text)
        cleaning_method, method_confidence = self.extract_cleaning_method(text)
        tools = self.extract_tools(text)
        steps = self.extract_steps(text)
        
        return {
            "surface_type": surface_type,
            "dirt_type": dirt_type,
            "cleaning_method": cleaning_method,
            "tools": [tool["name"] for tool in tools],  # Simple list of tool names
            "tools_detailed": tools,  # Detailed with confidence
            "steps": [step["step"] for step in steps],  # Simple list of step texts
            "steps_detailed": steps,  # Detailed with order and confidence
            "extraction_metadata": {
                "extraction_method": "rule_based",
                "confidence": {
                    "surface_type": round(surface_confidence, 3),
                    "dirt_type": round(dirt_confidence, 3),
                    "cleaning_method": round(method_confidence, 3),
                    "tools": round(sum(t["confidence"] for t in tools) / max(1, len(tools)), 3) if tools else 0.0,
                    "steps": round(sum(s["confidence"] for s in steps) / max(1, len(steps)), 3) if steps else 0.0,
                }
            }
        }

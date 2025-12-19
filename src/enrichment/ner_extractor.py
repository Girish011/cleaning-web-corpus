"""
NER-based extraction using spaCy.

This module provides Named Entity Recognition (NER) based extraction
for structured information from cleaning-related text.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import spaCy, handle gracefully if not available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning(
        "spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm"
    )

from src.enrichment.patterns import (
    SURFACE_KEYWORDS,
    DIRT_KEYWORDS,
    METHOD_KEYWORDS,
    TOOL_KEYWORDS,
    find_keywords_in_text,
    extract_best_match,
)


class NERExtractor:
    """
    NER-based extractor using spaCy for structured information extraction.
    
    Uses spaCy's NER model to identify entities and combines with
    keyword matching for better accuracy.
    """
    
    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        enable_tools_extraction: bool = True,
        enable_steps_extraction: bool = True,
        min_steps_confidence: float = 0.5,
    ):
        """
        Initialize the NER extractor.
        
        Args:
            model_name: spaCy model name (default: "en_core_web_sm")
            enable_tools_extraction: Whether to extract tools
            enable_steps_extraction: Whether to extract steps
            min_steps_confidence: Minimum confidence for step extraction
        """
        self.enable_tools_extraction = enable_tools_extraction
        self.enable_steps_extraction = enable_steps_extraction
        self.min_steps_confidence = min_steps_confidence
        
        if not SPACY_AVAILABLE:
            self._nlp = None
            logger.warning("spaCy not available, NER extraction will be limited")
            return
        
        try:
            # Load spaCy model
            self._nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.warning(
                f"spaCy model '{model_name}' not found. "
                f"Install with: python -m spacy download {model_name}"
            )
            self._nlp = None
        except Exception as e:
            logger.error(f"Error loading spaCy model: {e}")
            self._nlp = None
    
    def is_available(self) -> bool:
        """Check if NER is available and loaded."""
        return SPACY_AVAILABLE and self._nlp is not None
    
    def extract_surface_type(self, text: str, url: str = "") -> Tuple[str, float]:
        """
        Extract surface type using NER and keyword matching.
        
        Args:
            text: Text content
            url: URL (optional, for context)
            
        Returns:
            Tuple of (surface_type, confidence_score)
        """
        # Use keyword matching as base (same as rule-based)
        matches = find_keywords_in_text(text, SURFACE_KEYWORDS)
        surface_type, confidence = extract_best_match(matches, default="other")
        
        # Enhance with NER if available
        if self.is_available():
            doc = self._nlp(text)
            
            # Look for material/surface entities
            for ent in doc.ents:
                ent_text = ent.text.lower()
                ent_label = ent.label_
                
                # Check if entity matches surface keywords
                for category, keywords in SURFACE_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in ent_text:
                            # Boost confidence if NER found it
                            if category == surface_type:
                                confidence = min(1.0, confidence + 0.1)
                            break
        
        return surface_type, confidence
    
    def extract_dirt_type(self, text: str) -> Tuple[str, float]:
        """
        Extract dirt type using NER and keyword matching.
        
        Args:
            text: Text content
            
        Returns:
            Tuple of (dirt_type, confidence_score)
        """
        # Use keyword matching as base
        matches = find_keywords_in_text(text, DIRT_KEYWORDS)
        dirt_type, confidence = extract_best_match(matches, default="general")
        
        # Enhance with NER if available
        if self.is_available():
            doc = self._nlp(text)
            
            # Look for relevant entities
            for ent in doc.ents:
                ent_text = ent.text.lower()
                
                # Check if entity matches dirt keywords
                for category, keywords in DIRT_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in ent_text:
                            if category == dirt_type:
                                confidence = min(1.0, confidence + 0.1)
                            break
        
        return dirt_type, confidence
    
    def extract_cleaning_method(self, text: str) -> Tuple[str, float]:
        """
        Extract cleaning method using NER and keyword matching.
        
        Args:
            text: Text content
            
        Returns:
            Tuple of (cleaning_method, confidence_score)
        """
        # Use keyword matching as base
        matches = find_keywords_in_text(text, METHOD_KEYWORDS)
        method, confidence = extract_best_match(matches, default="other")
        
        # Enhance with NER if available
        if self.is_available():
            doc = self._nlp(text)
            
            # Look for action verbs and methods
            for token in doc:
                if token.pos_ == "VERB":
                    token_text = token.text.lower()
                    for category, keywords in METHOD_KEYWORDS.items():
                        for keyword in keywords:
                            if keyword in token_text:
                                if category == method:
                                    confidence = min(1.0, confidence + 0.1)
                                break
        
        return method, confidence
    
    def extract_tools(self, text: str) -> List[Dict[str, any]]:
        """
        Extract cleaning tools using NER and keyword matching.
        
        Args:
            text: Text content
            
        Returns:
            List of tool dictionaries with 'name' and 'confidence' keys
        """
        if not self.enable_tools_extraction:
            return []
        
        # Use keyword matching as base
        matches = find_keywords_in_text(text, TOOL_KEYWORDS)
        
        tools = []
        seen_tools = set()
        
        # Add tools from keyword matching
        for tool_name, confidence in matches.items():
            if confidence > 0.1 and tool_name not in seen_tools:
                tools.append({
                    "name": tool_name,
                    "confidence": round(confidence, 3),
                    "source": "keyword"
                })
                seen_tools.add(tool_name)
        
        # Enhance with NER if available
        if self.is_available():
            doc = self._nlp(text)
            
            # Look for product/object entities that might be tools
            for ent in doc.ents:
                ent_text = ent.text.lower()
                ent_label = ent.label_
                
                # Check if entity matches tool keywords
                for tool_name, keywords in TOOL_KEYWORDS.items():
                    if tool_name in seen_tools:
                        continue
                    
                    for keyword in keywords:
                        if keyword in ent_text:
                            # NER found a tool
                            tools.append({
                                "name": tool_name,
                                "confidence": 0.7,  # NER confidence
                                "source": "ner"
                            })
                            seen_tools.add(tool_name)
                            break
        
        # Sort by confidence
        tools.sort(key=lambda x: x["confidence"], reverse=True)
        
        return tools
    
    def extract_steps(self, text: str) -> List[Dict[str, any]]:
        """
        Extract cleaning steps using NER and sentence analysis.
        
        Args:
            text: Text content
            
        Returns:
            List of step dictionaries with 'step', 'order', and 'confidence' keys
        """
        if not self.enable_steps_extraction:
            return []
        
        steps = []
        
        if self.is_available():
            doc = self._nlp(text)
            
            # Split into sentences
            for sent_idx, sent in enumerate(doc.sents, 1):
                sent_text = sent.text.strip()
                
                if len(sent_text) < 20:  # Skip very short sentences
                    continue
                
                # Check if sentence looks like a step
                confidence = self._calculate_step_confidence_ner(sent)
                
                if confidence >= self.min_steps_confidence:
                    steps.append({
                        "step": sent_text,
                        "order": len(steps) + 1,
                        "confidence": round(confidence, 3),
                        "source": "ner"
                    })
        
        # Limit to reasonable number of steps
        return steps[:15]
    
    def _calculate_step_confidence_ner(self, sent) -> float:
        """
        Calculate confidence that a sentence is a cleaning step.
        
        Args:
            sent: spaCy sentence object
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.3  # Base confidence
        
        # Check for imperative verbs (commands/instructions)
        for token in sent:
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                # Root verb suggests action/instruction
                confidence += 0.2
                
                # Check for imperative mood
                if token.tag_ in ["VB", "VBP"]:  # Base form verbs
                    confidence += 0.2
                break
        
        # Check for step indicators
        step_indicators = ["first", "second", "then", "next", "finally", "step"]
        for token in sent:
            if token.text.lower() in step_indicators:
                confidence += 0.2
                break
        
        # Check for numbers (step numbers)
        for token in sent:
            if token.like_num:
                confidence += 0.1
                break
        
        # Check for action verbs
        action_verbs = ["mix", "apply", "spray", "wipe", "scrub", "rinse", "dry", "clean"]
        for token in sent:
            if token.text.lower() in action_verbs:
                confidence += 0.2
                break
        
        return min(1.0, confidence)
    
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
            "tools": [tool["name"] for tool in tools],  # Simple list
            "tools_detailed": tools,  # Detailed with confidence
            "steps": [step["step"] for step in steps],  # Simple list
            "steps_detailed": steps,  # Detailed with order and confidence
            "extraction_metadata": {
                "extraction_method": "ner",
                "spacy_available": self.is_available(),
                "confidence": {
                    "surface_type": round(surface_confidence, 3),
                    "dirt_type": round(dirt_confidence, 3),
                    "cleaning_method": round(method_confidence, 3),
                    "tools": round(sum(t["confidence"] for t in tools) / max(1, len(tools)), 3) if tools else 0.0,
                    "steps": round(sum(s["confidence"] for s in steps) / max(1, len(steps)), 3) if steps else 0.0,
                }
            }
        }

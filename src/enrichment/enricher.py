"""
Data enrichment orchestrator.

This module provides the main enrichment pipeline that applies
structured extraction and other enrichment steps to documents.
"""

import logging
from typing import Dict, Optional

from src.enrichment.extractors import RuleBasedExtractor
from src.enrichment.ner_extractor import NERExtractor
from src.enrichment.llm_extractor import LLMExtractor

logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """
    Main enrichment pipeline for adding structured information to documents.
    
    Currently supports:
    - Rule-based structured extraction (Phase 4.1)
    - Future: NER/LLM extraction (Phase 4.2)
    - Future: Image captioning (Phase 4.3)
    """
    
    def __init__(
        self,
        extraction_method: str = "rule_based",
        enable_tools_extraction: bool = True,
        enable_steps_extraction: bool = True,
        min_steps_confidence: float = 0.5,
        # NER config
        ner_model_name: str = "en_core_web_sm",
        # LLM config
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini",
        llm_api_key: Optional[str] = None,
        llm_temperature: float = 0.1,
        llm_max_tokens: int = 500,
        llm_enable_caching: bool = True,
        llm_cache_ttl_days: int = 30,
    ):
        """
        Initialize the enrichment pipeline.
        
        Args:
            extraction_method: Extraction method to use ("rule_based", "ner", "llm")
            enable_tools_extraction: Whether to extract tools
            enable_steps_extraction: Whether to extract steps
            min_steps_confidence: Minimum confidence for step extraction
            ner_model_name: spaCy model name for NER
            llm_provider: LLM provider ("openai", "anthropic", "ollama")
            llm_model: LLM model name
            llm_api_key: LLM API key (if None, tries env vars)
            llm_temperature: LLM temperature
            llm_max_tokens: LLM max tokens
            llm_enable_caching: Whether to cache LLM responses
            llm_cache_ttl_days: LLM cache TTL in days
        """
        self.extraction_method = extraction_method
        self.enable_tools_extraction = enable_tools_extraction
        self.enable_steps_extraction = enable_steps_extraction
        self.min_steps_confidence = min_steps_confidence
        
        # Initialize extractor based on method
        if extraction_method == "rule_based":
            self.extractor = RuleBasedExtractor(
                enable_tools_extraction=enable_tools_extraction,
                enable_steps_extraction=enable_steps_extraction,
                min_steps_confidence=min_steps_confidence,
            )
        elif extraction_method == "ner":
            self.extractor = NERExtractor(
                model_name=ner_model_name,
                enable_tools_extraction=enable_tools_extraction,
                enable_steps_extraction=enable_steps_extraction,
                min_steps_confidence=min_steps_confidence,
            )
            if not self.extractor.is_available():
                logger.warning("NER not available, falling back to rule_based")
                self.extractor = RuleBasedExtractor(
                    enable_tools_extraction=enable_tools_extraction,
                    enable_steps_extraction=enable_steps_extraction,
                    min_steps_confidence=min_steps_confidence,
                )
                self.extraction_method = "rule_based"  # Update method
        elif extraction_method == "llm":
            self.extractor = LLMExtractor(
                provider=llm_provider,
                model=llm_model,
                api_key=llm_api_key,
                temperature=llm_temperature,
                max_tokens=llm_max_tokens,
                enable_caching=llm_enable_caching,
                cache_ttl_days=llm_cache_ttl_days,
                enable_tools_extraction=enable_tools_extraction,
                enable_steps_extraction=enable_steps_extraction,
                min_steps_confidence=min_steps_confidence,
            )
            if not self.extractor.is_available():
                logger.warning("LLM not available, falling back to rule_based")
                self.extractor = RuleBasedExtractor(
                    enable_tools_extraction=enable_tools_extraction,
                    enable_steps_extraction=enable_steps_extraction,
                    min_steps_confidence=min_steps_confidence,
                )
                self.extraction_method = "rule_based"  # Update method
        else:
            raise ValueError(f"Unknown extraction method: {extraction_method}")
    
    def enrich(self, document: Dict) -> Dict:
        """
        Enrich a document with structured information.
        
        Args:
            document: Document dictionary with at least 'main_text' and 'url' keys
            
        Returns:
            Enriched document with additional fields:
            - surface_type (enhanced)
            - dirt_type (enhanced)
            - cleaning_method (enhanced)
            - tools (list)
            - steps (list)
            - extraction_metadata (dict)
        """
        text = document.get("main_text", "")
        url = document.get("url", "")
        
        if not text:
            logger.debug(f"No text found in document {url}, skipping enrichment")
            return document
        
        try:
            # Extract structured information
            extracted = self.extractor.extract_all(text, url)
            
            # Merge extracted data into document
            # Preserve existing fields, but update with extracted values
            enriched = document.copy()
            
            # Update surface_type, dirt_type, cleaning_method (may override existing)
            enriched["surface_type"] = extracted["surface_type"]
            enriched["dirt_type"] = extracted["dirt_type"]
            enriched["cleaning_method"] = extracted["cleaning_method"]
            
            # Add new fields
            enriched["tools"] = extracted["tools"]
            enriched["steps"] = extracted["steps"]
            
            # Add detailed extraction data (for analysis/debugging)
            enriched["tools_detailed"] = extracted["tools_detailed"]
            enriched["steps_detailed"] = extracted["steps_detailed"]
            enriched["extraction_metadata"] = extracted["extraction_metadata"]
            
            return enriched
            
        except Exception as e:
            logger.error(f"Error enriching document {url}: {e}")
            # Return original document on error (graceful degradation)
            return document
    
    def enrich_batch(self, documents: list[Dict]) -> list[Dict]:
        """
        Enrich a batch of documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of enriched documents
        """
        enriched = []
        for doc in documents:
            enriched_doc = self.enrich(doc)
            enriched.append(enriched_doc)
        
        return enriched

"""
Unit tests for data enrichment functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.enrichment.extractors import RuleBasedExtractor
from src.enrichment.enricher import EnrichmentPipeline
from src.config import ExtractionConfig, EnrichmentConfig

# Check if spaCy is available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class TestRuleBasedExtractor:
    """Test rule-based extraction."""
    
    def test_extract_surface_type_pillows(self):
        """Test surface type extraction for pillows."""
        extractor = RuleBasedExtractor()
        text = "How to clean your pillows and bedding. Remove dust from pillows."
        surface_type, confidence = extractor.extract_surface_type(text)
        assert surface_type == "pillows_bedding"
        assert confidence > 0.0
    
    def test_extract_surface_type_carpets(self):
        """Test surface type extraction for carpets."""
        extractor = RuleBasedExtractor()
        text = "Cleaning carpets and rugs requires special care."
        surface_type, confidence = extractor.extract_surface_type(text)
        assert surface_type == "carpets_floors"
        assert confidence > 0.0
    
    def test_extract_surface_type_clothes(self):
        """Test surface type extraction for clothes."""
        extractor = RuleBasedExtractor()
        text = "Washing shirts and t-shirts in the washing machine."
        surface_type, confidence = extractor.extract_surface_type(text)
        assert surface_type == "clothes"
        assert confidence > 0.0
    
    def test_extract_surface_type_upholstery(self):
        """Test surface type extraction for upholstery."""
        extractor = RuleBasedExtractor()
        text = "How to clean your sofa and upholstered furniture."
        surface_type, confidence = extractor.extract_surface_type(text)
        assert surface_type == "upholstery"
        assert confidence > 0.0
    
    def test_extract_dirt_type_stain(self):
        """Test dirt type extraction for stains."""
        extractor = RuleBasedExtractor()
        text = "Remove coffee stains from your carpet using vinegar."
        dirt_type, confidence = extractor.extract_dirt_type(text)
        assert dirt_type == "stain"
        assert confidence > 0.0
    
    def test_extract_dirt_type_dust(self):
        """Test dirt type extraction for dust."""
        extractor = RuleBasedExtractor()
        text = "Dust and dust mites accumulate on pillows over time."
        dirt_type, confidence = extractor.extract_dirt_type(text)
        assert dirt_type == "dust"
        assert confidence > 0.0
    
    def test_extract_dirt_type_grease(self):
        """Test dirt type extraction for grease."""
        extractor = RuleBasedExtractor()
        text = "Remove grease and oil stains from kitchen surfaces."
        dirt_type, confidence = extractor.extract_dirt_type(text)
        assert dirt_type == "grease"
        assert confidence > 0.0
    
    def test_extract_cleaning_method_vacuum(self):
        """Test cleaning method extraction for vacuuming."""
        extractor = RuleBasedExtractor()
        text = "Vacuum your carpet regularly to remove dust and dirt."
        method, confidence = extractor.extract_cleaning_method(text)
        assert method == "vacuum"
        assert confidence > 0.0
    
    def test_extract_cleaning_method_hand_wash(self):
        """Test cleaning method extraction for hand washing."""
        extractor = RuleBasedExtractor()
        text = "Hand wash delicate fabrics and soak in warm water."
        method, confidence = extractor.extract_cleaning_method(text)
        assert method == "hand_wash"
        assert confidence > 0.0
    
    def test_extract_tools(self):
        """Test tool extraction."""
        extractor = RuleBasedExtractor()
        text = """
        You will need: a vacuum cleaner, microfiber cloth, vinegar, 
        baking soda, and a spray bottle. Use a sponge to scrub.
        """
        tools = extractor.extract_tools(text)
        
        # Should extract multiple tools
        assert len(tools) > 0
        
        # Check tool names
        tool_names = [tool["name"] for tool in tools]
        assert "vacuum" in tool_names
        assert "microfiber_cloth" in tool_names
        assert "vinegar" in tool_names
        assert "baking_soda" in tool_names
        assert "spray_bottle" in tool_names
        assert "sponge" in tool_names
        
        # Check confidence scores
        for tool in tools:
            assert "name" in tool
            assert "confidence" in tool
            assert 0.0 <= tool["confidence"] <= 1.0
    
    def test_extract_tools_disabled(self):
        """Test that tool extraction can be disabled."""
        extractor = RuleBasedExtractor(enable_tools_extraction=False)
        text = "Use a vacuum and microfiber cloth."
        tools = extractor.extract_tools(text)
        assert tools == []
    
    def test_extract_steps_numbered(self):
        """Test step extraction from numbered steps."""
        extractor = RuleBasedExtractor()
        text = """
        Step 1: Mix equal parts vinegar and water in a spray bottle.
        Step 2: Spray the solution onto the stain.
        Step 3: Let it sit for 10 minutes.
        Step 4: Blot with a clean microfiber cloth.
        """
        steps = extractor.extract_steps(text)
        
        assert len(steps) >= 4
        
        # Check step structure
        for step in steps:
            assert "step" in step
            assert "order" in step
            assert "confidence" in step
            assert len(step["step"]) > 10  # Minimum length
            assert 0.0 <= step["confidence"] <= 1.0
        
        # Check ordering
        orders = [step["order"] for step in steps]
        assert orders == sorted(orders)
    
    def test_extract_steps_ordinal(self):
        """Test step extraction from ordinal steps."""
        extractor = RuleBasedExtractor()
        text = """
        First, blot excess liquid with a paper towel.
        Then, apply a cleaning solution.
        Next, let it sit for 5 minutes.
        Finally, rinse with clean water.
        """
        steps = extractor.extract_steps(text)
        
        assert len(steps) >= 3
    
    def test_extract_steps_bullet_points(self):
        """Test step extraction from bullet points."""
        extractor = RuleBasedExtractor()
        text = """
        - Mix vinegar and baking soda
        - Apply to the stain
        - Wait 10 minutes
        - Rinse thoroughly
        """
        steps = extractor.extract_steps(text)
        
        assert len(steps) >= 3
    
    def test_extract_steps_disabled(self):
        """Test that step extraction can be disabled."""
        extractor = RuleBasedExtractor(enable_steps_extraction=False)
        text = "Step 1: Do this. Step 2: Do that."
        steps = extractor.extract_steps(text)
        assert steps == []
    
    def test_extract_steps_confidence_threshold(self):
        """Test step extraction with confidence threshold."""
        extractor = RuleBasedExtractor(min_steps_confidence=0.8)
        text = "Step 1: Mix solution. Some random text that's not a step."
        steps = extractor.extract_steps(text)
        
        # Only high-confidence steps should be included
        for step in steps:
            assert step["confidence"] >= 0.8
    
    def test_extract_all(self):
        """Test extracting all information at once."""
        extractor = RuleBasedExtractor()
        text = """
        How to clean a carpet stain:
        
        Step 1: Blot excess liquid with a paper towel.
        Step 2: Mix equal parts vinegar and water in a spray bottle.
        Step 3: Spray the solution onto the stain.
        Step 4: Let it sit for 10 minutes.
        Step 5: Blot with a clean microfiber cloth.
        
        You'll need: vinegar, water, spray bottle, microfiber cloth, paper towel.
        """
        
        result = extractor.extract_all(text, url="https://example.com/carpet-cleaning")
        
        # Check all fields are present
        assert "surface_type" in result
        assert "dirt_type" in result
        assert "cleaning_method" in result
        assert "tools" in result
        assert "steps" in result
        assert "tools_detailed" in result
        assert "steps_detailed" in result
        assert "extraction_metadata" in result
        
        # Check surface type
        assert result["surface_type"] == "carpets_floors"
        
        # Check dirt type
        assert result["dirt_type"] == "stain"
        
        # Check tools
        assert len(result["tools"]) > 0
        assert "vinegar" in result["tools"]
        assert "microfiber_cloth" in result["tools"]
        
        # Check steps
        assert len(result["steps"]) >= 4
        
        # Check metadata
        metadata = result["extraction_metadata"]
        assert metadata["extraction_method"] == "rule_based"
        assert "confidence" in metadata
        assert "surface_type" in metadata["confidence"]
        assert "dirt_type" in metadata["confidence"]


class TestEnrichmentPipeline:
    """Test enrichment pipeline."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = EnrichmentPipeline(
            extraction_method="rule_based",
            enable_tools_extraction=True,
            enable_steps_extraction=True,
        )
        assert pipeline.extraction_method == "rule_based"
        assert pipeline.extractor is not None
    
    def test_pipeline_enrich(self):
        """Test document enrichment."""
        pipeline = EnrichmentPipeline()
        
        document = {
            "url": "https://example.com/clean-carpet",
            "title": "How to Clean Carpet Stains",
            "main_text": """
            Step 1: Blot the stain with a paper towel.
            Step 2: Mix vinegar and water in a spray bottle.
            Step 3: Apply the solution and let sit.
            
            You'll need: vinegar, water, spray bottle, microfiber cloth.
            """,
        }
        
        enriched = pipeline.enrich(document)
        
        # Check original fields preserved
        assert enriched["url"] == document["url"]
        assert enriched["title"] == document["title"]
        assert enriched["main_text"] == document["main_text"]
        
        # Check enriched fields
        assert "surface_type" in enriched
        assert "dirt_type" in enriched
        assert "cleaning_method" in enriched
        assert "tools" in enriched
        assert "steps" in enriched
        assert "extraction_metadata" in enriched
    
    def test_pipeline_enrich_no_text(self):
        """Test enrichment with no text (graceful handling)."""
        pipeline = EnrichmentPipeline()
        
        document = {
            "url": "https://example.com/page",
            "title": "Page Title",
            "main_text": "",
        }
        
        enriched = pipeline.enrich(document)
        
        # Should return original document
        assert enriched == document
    
    def test_pipeline_enrich_batch(self):
        """Test batch enrichment."""
        pipeline = EnrichmentPipeline()
        
        documents = [
            {
                "url": "https://example.com/1",
                "main_text": "Clean your carpet with a vacuum cleaner.",
            },
            {
                "url": "https://example.com/2",
                "main_text": "Wash clothes in the washing machine.",
            },
        ]
        
        enriched = pipeline.enrich_batch(documents)
        
        assert len(enriched) == 2
        assert "surface_type" in enriched[0]
        assert "surface_type" in enriched[1]
    
    def test_pipeline_error_handling(self):
        """Test that pipeline handles errors gracefully."""
        pipeline = EnrichmentPipeline()
        
        # Invalid document (should not crash)
        document = {
            "url": "https://example.com",
            # Missing main_text
        }
        
        # Should return original document on error
        enriched = pipeline.enrich(document)
        assert enriched == document


class TestEnrichmentConfig:
    """Test enrichment configuration."""
    
    def test_extraction_config_defaults(self):
        """Test default extraction configuration."""
        config = ExtractionConfig()
        assert config.method == "rule_based"
        assert config.enable_tools_extraction is True
        assert config.enable_steps_extraction is True
        assert config.min_steps_confidence == 0.5
    
    def test_extraction_config_custom(self):
        """Test custom extraction configuration."""
        config = ExtractionConfig(
            method="rule_based",
            enable_tools_extraction=False,
            enable_steps_extraction=True,
            min_steps_confidence=0.7,
        )
        assert config.method == "rule_based"
        assert config.enable_tools_extraction is False
        assert config.enable_steps_extraction is True
        assert config.min_steps_confidence == 0.7
    
    def test_enrichment_config(self):
        """Test enrichment configuration."""
        config = EnrichmentConfig()
        assert config.extraction is not None
        assert config.extraction.method == "rule_based"


class TestNERExtractor:
    """Test NER-based extraction."""
    
    def test_ner_extractor_initialization_without_spacy(self):
        """Test NER extractor initialization when spaCy is not available."""
        from src.enrichment.ner_extractor import NERExtractor, SPACY_AVAILABLE
        
        # Mock SPACY_AVAILABLE to False
        with patch('src.enrichment.ner_extractor.SPACY_AVAILABLE', False):
            extractor = NERExtractor()
            assert not extractor.is_available()
            assert extractor._nlp is None
    
    def test_ner_extractor_is_available(self):
        """Test is_available() method."""
        from src.enrichment.ner_extractor import NERExtractor
        
        extractor = NERExtractor()
        # Should return False if spaCy not installed or model not loaded
        # This is expected behavior if spaCy is not installed
        assert isinstance(extractor.is_available(), bool)
    
    @pytest.mark.skipif(
        not SPACY_AVAILABLE,
        reason="spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm"
    )
    def test_ner_extractor_with_spacy(self):
        """Test NER extractor when spaCy is available."""
        from src.enrichment.ner_extractor import NERExtractor
        
        extractor = NERExtractor()
        
        if extractor.is_available():
            text = "Clean your carpet with a vacuum cleaner and remove stains."
            result = extractor.extract_all(text)
            
            assert "surface_type" in result
            assert "dirt_type" in result
            assert "cleaning_method" in result
            assert "tools" in result
            assert "extraction_metadata" in result
            assert result["extraction_metadata"]["extraction_method"] == "ner"
    
    def test_ner_extractor_fallback(self):
        """Test that NER extractor falls back gracefully."""
        from src.enrichment.ner_extractor import NERExtractor
        
        extractor = NERExtractor()
        text = "Clean your carpet with a vacuum."
        
        # Should work even if spaCy not available (uses keyword matching)
        result = extractor.extract_all(text)
        assert "surface_type" in result
        assert result["surface_type"] in ["carpets_floors", "other"]


class TestLLMExtractor:
    """Test LLM-based extraction."""
    
    def test_llm_extractor_initialization(self):
        """Test LLM extractor initialization."""
        from src.enrichment.llm_extractor import LLMExtractor
        
        extractor = LLMExtractor(
            provider="openai",
            model="gpt-4o-mini",
            api_key=None,  # Will try env var
        )
        
        # Should initialize even without API key (will fallback)
        assert extractor.provider == "openai"
        assert extractor.model == "gpt-4o-mini"
    
    def test_llm_extractor_is_available(self):
        """Test is_available() method."""
        from src.enrichment.llm_extractor import LLMExtractor
        
        extractor = LLMExtractor(provider="openai", api_key=None)
        # Should return False if API key not set or library not installed
        assert isinstance(extractor.is_available(), bool)
    
    def test_llm_extractor_fallback(self):
        """Test that LLM extractor falls back to rule-based."""
        from src.enrichment.llm_extractor import LLMExtractor
        
        extractor = LLMExtractor(
            provider="openai",
            model="gpt-4o-mini",
            api_key=None,  # No API key, should fallback
        )
        
        text = "Clean your carpet with a vacuum cleaner."
        result = extractor.extract_all(text)
        
        # Should return result (either from LLM or fallback)
        assert "surface_type" in result
        assert "extraction_metadata" in result
    
    def test_llm_extractor_caching(self):
        """Test LLM extractor caching."""
        from src.enrichment.llm_extractor import LLMExtractor
        
        extractor = LLMExtractor(
            provider="openai",
            enable_caching=True,
        )
        
        # Cache path should be generated
        cache_path = extractor._get_cache_path("test text")
        assert cache_path is None or isinstance(cache_path, Path)
    
    def test_llm_extractor_multiple_providers(self):
        """Test LLM extractor with different providers."""
        from src.enrichment.llm_extractor import LLMExtractor
        
        # Test OpenAI
        extractor_openai = LLMExtractor(provider="openai", api_key=None)
        assert extractor_openai.provider == "openai"
        
        # Test Anthropic
        extractor_anthropic = LLMExtractor(provider="anthropic", api_key=None)
        assert extractor_anthropic.provider == "anthropic"
        
        # Test Ollama
        extractor_ollama = LLMExtractor(provider="ollama", api_key=None)
        assert extractor_ollama.provider == "ollama"


class TestEnrichmentPipelineWithNER:
    """Test enrichment pipeline with NER."""
    
    def test_pipeline_with_ner(self):
        """Test pipeline initialization with NER method."""
        pipeline = EnrichmentPipeline(extraction_method="ner")
        
        # Should initialize (may fallback to rule_based if NER not available)
        assert pipeline.extractor is not None
        assert pipeline.extraction_method in ["ner", "rule_based"]


class TestEnrichmentPipelineWithLLM:
    """Test enrichment pipeline with LLM."""
    
    def test_pipeline_with_llm(self):
        """Test pipeline initialization with LLM method."""
        pipeline = EnrichmentPipeline(
            extraction_method="llm",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            llm_api_key=None,
        )
        
        # Should initialize (may fallback to rule_based if LLM not available)
        assert pipeline.extractor is not None
        assert pipeline.extraction_method in ["llm", "rule_based"]
    
    def test_pipeline_with_llm_anthropic(self):
        """Test pipeline with Anthropic provider."""
        pipeline = EnrichmentPipeline(
            extraction_method="llm",
            llm_provider="anthropic",
            llm_model="claude-3-haiku",
            llm_api_key=None,
        )
        
        assert pipeline.extractor is not None
    
    def test_pipeline_with_llm_ollama(self):
        """Test pipeline with Ollama provider."""
        pipeline = EnrichmentPipeline(
            extraction_method="llm",
            llm_provider="ollama",
            llm_model="llama2",
            llm_api_key=None,
        )
        
        assert pipeline.extractor is not None

# Phase 4.2: NER/LLM Extraction - Implementation Summary

## ✅ Implementation Complete

Phase 4.2 has been successfully implemented! This adds advanced extraction methods using Named Entity Recognition (NER) and Large Language Models (LLMs) as alternatives to rule-based extraction.

## What Was Implemented

### 1. NER Extractor (`src/enrichment/ner_extractor.py`)

**Features:**
- Uses spaCy for Named Entity Recognition
- Combines NER with keyword matching for better accuracy
- Enhances confidence scores when NER finds relevant entities
- Graceful fallback to keyword matching if spaCy unavailable

**How it works:**
1. Uses keyword matching as base (same as rule-based)
2. Enhances with spaCy NER to find entities
3. Boosts confidence when NER confirms keyword matches
4. Extracts tools and steps using sentence analysis

**Configuration:**
- Model: `en_core_web_sm` (default) or `en_core_web_md` for better accuracy
- Can be configured in `configs/default.yaml`

### 2. LLM Extractor (`src/enrichment/llm_extractor.py`)

**Features:**
- Supports multiple LLM providers:
  - **OpenAI**: GPT-4, GPT-3.5, GPT-4o-mini
  - **Anthropic**: Claude 3 (Haiku, Sonnet, Opus)
  - **Ollama**: Local LLMs (Llama2, Mistral, etc.)
- Structured JSON output extraction
- Response caching to reduce API calls
- Automatic fallback to rule-based if LLM unavailable
- Configurable temperature, max tokens, etc.

**How it works:**
1. Creates extraction prompt with JSON schema
2. Calls LLM with structured output request
3. Parses JSON response
4. Normalizes and validates result
5. Caches response for future use
6. Falls back to rule-based if LLM fails

**Caching:**
- Caches LLM responses in `~/.cache/cleaning-corpus/llm/`
- Cache TTL: 30 days (configurable)
- Reduces API costs and improves speed

### 3. Configuration Updates

**config.py:**
- Added `NERConfig` class
- Added `LLMConfig` class
- Extended `ExtractionConfig` with NER/LLM settings

**default.yaml:**
```yaml
enrichment:
  extraction:
    method: "rule_based"  # "rule_based", "ner", "llm"
    ner:
      model_name: "en_core_web_sm"
    llm:
      provider: "openai"  # "openai", "anthropic", "ollama"
      model: "gpt-4o-mini"
      api_key: null  # Set via env vars
      temperature: 0.1
      max_tokens: 500
      enable_caching: true
      cache_ttl_days: 30
```

### 4. Integration

**enricher.py:**
- Updated to support NER and LLM extractors
- Automatic fallback to rule-based if NER/LLM unavailable
- Passes all configuration to extractors

**text_processor.py:**
- Automatically uses configured extraction method
- No code changes needed - works via configuration

## Usage

### Using NER Extraction

1. **Install spaCy and download model:**
   ```bash
   pip install spacy
   python -m spacy download en_core_web_sm
   ```

2. **Update configuration:**
   ```yaml
   enrichment:
     extraction:
       method: "ner"
       ner:
         model_name: "en_core_web_sm"
   ```

3. **Run processor:**
   ```bash
   python -m src.processors.text_processor
   ```

### Using LLM Extraction

1. **Install LLM library (choose one):**
   ```bash
   # For OpenAI
   pip install openai
   
   # For Anthropic
   pip install anthropic
   
   # For Ollama
   pip install ollama
   ```

2. **Set API key (for OpenAI/Anthropic):**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   # or
   export ANTHROPIC_API_KEY="your-key-here"
   ```

3. **For Ollama (local):**
   - Install Ollama: https://ollama.ai
   - Pull model: `ollama pull llama2`
   - No API key needed

4. **Update configuration:**
   ```yaml
   enrichment:
     extraction:
       method: "llm"
       llm:
         provider: "openai"  # or "anthropic", "ollama"
         model: "gpt-4o-mini"
         api_key: null  # Uses env var
   ```

5. **Run processor:**
   ```bash
   python -m src.processors.text_processor
   ```

## Comparison of Methods

| Method | Accuracy | Speed | Cost | Dependencies |
|--------|----------|-------|------|--------------|
| **Rule-based** | Medium | Very Fast | Free | None |
| **NER** | Medium-High | Fast | Free | spaCy + model |
| **LLM** | High | Slow | API costs | LLM library + API key |

## Testing

### Test NER (if spaCy installed):
```bash
pytest tests/test_enrichment.py::TestNERExtractor -v
```

### Test LLM (if API key set):
```bash
# Set API key first
export OPENAI_API_KEY="your-key"
pytest tests/test_enrichment.py::TestLLMExtractor -v
```

### Test Pipeline:
```bash
pytest tests/test_enrichment.py::TestEnrichmentPipelineWithNER -v
pytest tests/test_enrichment.py::TestEnrichmentPipelineWithLLM -v
```

## Graceful Degradation

Both NER and LLM extractors gracefully fall back to rule-based extraction if:
- Dependencies not installed
- API keys not configured
- Models not available
- API errors occur

This ensures the pipeline always works, even if advanced methods aren't available.

## Output Differences

### Rule-based:
```json
{
  "extraction_metadata": {
    "extraction_method": "rule_based",
    "confidence": {...}
  }
}
```

### NER:
```json
{
  "extraction_metadata": {
    "extraction_method": "ner",
    "spacy_available": true,
    "confidence": {...}
  }
}
```

### LLM:
```json
{
  "extraction_metadata": {
    "extraction_method": "llm",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "confidence": {...}
  }
}
```

## Files Created/Modified

### New Files
- `src/enrichment/ner_extractor.py` - NER-based extraction
- `src/enrichment/llm_extractor.py` - LLM-based extraction
- `docs/PHASE4_2_IMPLEMENTATION.md` - This document

### Modified Files
- `src/config.py` - Added NERConfig and LLMConfig
- `configs/default.yaml` - Added NER/LLM configuration
- `src/enrichment/enricher.py` - Support for NER/LLM extractors
- `src/processors/text_processor.py` - Pass NER/LLM config to pipeline
- `src/enrichment/__init__.py` - Export new extractors
- `tests/test_enrichment.py` - Added NER/LLM tests
- `requirements.txt` - Added spaCy (LLM libs are optional)

## Next Steps

- **Phase 4.3**: Image captioning with BLIP-2
- Fine-tune NER model on cleaning domain (optional)
- Add more LLM providers (e.g., Google Gemini, Cohere)

## Notes

- **NER**: Works best with spaCy's medium/large models (`en_core_web_md`, `en_core_web_lg`)
- **LLM**: OpenAI's `gpt-4o-mini` is cost-effective for this use case
- **Caching**: LLM responses are cached to reduce API costs
- **Fallback**: Always falls back to rule-based if advanced methods fail

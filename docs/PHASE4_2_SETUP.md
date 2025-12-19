# Phase 4.2: NER/LLM Setup Guide

## Quick Setup

### Option 1: NER Extraction (Recommended for Testing)

**Install spaCy:**
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

**Test NER:**
```bash
python3 -c "
from src.enrichment.ner_extractor import NERExtractor
extractor = NERExtractor()
if extractor.is_available():
    text = 'Clean your carpet with a vacuum cleaner and remove stains.'
    result = extractor.extract_all(text)
    print('✅ NER working!')
    print(f'Surface: {result[\"surface_type\"]}')
    print(f'Tools: {result[\"tools\"]}')
else:
    print('⚠️  NER not available (spaCy not installed or model not loaded)')
"
```

**Use NER in pipeline:**
1. Edit `configs/default.yaml`:
   ```yaml
   enrichment:
     extraction:
       method: "ner"
   ```
2. Run: `python -m src.processors.text_processor`

### Option 2: LLM Extraction (Requires API Key)

**For OpenAI:**
```bash
# Install library
pip install openai

# Set API key
export OPENAI_API_KEY="your-openai-api-key"

# Test
python3 -c "
from src.enrichment.llm_extractor import LLMExtractor
extractor = LLMExtractor(provider='openai', model='gpt-4o-mini')
if extractor.is_available():
    print('✅ OpenAI LLM ready!')
else:
    print('⚠️  OpenAI not available (check API key)')
"
```

**For Anthropic:**
```bash
# Install library
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Test
python3 -c "
from src.enrichment.llm_extractor import LLMExtractor
extractor = LLMExtractor(provider='anthropic', model='claude-3-haiku')
if extractor.is_available():
    print('✅ Anthropic LLM ready!')
else:
    print('⚠️  Anthropic not available (check API key)')
"
```

**For Ollama (Local):**
```bash
# Install Ollama (see https://ollama.ai)
# Then install Python library
pip install ollama

# Pull a model
ollama pull llama2

# Test
python3 -c "
from src.enrichment.llm_extractor import LLMExtractor
extractor = LLMExtractor(provider='ollama', model='llama2')
if extractor.is_available():
    print('✅ Ollama LLM ready!')
else:
    print('⚠️  Ollama not available (check if Ollama is running)')
"
```

**Use LLM in pipeline:**
1. Edit `configs/default.yaml`:
   ```yaml
   enrichment:
     extraction:
       method: "llm"
       llm:
         provider: "openai"  # or "anthropic", "ollama"
         model: "gpt-4o-mini"
         api_key: null  # Uses env var
   ```
2. Run: `python -m src.processors.text_processor`

## Verification

Check that extraction method is being used:

```bash
# Check output metadata
python3 -c "
import json
with open('data/processed/cleaning_docs.jsonl', 'r') as f:
    doc = json.loads(f.readline())
    method = doc.get('extraction_metadata', {}).get('extraction_method', 'unknown')
    print(f'Extraction method used: {method}')
"
```

## Troubleshooting

### NER Issues

**Problem**: "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

**Problem**: "spaCy not available"
```bash
pip install spacy
```

### LLM Issues

**Problem**: "OpenAI API key not found"
```bash
export OPENAI_API_KEY="your-key"
```

**Problem**: "Anthropic API key not found"
```bash
export ANTHROPIC_API_KEY="your-key"
```

**Problem**: "Ollama connection failed"
- Make sure Ollama is running: `ollama serve`
- Check if model is pulled: `ollama list`

**Problem**: "LLM extraction failed"
- Check API key is valid
- Check you have API credits/quota
- System will automatically fallback to rule-based

## Cost Considerations

- **NER**: Free (runs locally)
- **OpenAI**: ~$0.15 per 1M tokens (gpt-4o-mini)
- **Anthropic**: ~$0.25 per 1M tokens (claude-3-haiku)
- **Ollama**: Free (runs locally, requires GPU for best performance)

**Caching**: LLM responses are cached, so repeated extractions don't cost extra.

## Performance

- **Rule-based**: ~10ms per document
- **NER**: ~50-100ms per document
- **LLM**: ~500-2000ms per document (depends on API latency)

"""
LLM-based extraction using OpenAI, Anthropic, or Ollama.

This module provides LLM-based extraction for structured information
from cleaning-related text using various LLM providers.
"""

import json
import hashlib
import logging
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import LLM libraries
OPENAI_AVAILABLE = False
ANTHROPIC_AVAILABLE = False
OLLAMA_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    pass


class LLMExtractor:
    """
    LLM-based extractor using various providers (OpenAI, Anthropic, Ollama).
    
    Uses LLMs with structured output (JSON) to extract cleaning information.
    Falls back to rule-based if LLM unavailable or API errors occur.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
        enable_caching: bool = True,
        cache_ttl_days: int = 30,
        enable_tools_extraction: bool = True,
        enable_steps_extraction: bool = True,
        min_steps_confidence: float = 0.5,
    ):
        """
        Initialize the LLM extractor.
        
        Args:
            provider: LLM provider ("openai", "anthropic", "ollama")
            model: Model name (e.g., "gpt-4o-mini", "claude-3-haiku", "llama2")
            api_key: API key (if None, tries to get from env vars)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            enable_caching: Whether to cache LLM responses
            cache_ttl_days: Cache TTL in days
            enable_tools_extraction: Whether to extract tools
            enable_steps_extraction: Whether to extract steps
            min_steps_confidence: Minimum confidence for step extraction
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_caching = enable_caching
        self.cache_ttl_days = cache_ttl_days
        self.enable_tools_extraction = enable_tools_extraction
        self.enable_steps_extraction = enable_steps_extraction
        self.min_steps_confidence = min_steps_confidence

        # Initialize provider client
        self._client = None
        self._api_key = api_key or self._get_api_key()

        # Initialize cache directory
        if enable_caching:
            cache_dir = Path.home() / ".cache" / "cleaning-corpus" / "llm"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_dir = cache_dir
        else:
            self._cache_dir = None

        # Initialize provider
        self._init_provider()

        # Fallback to rule-based if LLM not available
        if not self.is_available():
            logger.warning("LLM not available, will use rule-based fallback")
            from src.enrichment.extractors import RuleBasedExtractor
            self._fallback_extractor = RuleBasedExtractor(
                enable_tools_extraction=enable_tools_extraction,
                enable_steps_extraction=enable_steps_extraction,
                min_steps_confidence=min_steps_confidence,
            )
        else:
            self._fallback_extractor = None

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        elif self.provider == "ollama":
            # Ollama doesn't require API key, but check for base URL
            return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return None

    def _init_provider(self):
        """Initialize the LLM provider client."""
        try:
            if self.provider == "openai":
                if not OPENAI_AVAILABLE:
                    logger.warning("OpenAI library not available. Install with: pip install openai")
                    return
                if not self._api_key:
                    logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
                    return
                self._client = openai.OpenAI(api_key=self._api_key)
                logger.info("OpenAI client initialized")

            elif self.provider == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    logger.warning("Anthropic library not available. Install with: pip install anthropic")
                    return
                if not self._api_key:
                    logger.warning("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
                    return
                self._client = anthropic.Anthropic(api_key=self._api_key)
                logger.info("Anthropic client initialized")

            elif self.provider == "ollama":
                if not OLLAMA_AVAILABLE:
                    logger.warning("Ollama library not available. Install with: pip install ollama")
                    return
                # Ollama doesn't need API key, just base URL
                self._client = ollama
                logger.info("Ollama client initialized")

            else:
                logger.error(f"Unknown provider: {self.provider}")

        except Exception as e:
            logger.error(f"Error initializing {self.provider} client: {e}")
            self._client = None

    def is_available(self) -> bool:
        """Check if LLM is available and configured."""
        return self._client is not None

    def _get_cache_path(self, text: str) -> Optional[Path]:
        """Get cache file path for text."""
        if not self._cache_dir:
            return None

        # Create hash of text + extraction settings
        cache_key = f"{text}_{self.provider}_{self.model}_{self.enable_tools_extraction}_{self.enable_steps_extraction}"
        cache_hash = hashlib.md5(cache_key.encode(), usedforsecurity=False).hexdigest()
        return self._cache_dir / f"{cache_hash}.json"

    def _load_from_cache(self, cache_path: Path) -> Optional[Dict]:
        """Load result from cache if valid."""
        if not cache_path.exists():
            return None

        try:
            import time
            # Check if cache is still valid
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age > (self.cache_ttl_days * 24 * 60 * 60):
                return None  # Cache expired

            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f"Error loading cache: {e}")
            return None

    def _save_to_cache(self, cache_path: Path, result: Dict):
        """Save result to cache."""
        try:
            with open(cache_path, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            logger.debug(f"Error saving cache: {e}")

    def _create_extraction_prompt(self, text: str) -> str:
        """Create prompt for LLM extraction."""
        prompt = f"""Extract structured cleaning information from the following text.

Text:
{text}

Extract the following information:
1. surface_type: Type of surface being cleaned (pillows_bedding, clothes, carpets_floors, upholstery, hard_surfaces, appliances, bathroom, outdoor, or other)
2. dirt_type: Type of dirt/stain/issue (dust, stain, odor, grease, mold, pet_hair, water_stain, ink, or general)
3. cleaning_method: Cleaning method used (washing_machine, hand_wash, vacuum, spot_clean, steam_clean, dry_clean, wipe, scrub, or other)
4. tools: List of cleaning tools/equipment mentioned (e.g., ["vacuum", "vinegar", "microfiber_cloth"])
5. steps: List of cleaning procedure steps in order (e.g., ["Mix solution", "Apply to stain", "Let sit 10 minutes"])

Return a JSON object with these fields. Be precise and only include information explicitly mentioned in the text."""

        if not self.enable_tools_extraction:
            prompt += "\n\nNote: Do not extract tools."
        if not self.enable_steps_extraction:
            prompt += "\n\nNote: Do not extract steps."

        prompt += "\n\nReturn only valid JSON, no additional text."

        return prompt

    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM and return response."""
        if not self.is_available():
            return None

        try:
            if self.provider == "openai":
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts structured information from cleaning-related text. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={
                        "type": "json_object"} if "gpt-4" in self.model or "gpt-3.5" in self.model else None,
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system="You are a helpful assistant that extracts structured information from cleaning-related text. Always return valid JSON.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                )
                return response.content[0].text

            elif self.provider == "ollama":
                response = self._client.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    }
                )
                return response.get("response", "")

        except Exception as e:
            logger.error(f"Error calling {self.provider} LLM: {e}")
            return None

        return None

    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """Parse LLM JSON response."""
        if not response:
            return None

        try:
            # Try to extract JSON from response (in case LLM adds extra text)
            response = response.strip()

            # Find JSON object in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing entire response
                return json.loads(response)

        except json.JSONDecodeError as e:
            logger.debug(f"Error parsing LLM JSON response: {e}")
            logger.debug(f"Response: {response[:200]}")
            return None

    def extract_all(self, text: str, url: str = "") -> Dict[str, any]:
        """
        Extract all structured information from text using LLM.
        
        Args:
            text: Text content
            url: URL (optional, for context)
            
        Returns:
            Dictionary with all extracted information and metadata
        """
        # Check cache first
        cache_path = self._get_cache_path(text) if self.enable_caching else None
        if cache_path:
            cached_result = self._load_from_cache(cache_path)
            if cached_result:
                logger.debug("Using cached LLM result")
                return cached_result

        # Try LLM extraction
        if self.is_available():
            prompt = self._create_extraction_prompt(text)
            response = self._call_llm(prompt)

            if response:
                parsed = self._parse_llm_response(response)
                if parsed:
                    # Normalize and validate result
                    result = self._normalize_result(parsed)

                    # Save to cache
                    if cache_path:
                        self._save_to_cache(cache_path, result)

                    return result

        # Fallback to rule-based
        logger.debug("Falling back to rule-based extraction")
        if self._fallback_extractor:
            return self._fallback_extractor.extract_all(text, url)
        else:
            # Last resort: return empty structure
            return self._empty_result()

    def _normalize_result(self, parsed: Dict) -> Dict:
        """Normalize and validate LLM extraction result."""
        # Ensure all required fields exist
        result = {
            "surface_type": parsed.get("surface_type", "other"),
            "dirt_type": parsed.get("dirt_type", "general"),
            "cleaning_method": parsed.get("cleaning_method", "other"),
            "tools": parsed.get("tools", []) if self.enable_tools_extraction else [],
            "steps": parsed.get("steps", []) if self.enable_steps_extraction else [],
        }

        # Ensure tools and steps are lists
        if not isinstance(result["tools"], list):
            result["tools"] = []
        if not isinstance(result["steps"], list):
            result["steps"] = []

        # Create detailed versions
        result["tools_detailed"] = [
            {"name": tool, "confidence": 0.9, "source": "llm"}
            for tool in result["tools"]
        ]

        result["steps_detailed"] = [
            {
                "step": step if isinstance(step, str) else str(step),
                "order": idx + 1,
                "confidence": 0.9,
                "source": "llm"
            }
            for idx, step in enumerate(result["steps"])
        ]

        # Add metadata
        result["extraction_metadata"] = {
            "extraction_method": "llm",
            "provider": self.provider,
            "model": self.model,
            "confidence": {
                "surface_type": 0.85,
                "dirt_type": 0.85,
                "cleaning_method": 0.85,
                "tools": 0.9 if result["tools"] else 0.0,
                "steps": 0.9 if result["steps"] else 0.0,
            }
        }

        return result

    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            "surface_type": "other",
            "dirt_type": "general",
            "cleaning_method": "other",
            "tools": [],
            "tools_detailed": [],
            "steps": [],
            "steps_detailed": [],
            "extraction_metadata": {
                "extraction_method": "llm",
                "provider": self.provider,
                "model": self.model,
                "error": "LLM extraction failed and no fallback available",
                "confidence": {
                    "surface_type": 0.0,
                    "dirt_type": 0.0,
                    "cleaning_method": 0.0,
                    "tools": 0.0,
                    "steps": 0.0,
                }
            }
        }

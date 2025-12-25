"""
Configuration management with Pydantic validation.

This module provides type-safe configuration loading and validation
for the cleaning corpus pipeline.
"""

import pathlib
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# Nested Configuration Models
# ============================================================================

class ProjectConfig(BaseModel):
    """Project metadata configuration."""
    name: str = Field(..., description="Project name")
    version: str = Field(..., description="Project version")


class SearchDiscoveryConfig(BaseModel):
    """Search engine discovery configuration."""
    enable: bool = Field(default=False, description="Enable automatic URL discovery")
    provider: Literal["google", "bing", "serpapi"] = Field(
        default="google",
        description="Search engine provider"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key (if None, tries environment variables)"
    )
    search_engine_id: Optional[str] = Field(
        default=None,
        description="Google Custom Search Engine ID (for Google provider)"
    )
    max_results_per_query: int = Field(
        default=100,
        ge=1,
        description="Maximum results per query"
    )
    delay_seconds: float = Field(
        default=1.0,
        ge=0.0,
        description="Delay between API calls"
    )
    max_urls: Optional[int] = Field(
        default=None,
        description="Maximum total URLs to discover (None = no limit)"
    )
    auto_discover: bool = Field(
        default=False,
        description="Automatically discover URLs before crawling"
    )


class CrawlerConfig(BaseModel):
    """Crawler configuration."""
    seeds_file: str = Field(default="data/seeds.txt", description="Path to seeds file")
    download_images: bool = Field(default=True, description="Whether to download images")
    max_images_per_page: int = Field(default=20, ge=1, description="Maximum images per page")
    respect_robots: bool = Field(default=True, description="Respect robots.txt")
    delay_seconds: float = Field(default=1.0, ge=0.0, description="Delay between requests in seconds")
    download_timeout: float = Field(
        default=30.0, ge=1.0, description="Download timeout in seconds (default: 30, was 180)")
    timeout_retry_times: int = Field(
        default=1, ge=0, description="Number of retries for timeout errors (default: 1, was 3)")
    timeout_blacklist: list[str] = Field(
        default_factory=list, description="List of domains to skip due to frequent timeouts")
    images_store: str = Field(default="data/images", description="Path to store downloaded images")
    images_expires_days: int = Field(default=90, ge=1, description="Days to keep images before expiration")
    images_min_height: int = Field(default=110, ge=1, description="Minimum image height in pixels")
    images_min_width: int = Field(default=110, ge=1, description="Minimum image width in pixels")
    search_discovery: SearchDiscoveryConfig = Field(
        default_factory=SearchDiscoveryConfig,
        description="Search engine discovery configuration"
    )


class TextQualityConfig(BaseModel):
    """Text quality filtering configuration."""
    min_words: int = Field(default=500, ge=1, description="Minimum word count")
    max_words: int = Field(default=50000, ge=1, description="Maximum word count")
    min_avg_word_length: float = Field(default=3.0, ge=0.0, description="Minimum average word length")
    language: str = Field(default="en", description="Target language code")

    # Repetition filter settings
    max_char_repetition_ratio: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Maximum ratio of characters that can be from repeated sequences (0.0-1.0)"
    )
    max_word_repetition_ratio: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Maximum ratio of words that can be duplicates (0.0-1.0)"
    )
    max_ngram_repetition: int = Field(
        default=3,
        ge=1,
        description="Maximum number of times an n-gram can appear in text"
    )
    ngram_size: int = Field(
        default=3,
        ge=2,
        le=10,
        description="Size of n-grams to check for repetition (2-10)"
    )
    min_text_length_for_repetition_check: int = Field(
        default=50,
        ge=1,
        description="Minimum text length (in words) to perform repetition checks"
    )

    # Perplexity filter settings (KenLM)
    enable_perplexity_filter: bool = Field(
        default=True,
        description="Enable perplexity-based quality filtering using KenLM"
    )
    kenlm_model_path: Optional[str] = Field(
        default=None,
        description="Path to KenLM language model file (.arpa or .bin). If None, perplexity filter is skipped."
    )
    max_perplexity: float = Field(
        default=1000.0,
        gt=0.0,
        description="Maximum perplexity score allowed. Lower is better (typical range: 50-500 for good text, >1000 for gibberish)"
    )
    min_text_length_for_perplexity: int = Field(
        default=20,
        ge=1,
        description="Minimum text length (in words) to perform perplexity check"
    )

    @field_validator("max_words")
    @classmethod
    def validate_max_words(cls, v, info):
        """Ensure max_words >= min_words."""
        if "min_words" in info.data and v < info.data["min_words"]:
            raise ValueError(f"max_words ({v}) must be >= min_words ({info.data['min_words']})")
        return v


class ImageQualityConfig(BaseModel):
    """Image quality filtering configuration."""
    min_resolution: List[int] = Field(
        default=[224, 224],
        min_length=2,
        max_length=2,
        description="Minimum resolution [width, height]"
    )
    max_aspect_ratio: float = Field(default=3.0, gt=0.0, description="Maximum aspect ratio")
    allowed_formats: List[str] = Field(
        default=["jpg", "jpeg", "png", "webp"],
        description="Allowed image formats"
    )

    # Duplicate detection settings
    enable_duplicate_detection: bool = Field(
        default=True,
        description="Enable duplicate/near-duplicate image detection"
    )
    duplicate_hash_algorithm: Literal["phash", "dhash", "whash", "average_hash"] = Field(
        default="phash",
        description="Perceptual hash algorithm to use (phash=perceptual, dhash=difference, whash=wavelet, average_hash=average)"
    )
    duplicate_similarity_threshold: int = Field(
        default=5,
        ge=0,
        le=64,
        description="Maximum Hamming distance for images to be considered duplicates (0=exact, higher=more lenient, max=64)"
    )
    min_images_for_duplicate_check: int = Field(
        default=2,
        ge=2,
        description="Minimum number of images required to perform duplicate detection"
    )

    @field_validator("min_resolution")
    @classmethod
    def validate_resolution(cls, v):
        """Ensure resolution values are positive."""
        if len(v) != 2 or any(x < 1 for x in v):
            raise ValueError("min_resolution must be [width, height] with positive values")
        return v


class AlignmentConfig(BaseModel):
    """Text-image alignment configuration."""
    min_clip_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum CLIP similarity score for text-image alignment"
    )


class NERConfig(BaseModel):
    """NER extraction configuration."""
    model_name: str = Field(
        default="en_core_web_sm",
        description="spaCy model name (e.g., 'en_core_web_sm', 'en_core_web_md')"
    )


class LLMConfig(BaseModel):
    """LLM extraction configuration."""
    provider: Literal["openai", "anthropic", "ollama"] = Field(
        default="openai",
        description="LLM provider: openai, anthropic, or ollama"
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="Model name (e.g., 'gpt-4o-mini', 'claude-3-haiku', 'llama2')"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key (if None, tries to get from environment variables)"
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0, lower = more deterministic)"
    )
    max_tokens: int = Field(
        default=500,
        ge=1,
        le=4000,
        description="Maximum tokens in LLM response"
    )
    enable_caching: bool = Field(
        default=True,
        description="Whether to cache LLM responses to reduce API calls"
    )
    cache_ttl_days: int = Field(
        default=30,
        ge=1,
        description="Cache TTL in days"
    )


class ExtractionConfig(BaseModel):
    """Structured extraction configuration."""
    method: Literal["rule_based", "ner", "llm"] = Field(
        default="rule_based",
        description="Extraction method: rule_based, ner, or llm"
    )
    enable_tools_extraction: bool = Field(
        default=True,
        description="Whether to extract cleaning tools/equipment"
    )
    enable_steps_extraction: bool = Field(
        default=True,
        description="Whether to extract cleaning procedure steps"
    )
    min_steps_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for step extraction"
    )
    ner: NERConfig = Field(default_factory=NERConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


class WorkflowConfig(BaseModel):
    """Workflow planning configuration."""
    min_steps: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Minimum number of steps required in a workflow (default: 3, can be lowered to 2 for testing)"
    )
    allow_fewer_steps_if_limited_data: bool = Field(
        default=True,
        description="If True, allow workflows with fewer steps if corpus has limited data (min 2 steps)"
    )


class QualityConfig(BaseModel):
    """Quality filtering configuration."""
    text: TextQualityConfig = Field(default_factory=TextQualityConfig)
    image: ImageQualityConfig = Field(default_factory=ImageQualityConfig)
    alignment: AlignmentConfig = Field(default_factory=AlignmentConfig)


class CaptioningConfig(BaseModel):
    """Image captioning configuration."""
    enable: bool = Field(
        default=True,
        description="Whether to enable image captioning"
    )
    model: str = Field(
        default="Salesforce/blip2-opt-2.7b",
        description="BLIP-2 model name (e.g., 'Salesforce/blip2-opt-2.7b', 'Salesforce/blip2-opt-6.7b')"
    )
    device: Optional[str] = Field(
        default=None,
        description="Device to run on ('cuda', 'cpu', or None for auto)"
    )
    max_length: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Maximum caption length in tokens"
    )
    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold (for future use)"
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Optional prompt to guide caption generation (e.g., 'a photo of')"
    )


class EnrichmentConfig(BaseModel):
    """Data enrichment configuration."""
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    captioning: CaptioningConfig = Field(default_factory=CaptioningConfig)


class ProcessingConfig(BaseModel):
    """Processing pipeline configuration."""
    batch_size: int = Field(default=100, ge=1, description="Batch size for processing")
    num_workers: int = Field(default=4, ge=1, description="Number of worker processes")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    format: str = Field(
        default="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        description="Log format string"
    )


class ClickHouseConfig(BaseModel):
    """ClickHouse database configuration."""
    host: str = Field(
        default="localhost",
        description="ClickHouse server host"
    )
    port: int = Field(
        default=9000,
        ge=1,
        le=65535,
        description="ClickHouse native protocol port (default: 9000)"
    )
    database: str = Field(
        default="cleaning_warehouse",
        description="ClickHouse database name"
    )
    user: str = Field(
        default="default",
        description="ClickHouse username"
    )
    password: str = Field(
        default="",
        description="ClickHouse password (empty string for no password)"
    )
    connect_timeout: float = Field(
        default=10.0,
        ge=1.0,
        description="Connection timeout in seconds"
    )
    send_receive_timeout: float = Field(
        default=300.0,
        ge=1.0,
        description="Send/receive timeout in seconds"
    )
    compression: bool = Field(
        default=True,
        description="Enable compression for data transfer"
    )


# ============================================================================
# Main Configuration Model
# ============================================================================

class Config(BaseModel):
    """
    Main configuration model for the cleaning corpus pipeline.
    
    This model validates the entire configuration structure and provides
    type-safe access to all configuration values.
    """

    model_config = ConfigDict(
        # Allow extra fields for forward compatibility
        extra="allow",
        # Validate assignment
        validate_assignment=True,
    )

    project: ProjectConfig = Field(
        default_factory=lambda: ProjectConfig(name="cleaning-corpus", version="0.2.0")
    )
    crawler: CrawlerConfig = Field(
        default_factory=lambda: CrawlerConfig(seeds_file="data/seeds.txt")
    )
    quality: QualityConfig = Field(default_factory=QualityConfig)
    enrichment: EnrichmentConfig = Field(default_factory=EnrichmentConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    clickhouse: ClickHouseConfig = Field(default_factory=ClickHouseConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    allowed_domains: List[str] = Field(
        default_factory=list,
        description="List of allowed domains for crawling"
    )


# ============================================================================
# Configuration Loading
# ============================================================================

def load_config(config_path: Optional[pathlib.Path] = None) -> Config:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file. If None, uses default location.
        
    Returns:
        Validated Config object.
        
    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValidationError: If config doesn't match schema.
    """
    import yaml

    if config_path is None:
        # Default to configs/default.yaml relative to project root
        # Assuming this file is in src/, go up 2 levels to project root
        project_root = pathlib.Path(__file__).resolve().parents[1]
        config_path = project_root / "configs" / "default.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load YAML
    with config_path.open() as f:
        config_dict = yaml.safe_load(f)

    if config_dict is None:
        config_dict = {}

    # Validate with Pydantic
    try:
        config = Config.model_validate(config_dict)
        return config
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}") from e


def get_config(config_path: Optional[pathlib.Path] = None) -> Config:
    """
    Get configuration instance (singleton pattern).
    
    This function caches the config to avoid reloading on every call.
    
    Args:
        config_path: Path to YAML config file. If None, uses default location.
        
    Returns:
        Validated Config object.
    """
    if not hasattr(get_config, "_cached_config"):
        get_config._cached_config = load_config(config_path)
    return get_config._cached_config


def reload_config(config_path: Optional[pathlib.Path] = None) -> Config:
    """
    Force reload configuration (clears cache).
    
    Args:
        config_path: Path to YAML config file. If None, uses default location.
        
    Returns:
        Validated Config object.
    """
    get_config._cached_config = load_config(config_path)
    return get_config._cached_config

"""
Tests for configuration loading and validation.
"""

import pytest
import pathlib
import tempfile
import yaml
from pydantic import ValidationError

from src.config import (
    Config,
    ProjectConfig,
    CrawlerConfig,
    QualityConfig,
    TextQualityConfig,
    ImageQualityConfig,
    AlignmentConfig,
    ProcessingConfig,
    LoggingConfig,
    load_config,
    get_config,
    reload_config,
)


class TestProjectConfig:
    """Tests for ProjectConfig model."""
    
    def test_valid_project_config(self):
        """Test valid project configuration."""
        config = ProjectConfig(name="test-project", version="1.0.0")
        assert config.name == "test-project"
        assert config.version == "1.0.0"
    
    def test_project_config_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            ProjectConfig(name="test")  # Missing version


class TestCrawlerConfig:
    """Tests for CrawlerConfig model."""
    
    def test_valid_crawler_config(self):
        """Test valid crawler configuration."""
        config = CrawlerConfig(
            seeds_file="data/seeds.txt",
            download_images=True,
            max_images_per_page=20,
            respect_robots=True,
            delay_seconds=1.0
        )
        assert config.seeds_file == "data/seeds.txt"
        assert config.download_images is True
        assert config.max_images_per_page == 20
    
    def test_crawler_config_defaults(self):
        """Test crawler config defaults."""
        config = CrawlerConfig(seeds_file="data/seeds.txt")
        assert config.download_images is True
        assert config.max_images_per_page == 20
        assert config.respect_robots is True
        assert config.delay_seconds == 1.0
    
    def test_crawler_config_validation(self):
        """Test crawler config validation."""
        with pytest.raises(ValidationError):
            CrawlerConfig(seeds_file="data/seeds.txt", max_images_per_page=-1)  # Negative value
        
        with pytest.raises(ValidationError):
            CrawlerConfig(seeds_file="data/seeds.txt", delay_seconds=-1.0)  # Negative delay


class TestTextQualityConfig:
    """Tests for TextQualityConfig model."""
    
    def test_valid_text_quality_config(self):
        """Test valid text quality configuration."""
        config = TextQualityConfig(
            min_words=500,
            max_words=50000,
            min_avg_word_length=3.0,
            language="en"
        )
        assert config.min_words == 500
        assert config.max_words == 50000
    
    def test_text_quality_config_validation(self):
        """Test text quality config validation."""
        # max_words must be >= min_words
        with pytest.raises(ValidationError):
            TextQualityConfig(min_words=1000, max_words=500)  # max < min


class TestImageQualityConfig:
    """Tests for ImageQualityConfig model."""
    
    def test_valid_image_quality_config(self):
        """Test valid image quality configuration."""
        config = ImageQualityConfig(
            min_resolution=[224, 224],
            max_aspect_ratio=3.0,
            allowed_formats=["jpg", "png"]
        )
        assert config.min_resolution == [224, 224]
        assert config.max_aspect_ratio == 3.0
    
    def test_image_quality_config_validation(self):
        """Test image quality config validation."""
        # Resolution must be [width, height]
        with pytest.raises(ValidationError):
            ImageQualityConfig(min_resolution=[224])  # Wrong length
        
        with pytest.raises(ValidationError):
            ImageQualityConfig(min_resolution=[0, 224])  # Non-positive value


class TestAlignmentConfig:
    """Tests for AlignmentConfig model."""
    
    def test_valid_alignment_config(self):
        """Test valid alignment configuration."""
        config = AlignmentConfig(min_clip_score=0.2)
        assert config.min_clip_score == 0.2
    
    def test_alignment_config_validation(self):
        """Test alignment config validation."""
        # Score must be between 0 and 1
        with pytest.raises(ValidationError):
            AlignmentConfig(min_clip_score=1.5)  # > 1.0
        
        with pytest.raises(ValidationError):
            AlignmentConfig(min_clip_score=-0.1)  # < 0.0


class TestLoggingConfig:
    """Tests for LoggingConfig model."""
    
    def test_valid_logging_config(self):
        """Test valid logging configuration."""
        config = LoggingConfig(level="INFO")
        assert config.level == "INFO"
    
    def test_logging_config_validation(self):
        """Test logging config validation."""
        # Level must be valid literal
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID")  # Not a valid level


class TestConfigLoading:
    """Tests for config loading functions."""
    
    def test_load_config_from_file(self):
        """Test loading config from a valid YAML file."""
        # Create a temporary valid config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "project": {"name": "test", "version": "1.0.0"},
                "crawler": {"seeds_file": "data/seeds.txt"},
                "quality": {
                    "text": {"min_words": 500},
                    "image": {"min_resolution": [224, 224]},
                    "alignment": {"min_clip_score": 0.2}
                },
                "processing": {"batch_size": 100},
                "logging": {"level": "INFO"},
                "allowed_domains": ["example.com"]
            }
            yaml.dump(config_data, f)
            temp_path = pathlib.Path(f.name)
        
        try:
            config = load_config(temp_path)
            assert config.project.name == "test"
            assert config.quality.text.min_words == 500
            assert "example.com" in config.allowed_domains
        finally:
            temp_path.unlink()
    
    def test_load_config_invalid_file(self):
        """Test loading config from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_config(pathlib.Path("/nonexistent/config.yaml"))
    
    def test_load_config_invalid_yaml(self):
        """Test loading config with invalid YAML structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Invalid YAML structure
            f.write("invalid: yaml: content: [")
            temp_path = pathlib.Path(f.name)
        
        try:
            with pytest.raises((ValueError, yaml.YAMLError)):
                load_config(temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_load_config_validation_error(self):
        """Test loading config that fails validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "quality": {
                    "text": {
                        "min_words": 1000,
                        "max_words": 500  # Invalid: max < min
                    }
                }
            }
            yaml.dump(config_data, f)
            temp_path = pathlib.Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                load_config(temp_path)
        finally:
            temp_path.unlink()
    
    def test_get_config_singleton(self):
        """Test that get_config returns cached instance."""
        # Clear cache
        if hasattr(get_config, "_cached_config"):
            delattr(get_config, "_cached_config")
        
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same instance
        assert config1 is config2
    
    def test_reload_config(self):
        """Test that reload_config forces reload."""
        # Clear cache
        if hasattr(get_config, "_cached_config"):
            delattr(get_config, "_cached_config")
        
        config1 = get_config()
        config2 = reload_config()
        
        # Should be different instances (new load)
        assert config1 is not config2


class TestFullConfig:
    """Tests for full Config model."""
    
    def test_config_with_defaults(self):
        """Test config with all defaults."""
        config = Config()
        assert config.project.name == "cleaning-corpus"
        assert config.quality.text.min_words == 500
        assert config.crawler.download_images is True
    
    def test_config_with_partial_data(self):
        """Test config with partial data (should use defaults for rest)."""
        config = Config.model_validate({
            "project": {"name": "custom", "version": "2.0.0"},
            "quality": {"text": {"min_words": 1000}}
        })
        assert config.project.name == "custom"
        assert config.quality.text.min_words == 1000
        # Should use defaults for other fields
        assert config.crawler.download_images is True
        assert config.processing.batch_size == 100
    
    def test_config_allows_extra_fields(self):
        """Test that config allows extra fields for forward compatibility."""
        config = Config.model_validate({
            "project": {"name": "test", "version": "1.0.0"},
            "extra_field": "should be allowed"
        })
        # Should not raise error
        assert config.project.name == "test"

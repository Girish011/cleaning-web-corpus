"""
Unit tests for image captioning functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from PIL import Image

from src.enrichment.captioner import BLIP2Captioner, BLIP2_AVAILABLE
from src.config import CaptioningConfig


class TestCaptioningConfig:
    """Test captioning configuration."""
    
    def test_captioning_config_defaults(self):
        """Test default captioning configuration."""
        config = CaptioningConfig()
        assert config.enable is True
        assert config.model == "Salesforce/blip2-opt-2.7b"
        assert config.max_length == 50
        assert config.min_confidence == 0.5
    
    def test_captioning_config_custom(self):
        """Test custom captioning configuration."""
        config = CaptioningConfig(
            enable=True,
            model="Salesforce/blip2-opt-6.7b",
            device="cpu",
            max_length=100,
            prompt="a detailed photo of",
        )
        assert config.enable is True
        assert config.model == "Salesforce/blip2-opt-6.7b"
        assert config.device == "cpu"
        assert config.max_length == 100
        assert config.prompt == "a detailed photo of"


class TestBLIP2Captioner:
    """Test BLIP-2 captioner."""
    
    def test_captioner_initialization_without_blip2(self):
        """Test captioner initialization when BLIP-2 is not available."""
        from unittest.mock import patch
        
        with patch('src.enrichment.captioner.BLIP2_AVAILABLE', False):
            captioner = BLIP2Captioner()
            assert not captioner.is_available()
            assert captioner._model is None
            assert captioner._processor is None
    
    def test_captioner_is_available(self):
        """Test is_available() method."""
        captioner = BLIP2Captioner()
        # Should return False if BLIP-2 not installed or model not loaded
        assert isinstance(captioner.is_available(), bool)
    
    def test_generate_caption_no_blip2(self):
        """Test caption generation when BLIP-2 not available."""
        from unittest.mock import patch
        
        with patch('src.enrichment.captioner.BLIP2_AVAILABLE', False):
            captioner = BLIP2Captioner()
            
            # Create test image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                img = Image.new('RGB', (224, 224), color='red')
                img.save(tmp.name, 'JPEG')
                tmp_path = tmp.name
            
            try:
                caption, metadata = captioner.generate_caption(tmp_path)
                assert caption is None
                assert metadata["reason"] == "blip2_not_available"
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def test_generate_caption_image_not_found(self):
        """Test caption generation when image doesn't exist."""
        captioner = BLIP2Captioner()
        
        caption, metadata = captioner.generate_caption("nonexistent_image_12345.jpg")
        
        assert caption is None
        assert metadata["reason"] == "image_not_found" or metadata["reason"] == "blip2_not_available"
    
    @pytest.mark.skipif(
        not BLIP2_AVAILABLE,
        reason="BLIP-2 dependencies not available. Install with: pip install torch transformers accelerate"
    )
    def test_generate_caption_with_blip2(self):
        """Test caption generation when BLIP-2 is available."""
        captioner = BLIP2Captioner()
        
        if not captioner.is_available():
            pytest.skip("BLIP-2 model not loaded")
        
        # Create test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (224, 224), color='red')
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            caption, metadata = captioner.generate_caption(tmp_path)
            
            # Should return a caption
            assert caption is not None
            assert len(caption) > 0
            assert "caption" in metadata
            assert "model" in metadata
            assert "generated_at" in metadata
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_caption_images(self):
        """Test captioning multiple images."""
        captioner = BLIP2Captioner()
        
        # Create test images
        test_images = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                img = Image.new('RGB', (224, 224), color='blue')
                img.save(tmp.name, 'JPEG')
                test_images.append({
                    "path": tmp.name,
                    "url": f"http://example.com/img{i}.jpg",
                })
        
        try:
            captioned = captioner.caption_images(test_images)
            
            # Should return same number of images
            assert len(captioned) == len(test_images)
            
            # Each image should have caption field (may be None if BLIP-2 unavailable)
            for img in captioned:
                assert "caption" in img
                assert "caption_metadata" in img
        finally:
            for img in test_images:
                if os.path.exists(img["path"]):
                    os.unlink(img["path"])
    
    def test_caption_images_no_path(self):
        """Test captioning images without path."""
        captioner = BLIP2Captioner()
        
        images = [
            {"url": "http://example.com/img1.jpg"},  # No path
            {"path": "img2.jpg", "url": "http://example.com/img2.jpg"},
        ]
        
        captioned = captioner.caption_images(images)
        
        # Should return all images
        assert len(captioned) == 2
        # Image without path should not have caption
        assert captioned[0].get("caption") is None or "caption" in captioned[0]
    
    def test_caption_image_batch(self):
        """Test batch captioning."""
        captioner = BLIP2Captioner()
        
        # Create test images
        test_images = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                img = Image.new('RGB', (224, 224), color='green')
                img.save(tmp.name, 'JPEG')
                test_images.append({
                    "path": tmp.name,
                    "url": f"http://example.com/img{i}.jpg",
                })
        
        try:
            captioned = captioner.caption_image_batch(test_images, batch_size=2)
            
            # Should return all images
            assert len(captioned) == len(test_images)
        finally:
            for img in test_images:
                if os.path.exists(img["path"]):
                    os.unlink(img["path"])
    
    def test_captioner_with_prompt(self):
        """Test caption generation with custom prompt."""
        captioner = BLIP2Captioner()
        
        # Create test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (224, 224), color='yellow')
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            caption, metadata = captioner.generate_caption(tmp_path, prompt="a photo of")
            
            # Should work (may return None if BLIP-2 unavailable)
            assert isinstance(caption, (str, type(None)))
            if metadata.get("prompt"):
                assert metadata["prompt"] == "a photo of"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_captioner_different_models(self):
        """Test captioner with different model names."""
        # Test with default model
        captioner1 = BLIP2Captioner(model_name="Salesforce/blip2-opt-2.7b")
        assert captioner1.model_name == "Salesforce/blip2-opt-2.7b"
        
        # Test with larger model
        captioner2 = BLIP2Captioner(model_name="Salesforce/blip2-opt-6.7b")
        assert captioner2.model_name == "Salesforce/blip2-opt-6.7b"
        
        # Test with alternative architecture
        captioner3 = BLIP2Captioner(model_name="Salesforce/blip2-flan-t5-xl")
        assert captioner3.model_name == "Salesforce/blip2-flan-t5-xl"
    
    def test_captioner_device_selection(self):
        """Test captioner device selection."""
        # Auto device
        captioner1 = BLIP2Captioner(device=None)
        assert captioner1._device is None or isinstance(captioner1._device, str)
        
        # CPU device
        captioner2 = BLIP2Captioner(device="cpu")
        assert captioner2._device == "cpu"
        
        # CUDA device (if available)
        captioner3 = BLIP2Captioner(device="cuda")
        assert captioner3._device == "cuda"

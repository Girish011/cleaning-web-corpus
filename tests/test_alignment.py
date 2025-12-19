"""
Unit tests for CLIP text-image alignment scoring.
"""

import pytest
import pathlib
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile
import os

from src.config import AlignmentConfig
from src.quality.alignment import CLIPAlignmentScorer, CLIP_AVAILABLE


class TestAlignmentConfig:
    """Test alignment configuration."""
    
    def test_default_config(self):
        """Test default alignment configuration."""
        config = AlignmentConfig()
        assert config.min_clip_score == 0.2
        assert 0.0 <= config.min_clip_score <= 1.0
    
    def test_custom_config(self):
        """Test custom alignment configuration."""
        config = AlignmentConfig(min_clip_score=0.5)
        assert config.min_clip_score == 0.5
    
    def test_config_validation(self):
        """Test that invalid config values are rejected."""
        # Score > 1.0 should fail
        with pytest.raises(Exception):
            AlignmentConfig(min_clip_score=1.5)
        
        # Score < 0.0 should fail
        with pytest.raises(Exception):
            AlignmentConfig(min_clip_score=-0.1)


class TestCLIPAlignmentScorer:
    """Test CLIP alignment scorer."""
    
    def test_scorer_initialization_without_clip(self):
        """Test scorer initialization when CLIP is not available."""
        # Mock CLIP_AVAILABLE to False
        with patch('src.quality.alignment.CLIP_AVAILABLE', False):
            config = AlignmentConfig(min_clip_score=0.2)
            scorer = CLIPAlignmentScorer(config)
            
            assert not scorer.is_available()
            assert scorer._model is None
            assert scorer._processor is None
    
    def test_is_available_without_clip(self):
        """Test is_available() returns False when CLIP not available."""
        with patch('src.quality.alignment.CLIP_AVAILABLE', False):
            config = AlignmentConfig()
            scorer = CLIPAlignmentScorer(config)
            assert not scorer.is_available()
    
    @pytest.mark.skipif(not CLIP_AVAILABLE, reason="CLIP dependencies not available")
    def test_scorer_initialization_with_clip(self):
        """Test scorer initialization when CLIP is available."""
        config = AlignmentConfig(min_clip_score=0.2)
        scorer = CLIPAlignmentScorer(config)
        
        # Should be available if CLIP is installed
        # Note: This test may fail if CLIP model download fails
        if scorer.is_available():
            assert scorer._model is not None
            assert scorer._processor is not None
    
    def test_score_text_image_no_clip(self):
        """Test scoring when CLIP is not available (graceful fallback)."""
        with patch('src.quality.alignment.CLIP_AVAILABLE', False):
            config = AlignmentConfig(min_clip_score=0.2)
            scorer = CLIPAlignmentScorer(config)
            
            score, stats = scorer.score_text_image("test text", "nonexistent.jpg")
            
            assert score is None
            assert stats["reason"] == "clip_not_available"
            assert stats["passed"] is True  # Graceful fallback
    
    def test_score_text_image_image_not_found(self):
        """Test scoring when image file doesn't exist."""
        config = AlignmentConfig(min_clip_score=0.2)
        scorer = CLIPAlignmentScorer(config)
        
        # Use a non-existent image path
        score, stats = scorer.score_text_image("test text", "nonexistent_image_12345.jpg")
        
        # Should return None with graceful fallback
        if not scorer.is_available():
            assert score is None
            assert stats["passed"] is True
        else:
            # If CLIP is available, should return None due to missing image
            assert score is None or stats["reason"] == "image_not_found"
    
    def test_score_text_images_no_clip(self):
        """Test scoring multiple images when CLIP not available."""
        with patch('src.quality.alignment.CLIP_AVAILABLE', False):
            config = AlignmentConfig(min_clip_score=0.2)
            scorer = CLIPAlignmentScorer(config)
            
            images = [
                {"path": "img1.jpg", "url": "http://example.com/img1.jpg"},
                {"path": "img2.jpg", "url": "http://example.com/img2.jpg"},
            ]
            
            aligned, misaligned = scorer.score_text_images("test text", images)
            
            # Should pass all images when CLIP unavailable (graceful fallback)
            assert len(aligned) == 2
            assert len(misaligned) == 0
    
    def test_score_text_images_no_path(self):
        """Test scoring images without path (should pass leniently)."""
        config = AlignmentConfig(min_clip_score=0.2)
        scorer = CLIPAlignmentScorer(config)
        
        images = [
            {"url": "http://example.com/img1.jpg"},  # No path
            {"path": "img2.jpg", "url": "http://example.com/img2.jpg"},
        ]
        
        aligned, misaligned = scorer.score_text_images("test text", images)
        
        # Image without path should be kept (lenient)
        assert len(aligned) >= 1  # At least the one without path
    
    def test_filter_by_alignment(self):
        """Test filter_by_alignment method."""
        config = AlignmentConfig(min_clip_score=0.2)
        scorer = CLIPAlignmentScorer(config)
        
        images = [
            {"path": "img1.jpg", "url": "http://example.com/img1.jpg"},
        ]
        
        aligned, misaligned = scorer.filter_by_alignment("test text", images)
        
        # Should return tuple of (aligned, misaligned)
        assert isinstance(aligned, list)
        assert isinstance(misaligned, list)
    
    @pytest.mark.skipif(not CLIP_AVAILABLE, reason="CLIP dependencies not available")
    def test_score_text_image_with_real_image(self):
        """Test scoring with a real image file (requires CLIP)."""
        config = AlignmentConfig(min_clip_score=0.2)
        scorer = CLIPAlignmentScorer(config)
        
        if not scorer.is_available():
            pytest.skip("CLIP model not loaded")
        
        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create a simple test image
            img = Image.new('RGB', (224, 224), color='red')
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            text = "a red image"
            score, stats = scorer.score_text_image(text, tmp_path)
            
            # Should return a valid score
            assert score is not None
            assert 0.0 <= score <= 1.0
            assert "score" in stats
            assert "passed" in stats
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @pytest.mark.skipif(not CLIP_AVAILABLE, reason="CLIP dependencies not available")
    def test_score_threshold_filtering(self):
        """Test that images are filtered by score threshold."""
        config = AlignmentConfig(min_clip_score=0.8)  # High threshold
        scorer = CLIPAlignmentScorer(config)
        
        if not scorer.is_available():
            pytest.skip("CLIP model not loaded")
        
        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (224, 224), color='blue')
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Text that might not align well with a blue image
            text = "a red apple on a wooden table"
            score, stats = scorer.score_text_image(text, tmp_path)
            
            if score is not None:
                # Check that threshold is applied correctly
                assert stats["min_clip_score"] == 0.8
                assert stats["passed"] == (score >= 0.8)
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestCLIPIntegration:
    """Integration tests for CLIP alignment in the pipeline."""
    
    def test_scorer_handles_missing_dependencies_gracefully(self):
        """Test that scorer handles missing CLIP dependencies gracefully."""
        # This test ensures the module can be imported even without CLIP
        from src.quality.alignment import CLIPAlignmentScorer, CLIP_AVAILABLE
        
        config = AlignmentConfig(min_clip_score=0.2)
        scorer = CLIPAlignmentScorer(config)
        
        # Should not raise exception even if CLIP unavailable
        assert isinstance(scorer, CLIPAlignmentScorer)
        
        # Should handle scoring gracefully
        score, stats = scorer.score_text_image("test", "nonexistent.jpg")
        assert score is None or isinstance(score, float)

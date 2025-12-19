"""
Unit tests for image quality filters.
"""

import pytest
from src.config import ImageQualityConfig
from src.quality.image_filters import ImageQualityFilter


class TestResolutionFilter:
    """Test resolution filtering."""
    
    def test_resolution_too_small(self):
        """Test that images smaller than minimum resolution are rejected."""
        config = ImageQualityConfig(min_resolution=[224, 224])
        filter_instance = ImageQualityFilter(config)
        
        # Image too small
        image_data = {"width": 100, "height": 100, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert not result["passed"]
        assert "resolution" in result["reason"].lower()
    
    def test_resolution_valid(self):
        """Test that images meeting minimum resolution pass."""
        config = ImageQualityConfig(min_resolution=[224, 224])
        filter_instance = ImageQualityFilter(config)
        
        # Valid image
        image_data = {"width": 800, "height": 600, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]
    
    def test_resolution_boundary(self):
        """Test resolution at minimum boundary."""
        config = ImageQualityConfig(min_resolution=[224, 224])
        filter_instance = ImageQualityFilter(config)
        
        # Exactly at minimum
        image_data = {"width": 224, "height": 224, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]
    
    def test_resolution_unknown_dimensions(self):
        """Test that images with unknown dimensions pass (lenient)."""
        config = ImageQualityConfig(min_resolution=[224, 224])
        filter_instance = ImageQualityFilter(config)
        
        # Unknown dimensions
        image_data = {"width": None, "height": None, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]  # Should pass when dimensions unknown
        assert "dimensions_unknown" in result["stats"].get("reason", "")


class TestAspectRatioFilter:
    """Test aspect ratio filtering."""
    
    def test_aspect_ratio_too_extreme(self):
        """Test that images with extreme aspect ratios are rejected."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],  # Lower threshold so resolution passes
            max_aspect_ratio=3.0
        )
        filter_instance = ImageQualityFilter(config)
        
        # Very wide image (aspect ratio > 3.0, but passes resolution)
        image_data = {"width": 1000, "height": 200, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert not result["passed"]
        assert "aspect_ratio" in result["reason"].lower()
    
    def test_aspect_ratio_valid(self):
        """Test that images with normal aspect ratios pass."""
        config = ImageQualityConfig(max_aspect_ratio=3.0)
        filter_instance = ImageQualityFilter(config)
        
        # Normal aspect ratio
        image_data = {"width": 800, "height": 600, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]
    
    def test_aspect_ratio_portrait(self):
        """Test that tall (portrait) images are handled correctly."""
        config = ImageQualityConfig(max_aspect_ratio=3.0)
        filter_instance = ImageQualityFilter(config)
        
        # Tall image (portrait orientation)
        image_data = {"width": 200, "height": 1000, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        # Should fail (aspect ratio 5.0 > 3.0)
        assert not result["passed"]
    
    def test_aspect_ratio_boundary(self):
        """Test aspect ratio at maximum boundary."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],  # Lower threshold so resolution passes
            max_aspect_ratio=3.0
        )
        filter_instance = ImageQualityFilter(config)
        
        # Exactly at maximum (3.0)
        image_data = {"width": 600, "height": 200, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]
    
    def test_aspect_ratio_unknown_dimensions(self):
        """Test that images with unknown dimensions pass (lenient)."""
        config = ImageQualityConfig(max_aspect_ratio=3.0)
        filter_instance = ImageQualityFilter(config)
        
        image_data = {"width": None, "height": None, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]


class TestFormatFilter:
    """Test format filtering."""
    
    def test_format_not_allowed(self):
        """Test that disallowed formats are rejected."""
        config = ImageQualityConfig(allowed_formats=["jpg", "jpeg", "png", "webp"])
        filter_instance = ImageQualityFilter(config)
        
        # GIF format (not in allowed list)
        image_data = {"url": "http://example.com/img.gif", "path": "images/img.gif"}
        result = filter_instance.filter_image(image_data)
        assert not result["passed"]
        assert "format" in result["reason"].lower()
    
    def test_format_allowed(self):
        """Test that allowed formats pass."""
        config = ImageQualityConfig(allowed_formats=["jpg", "jpeg", "png", "webp"])
        filter_instance = ImageQualityFilter(config)
        
        # JPG format
        image_data = {"url": "http://example.com/img.jpg", "path": "images/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]
    
    def test_format_jpg_jpeg_normalization(self):
        """Test that jpg and jpeg are treated as the same."""
        config = ImageQualityConfig(allowed_formats=["jpg", "jpeg", "png", "webp"])
        filter_instance = ImageQualityFilter(config)
        
        # JPG (should normalize to jpeg)
        image_data = {"url": "http://example.com/img.jpg"}
        result1 = filter_instance.filter_image(image_data)
        assert result1["passed"]
        
        # JPEG
        image_data = {"url": "http://example.com/img.jpeg"}
        result2 = filter_instance.filter_image(image_data)
        assert result2["passed"]
    
    def test_format_from_path(self):
        """Test format detection from file path."""
        config = ImageQualityConfig(allowed_formats=["jpg", "jpeg", "png", "webp"])
        filter_instance = ImageQualityFilter(config)
        
        image_data = {"path": "images/example.png", "url": "http://example.com/img"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]
        assert result["stats"]["format"] == "png"
    
    def test_format_unknown(self):
        """Test that images with unknown format pass (lenient)."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],  # Set low threshold
            allowed_formats=["jpg", "jpeg", "png", "webp"]
        )
        filter_instance = ImageQualityFilter(config)
        
        # Image with unknown format but valid dimensions
        image_data = {
            "width": 500,
            "height": 500,
            "url": "http://example.com/img"  # No extension
        }
        result = filter_instance.filter_image(image_data)
        assert result["passed"]  # Should pass when format unknown (lenient)
        # Check that format check passed
        assert result["stats"].get("format_passed") is True


class TestCombinedFilters:
    """Test combined filter behavior."""
    
    def test_all_filters_pass(self):
        """Test that image passing all filters returns passed=True."""
        config = ImageQualityConfig(
            min_resolution=[224, 224],
            max_aspect_ratio=3.0,
            allowed_formats=["jpg", "jpeg", "png", "webp"]
        )
        filter_instance = ImageQualityFilter(config)
        
        good_image = {
            "width": 800,
            "height": 600,
            "url": "http://example.com/img.jpg",
            "path": "images/img.jpg"
        }
        
        result = filter_instance.filter_image(good_image)
        assert result["passed"]
        assert result["reason"] == "passed"
    
    def test_multiple_failures(self):
        """Test that first failing filter stops processing."""
        config = ImageQualityConfig(
            min_resolution=[224, 224],
            max_aspect_ratio=3.0,
            allowed_formats=["jpg", "jpeg", "png", "webp"]
        )
        filter_instance = ImageQualityFilter(config)
        
        # Image that fails resolution check
        bad_image = {
            "width": 100,
            "height": 100,
            "url": "http://example.com/img.jpg"
        }
        
        result = filter_instance.filter_image(bad_image)
        assert not result["passed"]
        assert "resolution" in result["reason"].lower()
        # Should not check aspect ratio or format after resolution fails


class TestFilterImagesList:
    """Test filtering multiple images."""
    
    def test_filter_images_list(self):
        """Test filtering a list of images."""
        config = ImageQualityConfig(
            min_resolution=[224, 224],
            max_aspect_ratio=3.0
        )
        filter_instance = ImageQualityFilter(config)
        
        images = [
            {"width": 800, "height": 600, "url": "http://example.com/img1.jpg"},  # Pass
            {"width": 100, "height": 100, "url": "http://example.com/img2.jpg"},  # Fail: too small
            {"width": 5000, "height": 500, "url": "http://example.com/img3.jpg"},  # Fail: aspect ratio
            {"width": 500, "height": 500, "url": "http://example.com/img4.jpg"},  # Pass
        ]
        
        passed, failed = filter_instance.filter_images(images)
        
        assert len(passed) == 2
        assert len(failed) == 2
        
        # Check that failed images have filter_reason
        assert "filter_reason" in failed[0]
        assert "filter_reason" in failed[1]
        
        # Check reasons
        assert "resolution" in failed[0]["filter_reason"].lower()
        assert "aspect_ratio" in failed[1]["filter_reason"].lower()


class TestEdgeCases:
    """Test edge cases."""
    
    def test_zero_height(self):
        """Test handling of zero height."""
        config = ImageQualityConfig(max_aspect_ratio=3.0)
        filter_instance = ImageQualityFilter(config)
        
        image_data = {"width": 100, "height": 0, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        # Should handle gracefully (pass when dimensions invalid)
        assert result["passed"] or "aspect_ratio" not in result.get("reason", "").lower()
    
    def test_very_large_image(self):
        """Test handling of very large images."""
        config = ImageQualityConfig(
            min_resolution=[224, 224],
            max_aspect_ratio=3.0
        )
        filter_instance = ImageQualityFilter(config)
        
        image_data = {"width": 10000, "height": 8000, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        # Should pass (meets all criteria)
        assert result["passed"]
    
    def test_square_image(self):
        """Test square images (aspect ratio 1.0)."""
        config = ImageQualityConfig(max_aspect_ratio=3.0)
        filter_instance = ImageQualityFilter(config)
        
        image_data = {"width": 500, "height": 500, "url": "http://example.com/img.jpg"}
        result = filter_instance.filter_image(image_data)
        assert result["passed"]
        assert result["stats"]["aspect_ratio"] == 1.0


class TestDuplicateDetection:
    """Test duplicate image detection."""
    
    def test_duplicate_detection_disabled(self):
        """Test that duplicate detection is skipped when disabled."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],
            enable_duplicate_detection=False
        )
        filter_instance = ImageQualityFilter(config)
        
        images = [
            {"width": 500, "height": 500, "path": "test1.jpg", "url": "http://example.com/img1.jpg"},
            {"width": 500, "height": 500, "path": "test2.jpg", "url": "http://example.com/img2.jpg"},
        ]
        
        passed, failed = filter_instance.filter_images(images)
        # Should pass all (duplicate detection disabled)
        assert len(passed) == 2
        assert len(failed) == 0
    
    def test_duplicate_detection_too_few_images(self):
        """Test that duplicate detection is skipped with too few images."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],
            enable_duplicate_detection=True,
            min_images_for_duplicate_check=3
        )
        filter_instance = ImageQualityFilter(config)
        
        images = [
            {"width": 500, "height": 500, "path": "test1.jpg", "url": "http://example.com/img1.jpg"},
            {"width": 500, "height": 500, "path": "test2.jpg", "url": "http://example.com/img2.jpg"},
        ]
        
        passed, failed = filter_instance.filter_images(images)
        # Should pass all (not enough images for duplicate check)
        assert len(passed) == 2
    
    def test_duplicate_detection_no_path(self):
        """Test that images without paths are kept (can't compute hash)."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],
            enable_duplicate_detection=True
        )
        filter_instance = ImageQualityFilter(config)
        
        images = [
            {"width": 500, "height": 500, "url": "http://example.com/img1.jpg"},  # No path
            {"width": 500, "height": 500, "url": "http://example.com/img2.jpg"},  # No path
        ]
        
        passed, failed = filter_instance.filter_images(images)
        # Should keep all (no paths to compute hash)
        assert len(passed) == 2
    
    def test_duplicate_detection_hash_computation_error(self):
        """Test graceful handling when hash computation fails."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],
            enable_duplicate_detection=True
        )
        filter_instance = ImageQualityFilter(config)
        
        # Images with non-existent paths
        images = [
            {"width": 500, "height": 500, "path": "/nonexistent/image1.jpg", "url": "http://example.com/img1.jpg"},
            {"width": 500, "height": 500, "path": "/nonexistent/image2.jpg", "url": "http://example.com/img2.jpg"},
        ]
        
        passed, failed = filter_instance.filter_images(images)
        # Should keep all (hash computation failed, be lenient)
        assert len(passed) == 2
    
    def test_duplicate_detection_integration(self):
        """Test duplicate detection integration with quality filters."""
        config = ImageQualityConfig(
            min_resolution=[100, 100],
            enable_duplicate_detection=True,
            duplicate_similarity_threshold=5
        )
        filter_instance = ImageQualityFilter(config)
        
        # Mix of quality-passed and quality-failed images
        images = [
            {"width": 500, "height": 500, "path": "test1.jpg", "url": "http://example.com/img1.jpg"},  # Pass
            {"width": 50, "height": 50, "path": "test2.jpg", "url": "http://example.com/img2.jpg"},  # Fail: too small
            {"width": 500, "height": 500, "path": "test3.jpg", "url": "http://example.com/img3.jpg"},  # Pass
        ]
        
        passed, failed = filter_instance.filter_images(images)
        # One should fail quality check
        assert len(failed) >= 1
        # Remaining should go through duplicate detection
        assert len(passed) >= 1

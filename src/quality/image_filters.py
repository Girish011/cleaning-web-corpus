"""
Image quality filtering module.

This module provides image quality filters to ensure downloaded images
meet minimum quality standards before being included in the corpus.
"""

import logging
import pathlib
from typing import Dict, List, Optional, Tuple, Set

from PIL import Image
from src.config import ImageQualityConfig

logger = logging.getLogger(__name__)

# Try to import imagehash, handle gracefully if not available
try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    logger.warning("imagehash not available, duplicate detection will be skipped. Install with: pip install imagehash")


class ImageQualityFilter:
    """
    Image quality filter that applies multiple quality checks.
    
    Filters include:
    - Resolution check (minimum width/height)
    - Aspect ratio check (remove weird/odd aspect ratios)
    - Format validation
    - Duplicate detection (exact and near-duplicates using perceptual hashing)
    """
    
    def __init__(self, config: ImageQualityConfig):
        """
        Initialize the image quality filter.
        
        Args:
            config: ImageQualityConfig instance with filter parameters
        """
        self.config = config
        self._init_hash_algorithm()
    
    def _init_hash_algorithm(self):
        """Initialize the hash algorithm function based on config."""
        if not IMAGEHASH_AVAILABLE:
            self._hash_func = None
            return
        
        algorithm = self.config.duplicate_hash_algorithm
        
        if algorithm == "phash":
            self._hash_func = imagehash.phash
        elif algorithm == "dhash":
            self._hash_func = imagehash.dhash
        elif algorithm == "whash":
            self._hash_func = imagehash.whash
        elif algorithm == "average_hash":
            self._hash_func = imagehash.average_hash
        else:
            logger.warning(f"Unknown hash algorithm: {algorithm}, using phash")
            self._hash_func = imagehash.phash
    
    def check_resolution(self, width: Optional[int], height: Optional[int]) -> Tuple[bool, Dict]:
        """
        Check if image meets minimum resolution requirements.
        
        Args:
            width: Image width in pixels (None if unknown)
            height: Image height in pixels (None if unknown)
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        min_width, min_height = self.config.min_resolution
        
        # If dimensions are unknown, we can't validate - be lenient and pass
        if width is None or height is None:
            return True, {
                "resolution_passed": True,
                "width": width,
                "height": height,
                "min_width": min_width,
                "min_height": min_height,
                "reason": "dimensions_unknown"
            }
        
        passed = width >= min_width and height >= min_height
        
        stats = {
            "resolution_passed": passed,
            "width": width,
            "height": height,
            "min_width": min_width,
            "min_height": min_height,
        }
        
        return passed, stats
    
    def check_aspect_ratio(self, width: Optional[int], height: Optional[int]) -> Tuple[bool, Dict]:
        """
        Check if image has acceptable aspect ratio.
        
        Removes images with weird aspect ratios (too wide, too tall, etc.)
        
        Args:
            width: Image width in pixels (None if unknown)
            height: Image height in pixels (None if unknown)
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        # If dimensions are unknown, we can't validate - be lenient and pass
        if width is None or height is None or height == 0:
            return True, {
                "aspect_ratio_passed": True,
                "aspect_ratio": None,
                "max_aspect_ratio": self.config.max_aspect_ratio,
                "reason": "dimensions_unknown"
            }
        
        # Calculate aspect ratio (width/height)
        # Handle both landscape and portrait orientations
        aspect_ratio = max(width, height) / min(width, height)
        
        passed = aspect_ratio <= self.config.max_aspect_ratio
        
        stats = {
            "aspect_ratio_passed": passed,
            "aspect_ratio": round(aspect_ratio, 2),
            "max_aspect_ratio": self.config.max_aspect_ratio,
            "width": width,
            "height": height,
        }
        
        return passed, stats
    
    def check_format(self, image_path: Optional[str], image_url: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Check if image format is in allowed list.
        
        Args:
            image_path: Path to image file (optional)
            image_url: Original image URL (optional, used as fallback)
            
        Returns:
            Tuple of (passed: bool, stats: dict)
        """
        # Determine format from path or URL
        format_str = None
        
        if image_path:
            # Extract extension from path
            # Handle both "path/to/file.jpg" and "file.jpg" formats
            parts = image_path.lower().rsplit('.', 1)  # Split from right, max 1 split
            if len(parts) == 2:
                format_str = parts[1]
        elif image_url:
            # Extract extension from URL
            # Remove query params first
            url_without_params = image_url.lower().split('?')[0]
            # Split from right to get extension
            parts = url_without_params.rsplit('.', 1)
            if len(parts) == 2:
                potential_format = parts[1]
                # Only accept if it looks like a file extension (short, alphanumeric)
                if len(potential_format) <= 5 and potential_format.isalnum():
                    format_str = potential_format
        
        if format_str is None:
            # Format unknown - be lenient and pass
            return True, {
                "format_passed": True,
                "format": None,
                "allowed_formats": self.config.allowed_formats,
                "reason": "format_unknown"
            }
        
        # Normalize format (jpg/jpeg are the same)
        normalized_format = format_str
        if format_str == "jpg":
            normalized_format = "jpeg"
        
        passed = normalized_format in self.config.allowed_formats
        
        stats = {
            "format_passed": passed,
            "format": format_str,
            "allowed_formats": self.config.allowed_formats,
        }
        
        return passed, stats
    
    def filter_image(self, image_data: Dict) -> Dict:
        """
        Apply all image quality filters to a single image.
        
        Args:
            image_data: Dictionary with image metadata. Expected keys:
                - width: int or None
                - height: int or None
                - path: str or None (file path)
                - url: str or None (original URL)
                - format: str or None (optional, will be inferred)
                
        Returns:
            Dictionary with keys:
            - passed: bool - Whether all filters passed
            - reason: str - Failure reason or "passed"
            - stats: dict - All filter statistics
        """
        width = image_data.get("width")
        height = image_data.get("height")
        path = image_data.get("path")
        url = image_data.get("url")
        
        all_stats = {}
        
        # Check resolution
        resolution_passed, resolution_stats = self.check_resolution(width, height)
        all_stats.update(resolution_stats)
        if not resolution_passed:
            return {
                "passed": False,
                "reason": f"resolution_too_small: {width}x{height} (min: {self.config.min_resolution[0]}x{self.config.min_resolution[1]})",
                "stats": all_stats
            }
        
        # Check aspect ratio
        aspect_ratio_passed, aspect_stats = self.check_aspect_ratio(width, height)
        all_stats.update(aspect_stats)
        if not aspect_ratio_passed:
            aspect_ratio = aspect_stats.get("aspect_ratio", 0.0)
            return {
                "passed": False,
                "reason": f"aspect_ratio_too_extreme: {aspect_ratio:.2f} (max: {self.config.max_aspect_ratio:.2f})",
                "stats": all_stats
            }
        
        # Check format
        format_passed, format_stats = self.check_format(path, url)
        all_stats.update(format_stats)
        if not format_passed:
            format_str = format_stats.get("format", "unknown")
            return {
                "passed": False,
                "reason": f"format_not_allowed: {format_str} (allowed: {self.config.allowed_formats})",
                "stats": all_stats
            }
        
        # All checks passed
        return {
            "passed": True,
            "reason": "passed",
            "stats": all_stats
        }
    
    def filter_images(self, images: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a list of images, returning passed and failed images.
        
        Args:
            images: List of image metadata dictionaries
            
        Returns:
            Tuple of (passed_images: List[Dict], failed_images: List[Dict])
            Each failed image includes a 'filter_reason' field explaining why it failed
        """
        passed_images = []
        failed_images = []
        
        for image in images:
            filter_result = self.filter_image(image)
            
            if filter_result["passed"]:
                passed_images.append(image)
            else:
                # Add filter reason to failed image
                failed_image = image.copy()
                failed_image["filter_reason"] = filter_result["reason"]
                failed_image["filter_stats"] = filter_result["stats"]
                failed_images.append(failed_image)
        
        return passed_images, failed_images
    
    def _compute_image_hash(self, image_path: str) -> Optional[str]:
        """
        Compute perceptual hash for an image file.
        
        Args:
            image_path: Path to image file (can be relative or absolute)
            
        Returns:
            Hash string (hex) or None if computation fails
        """
        if not IMAGEHASH_AVAILABLE or self._hash_func is None:
            return None
        
        try:
            # Handle relative paths (relative to project root)
            path = pathlib.Path(image_path)
            if not path.is_absolute():
                # Try relative to project root
                project_root = pathlib.Path(__file__).resolve().parents[2]
                path = project_root / path
            
            if not path.exists():
                logger.debug(f"Image file not found for hash computation: {path}")
                return None
            
            # Open and compute hash
            with Image.open(path) as img:
                # Convert to RGB if necessary (handles RGBA, P, etc.)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                hash_value = self._hash_func(img)
                return str(hash_value)
                
        except Exception as e:
            logger.debug(f"Error computing hash for {image_path}: {e}")
            return None
    
    def _detect_duplicates(self, images: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect duplicate and near-duplicate images using perceptual hashing.
        
        Args:
            images: List of image dictionaries with 'path' or 'url' keys
            
        Returns:
            Tuple of (unique_images: List[Dict], duplicate_images: List[Dict])
            Duplicate images include 'duplicate_of' field pointing to the first occurrence
        """
        if not self.config.enable_duplicate_detection:
            return images, []
        
        if not IMAGEHASH_AVAILABLE or self._hash_func is None:
            logger.debug("Duplicate detection skipped: imagehash not available")
            return images, []
        
        if len(images) < self.config.min_images_for_duplicate_check:
            return images, []
        
        unique_images = []
        duplicate_images = []
        seen_hashes: Dict[str, int] = {}  # hash -> index of first occurrence
        
        for idx, image in enumerate(images):
            image_path = image.get("path")
            
            if not image_path:
                # No path available, can't compute hash - keep it
                unique_images.append(image)
                continue
            
            # Compute hash
            image_hash = self._compute_image_hash(image_path)
            
            if image_hash is None:
                # Hash computation failed - keep image (lenient)
                unique_images.append(image)
                continue
            
            # Check for duplicates
            is_duplicate = False
            duplicate_of_idx = None
            hamming_distance = None
            
            for seen_hash, first_idx in seen_hashes.items():
                # Calculate Hamming distance
                try:
                    hash1 = imagehash.hex_to_hash(image_hash)
                    hash2 = imagehash.hex_to_hash(seen_hash)
                    hamming_distance = hash1 - hash2
                    
                    if hamming_distance <= self.config.duplicate_similarity_threshold:
                        # This is a duplicate
                        is_duplicate = True
                        duplicate_of_idx = first_idx
                        break
                except Exception as e:
                    logger.debug(f"Error comparing hashes: {e}")
                    continue
            
            if is_duplicate and duplicate_of_idx is not None:
                # Mark as duplicate
                duplicate_image = image.copy()
                duplicate_image["duplicate_of"] = unique_images[duplicate_of_idx].get("url") or unique_images[duplicate_of_idx].get("path")
                duplicate_image["hamming_distance"] = hamming_distance
                duplicate_image["filter_reason"] = f"duplicate_image: hamming_distance={hamming_distance} (threshold={self.config.duplicate_similarity_threshold})"
                duplicate_images.append(duplicate_image)
            else:
                # New unique image
                seen_hashes[image_hash] = len(unique_images)
                unique_images.append(image)
        
        return unique_images, duplicate_images
    
    def filter_images(self, images: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a list of images, returning passed and failed images.
        
        Applies quality filters first, then duplicate detection on passed images.
        
        Args:
            images: List of image metadata dictionaries
            
        Returns:
            Tuple of (passed_images: List[Dict], failed_images: List[Dict])
            Each failed image includes a 'filter_reason' field explaining why it failed
        """
        # First, apply quality filters (resolution, aspect ratio, format)
        quality_passed = []
        quality_failed = []
        
        for image in images:
            filter_result = self.filter_image(image)
            
            if filter_result["passed"]:
                quality_passed.append(image)
            else:
                # Add filter reason to failed image
                failed_image = image.copy()
                failed_image["filter_reason"] = filter_result["reason"]
                failed_image["filter_stats"] = filter_result["stats"]
                quality_failed.append(failed_image)
        
        # Then, detect duplicates among quality-passed images
        unique_images, duplicate_images = self._detect_duplicates(quality_passed)
        
        # Combine all failed images
        all_failed = quality_failed + duplicate_images
        
        return unique_images, all_failed

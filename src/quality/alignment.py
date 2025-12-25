"""
Text-image alignment scoring using CLIP.

This module provides CLIP-based text-image alignment scoring to measure
the semantic relevance between text content and images. This is a key
differentiator for multi-modal quality filtering.
"""

import logging
import pathlib
from typing import Dict, List, Optional, Tuple

from PIL import Image
from src.config import AlignmentConfig

logger = logging.getLogger(__name__)

# Try to import CLIP dependencies, handle gracefully if not available
try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logger.warning(
        "CLIP dependencies not available. Install with: pip install torch transformers"
    )


class CLIPAlignmentScorer:
    """
    CLIP-based text-image alignment scorer.
    
    Uses CLIP (Contrastive Language-Image Pre-training) to compute
    semantic similarity scores between text and images. Higher scores
    indicate better alignment/relevance.
    
    Scores range from -1 to 1 (cosine similarity), but typically
    CLIP produces scores in the range [0, 1] for positive pairs.
    """

    def __init__(self, config: AlignmentConfig, device: Optional[str] = None):
        """
        Initialize the CLIP alignment scorer.
        
        Args:
            config: AlignmentConfig instance with scoring parameters
            device: Device to run CLIP on ('cuda', 'cpu', or None for auto)
        """
        self.config = config

        if not CLIP_AVAILABLE:
            self._model = None
            self._processor = None
            self._device = None
            logger.warning("CLIP not available, alignment scoring will be skipped")
            return

        # Auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self._device = device

        try:
            # Load CLIP model and processor
            # Using ViT-B/32 as it's a good balance of speed and accuracy
            model_name = "openai/clip-vit-base-patch32"
            logger.info(f"Loading CLIP model: {model_name} on {device}")

            # NOTE: For security, pin to a specific commit hash using revision parameter
            # Example: revision="abc123def456..." (get from HuggingFace model page)
            # For now using main, but should be pinned to specific commit in production
            self._model = CLIPModel.from_pretrained(
                model_name,
                revision="main"  # TODO: Pin to specific commit hash for security
            ).to(device)
            self._processor = CLIPProcessor.from_pretrained(
                model_name,
                revision="main"  # TODO: Pin to specific commit hash for security
            )

            # Set to evaluation mode
            self._model.eval()

            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            self._model = None
            self._processor = None
            self._device = None

    def is_available(self) -> bool:
        """Check if CLIP is available and loaded."""
        return (
            CLIP_AVAILABLE
            and self._model is not None
            and self._processor is not None
        )

    def score_text_image(
        self, text: str, image_path: str
    ) -> Tuple[Optional[float], Dict]:
        """
        Compute CLIP similarity score between text and image.
        
        Args:
            text: Text content to compare
            image_path: Path to image file
            
        Returns:
            Tuple of (score: Optional[float], stats: dict)
            - score: CLIP similarity score (0-1 range, higher = more relevant)
                     or None if scoring failed
            - stats: Dictionary with scoring metadata
        """
        if not self.is_available():
            return None, {
                "score": None,
                "reason": "clip_not_available",
                "passed": True,  # Graceful fallback: pass if CLIP unavailable
            }

        try:
            # Load and preprocess image
            path = pathlib.Path(image_path)
            if not path.is_absolute():
                # Try relative to project root
                project_root = pathlib.Path(__file__).resolve().parents[2]
                path = project_root / path

            if not path.exists():
                logger.debug(f"Image file not found for CLIP scoring: {path}")
                return None, {
                    "score": None,
                    "reason": "image_not_found",
                    "passed": True,  # Graceful fallback
                }

            # Open image
            with Image.open(path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                # Process inputs
                inputs = self._processor(
                    text=[text],
                    images=[img],
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                )

                # Move inputs to device
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

                # Compute similarity using CLIP
                with torch.no_grad():
                    # Get image and text features
                    image_features = self._model.get_image_features(
                        pixel_values=inputs["pixel_values"]
                    )
                    text_features = self._model.get_text_features(
                        input_ids=inputs["input_ids"],
                        attention_mask=inputs.get("attention_mask")
                    )

                    # Normalize features (CLIP uses normalized embeddings)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)

                    # Compute cosine similarity (dot product of normalized vectors)
                    # This gives us a score in [-1, 1] range
                    cosine_sim = (image_features @ text_features.T).squeeze().item()

                    # Normalize to [0, 1] range: (cosine_sim + 1) / 2
                    # This maps: -1 (dissimilar) -> 0, 0 (neutral) -> 0.5, 1 (similar) -> 1
                    score = (cosine_sim + 1.0) / 2.0

                    # Ensure score is in [0, 1] and clamp if needed
                    score = max(0.0, min(1.0, score))

                # Check if score meets threshold
                passed = score >= self.config.min_clip_score

                stats = {
                    "score": round(score, 4),
                    "min_clip_score": self.config.min_clip_score,
                    "passed": passed,
                    "reason": "passed" if passed else f"score_too_low: {score:.4f} < {self.config.min_clip_score:.4f}",
                }

                return score, stats

        except Exception as e:
            logger.debug(f"Error computing CLIP score for {image_path}: {e}")
            return None, {
                "score": None,
                "reason": f"scoring_error: {str(e)}",
                "passed": True,  # Graceful fallback
            }

    def score_text_images(
        self, text: str, images: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Score multiple images against text and filter by alignment score.
        
        Args:
            text: Text content to compare against
            images: List of image dictionaries with 'path' key
            
        Returns:
            Tuple of (aligned_images: List[Dict], misaligned_images: List[Dict])
            - aligned_images: Images that meet min_clip_score threshold
            - misaligned_images: Images that don't meet threshold (include score in metadata)
        """
        if not self.is_available():
            # Graceful fallback: if CLIP unavailable, pass all images
            logger.debug("CLIP not available, skipping alignment filtering")
            return images, []

        aligned_images = []
        misaligned_images = []

        for image in images:
            image_path = image.get("path")

            if not image_path:
                # No path available, can't score - keep it (lenient)
                aligned_images.append(image)
                continue

            score, stats = self.score_text_image(text, image_path)

            if score is None:
                # Scoring failed - keep image (lenient)
                aligned_images.append(image)
                continue

            # Add score to image metadata
            image_with_score = image.copy()
            image_with_score["clip_score"] = stats["score"]
            image_with_score["clip_stats"] = stats

            if stats["passed"]:
                aligned_images.append(image_with_score)
            else:
                image_with_score["filter_reason"] = stats["reason"]
                misaligned_images.append(image_with_score)

        return aligned_images, misaligned_images

    def filter_by_alignment(
        self, text: str, images: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter images based on text-image alignment score.
        
        This is the main entry point for filtering images by relevance.
        
        Args:
            text: Text content to compare against
            images: List of image dictionaries with 'path' key
            
        Returns:
            Tuple of (aligned_images: List[Dict], misaligned_images: List[Dict])
        """
        return self.score_text_images(text, images)

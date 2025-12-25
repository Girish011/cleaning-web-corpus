"""
Image caption generation using BLIP-2.

This module provides BLIP-2-based image captioning to generate
descriptive captions for images in the corpus.
"""

import logging
import pathlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PIL import Image

logger = logging.getLogger(__name__)

# Try to import BLIP-2 dependencies, handle gracefully if not available
try:
    import torch
    from transformers import Blip2Processor, Blip2ForConditionalGeneration
    BLIP2_AVAILABLE = True
except ImportError:
    BLIP2_AVAILABLE = False
    logger.warning(
        "BLIP-2 dependencies not available. Install with: pip install torch transformers accelerate"
    )


class BLIP2Captioner:
    """
    BLIP-2-based image caption generator.
    
    Uses BLIP-2 (Bootstrapping Language-Image Pre-training) to generate
    detailed captions for images. Better than CLIP for detailed descriptions.
    """

    def __init__(
        self,
        model_name: str = "Salesforce/blip2-opt-2.7b",
        device: Optional[str] = None,
        max_length: int = 50,
        min_confidence: float = 0.5,
    ):
        """
        Initialize the BLIP-2 captioner.
        
        Args:
            model_name: BLIP-2 model name
                - "Salesforce/blip2-opt-2.7b" (default, smaller, faster)
                - "Salesforce/blip2-opt-6.7b" (larger, better quality)
                - "Salesforce/blip2-flan-t5-xl" (alternative architecture)
            device: Device to run on ('cuda', 'cpu', or None for auto)
            max_length: Maximum caption length in tokens
            min_confidence: Minimum confidence threshold (not used by BLIP-2, kept for API compatibility)
        """
        self.model_name = model_name
        self.max_length = max_length
        self.min_confidence = min_confidence

        if not BLIP2_AVAILABLE:
            self._model = None
            self._processor = None
            self._device = None
            logger.warning("BLIP-2 not available, captioning will be skipped")
            return

        # Auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self._device = device

        try:
            logger.info(f"Loading BLIP-2 model: {model_name} on {device}")

            # Load processor and model
            # NOTE: For security, pin to a specific commit hash using revision parameter
            # Example: revision="abc123def456..." (get from HuggingFace model page)
            # For now using main, but should be pinned to specific commit in production
            self._processor = Blip2Processor.from_pretrained(
                model_name,
                revision="main"  # TODO: Pin to specific commit hash for security
            )
            self._model = Blip2ForConditionalGeneration.from_pretrained(
                model_name,
                revision="main",  # TODO: Pin to specific commit hash for security
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
            )

            if device == "cpu":
                self._model = self._model.to(device)

            # Set to evaluation mode
            self._model.eval()

            logger.info("BLIP-2 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load BLIP-2 model: {e}")
            self._model = None
            self._processor = None
            self._device = None

    def is_available(self) -> bool:
        """Check if BLIP-2 is available and loaded."""
        return (
            BLIP2_AVAILABLE
            and self._model is not None
            and self._processor is not None
        )

    def generate_caption(
        self, image_path: str, prompt: Optional[str] = None
    ) -> Tuple[Optional[str], Dict]:
        """
        Generate caption for an image.
        
        Args:
            image_path: Path to image file (relative or absolute)
            prompt: Optional prompt to guide caption generation
                    (e.g., "a photo of" for more descriptive captions)
            
        Returns:
            Tuple of (caption: Optional[str], metadata: dict)
            - caption: Generated caption or None if generation failed
            - metadata: Dictionary with generation metadata
        """
        if not self.is_available():
            return None, {
                "caption": None,
                "reason": "blip2_not_available",
                "model": self.model_name,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

        try:
            # Load and preprocess image
            path = pathlib.Path(image_path)
            if not path.is_absolute():
                # Try relative to project root
                project_root = pathlib.Path(__file__).resolve().parents[2]
                path = project_root / path

            if not path.exists():
                logger.debug(f"Image file not found for captioning: {path}")
                return None, {
                    "caption": None,
                    "reason": "image_not_found",
                    "model": self.model_name,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                }

            # Open image
            with Image.open(path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                # Prepare prompt
                if prompt is None:
                    prompt = "a photo of"

                # Process inputs
                inputs = self._processor(
                    images=img,
                    text=prompt,
                    return_tensors="pt",
                ).to(self._device)

                # Generate caption
                with torch.no_grad():
                    generated_ids = self._model.generate(
                        **inputs,
                        max_length=self.max_length,
                        num_beams=3,
                        do_sample=False,
                    )

                # Decode caption
                generated_text = self._processor.batch_decode(
                    generated_ids, skip_special_tokens=True
                )[0].strip()

                # Clean up caption (remove prompt if present)
                if prompt.lower() in generated_text.lower():
                    generated_text = generated_text.replace(prompt, "", 1).strip()

                metadata = {
                    "caption": generated_text,
                    "model": self.model_name,
                    "prompt": prompt,
                    "max_length": self.max_length,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "device": self._device,
                }

                return generated_text, metadata

        except Exception as e:
            logger.debug(f"Error generating caption for {image_path}: {e}")
            return None, {
                "caption": None,
                "reason": f"generation_error: {str(e)}",
                "model": self.model_name,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

    def caption_images(
        self, images: List[Dict], prompt: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate captions for multiple images.
        
        Args:
            images: List of image dictionaries with 'path' key
            prompt: Optional prompt to guide caption generation
            
        Returns:
            List of image dictionaries with added 'caption' and 'caption_metadata' fields
        """
        if not self.is_available():
            logger.debug("BLIP-2 not available, skipping captioning")
            return images

        captioned_images = []

        for image in images:
            image_path = image.get("path")

            if not image_path:
                # No path available, can't caption - keep original
                captioned_images.append(image)
                continue

            caption, metadata = self.generate_caption(image_path, prompt)

            # Add caption to image metadata
            image_with_caption = image.copy()

            if caption:
                image_with_caption["caption"] = caption
                image_with_caption["caption_metadata"] = metadata
            else:
                # Caption generation failed, but keep image
                image_with_caption["caption"] = None
                image_with_caption["caption_metadata"] = metadata

            captioned_images.append(image_with_caption)

        return captioned_images

    def caption_image_batch(
        self, images: List[Dict], prompt: Optional[str] = None, batch_size: int = 4
    ) -> List[Dict]:
        """
        Generate captions for images in batches (more efficient).
        
        Args:
            images: List of image dictionaries with 'path' key
            prompt: Optional prompt to guide caption generation
            batch_size: Number of images to process at once
            
        Returns:
            List of image dictionaries with added 'caption' and 'caption_metadata' fields
        """
        if not self.is_available():
            return self.caption_images(images, prompt)

        # Process in batches for efficiency
        captioned_images = []

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            captioned_batch = self.caption_images(batch, prompt)
            captioned_images.extend(captioned_batch)

        return captioned_images

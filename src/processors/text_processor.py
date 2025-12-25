import json
import pathlib
from datetime import datetime
import os
import logging

import requests
import trafilatura

from src.config import get_config
from src.quality.text_filters import TextQualityFilter
from src.quality.image_filters import ImageQualityFilter
from src.quality.alignment import CLIPAlignmentScorer
from src.enrichment.enricher import EnrichmentPipeline
from src.enrichment.captioner import BLIP2Captioner

# Load validated config
config = get_config()

ROOT = pathlib.Path(__file__).resolve().parents[2]  # Updated: 2 levels up to repo root

# Get config values with type safety
MIN_WORDS = int(os.getenv("MIN_WORDS", str(config.quality.text.min_words)))

RAW_PATH = ROOT / "data" / "raw" / "seed_pages.jsonl"
OUT_PATH = ROOT / "data" / "processed" / "cleaning_docs.jsonl"

# Setup logging from config
log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format=config.logging.format,
)
logger = logging.getLogger(__name__)


def infer_source_type(url: str) -> str:
    """Infer source type from URL (legacy function, kept for backward compatibility)."""
    if "puffy.com" in url or "maidbrigade.com" in url:
        return "pillows_bedding"
    if "whirlpool.com" in url or "ariel.in" in url or "cleaninginstitute.org" in url:
        return "clothes"
    if "vanish.co.in" in url or "floorworld.com.au" in url or "mycleaners.in" in url or "spincycles.in" in url:
        return "carpets_floors"
    return "unknown"

def process_url(url: str, title: str, image_urls: list = None, video_urls: list = None, image_details: list = None, video_metadata: list = None) -> dict | None:
    try:
        resp = requests.get(url, timeout=20)
    except Exception:
        return None

    status = resp.status_code
    html = resp.text

    downloaded = trafilatura.Document(html, url=url) if hasattr(trafilatura, "Document") else None
    if downloaded is not None:
        main_text = trafilatura.extract(downloaded) or ""
    else:
        main_text = trafilatura.extract(html) or ""

    if not main_text.strip():
        # skip if we couldn't get meaningful text
        return None

    # Apply text quality filters (includes repetition filter)
    text_filter = TextQualityFilter(config.quality.text)
    filter_result = text_filter.filter(main_text)

    if not filter_result["passed"]:
        reason = filter_result['reason']
        # Log with more detail for repetition failures
        if 'repetition' in reason.lower():
            logger.info(f"Text quality filter failed for {url}: {reason}")
            # Log repetition stats if available
            stats = filter_result.get('stats', {})
            if 'char_repetition_ratio' in stats:
                logger.debug(f"  Char repetition ratio: {stats['char_repetition_ratio']:.3f}")
            if 'word_repetition_ratio' in stats:
                logger.debug(f"  Word repetition ratio: {stats['word_repetition_ratio']:.3f}")
            if 'max_ngram_repetition' in stats:
                logger.debug(f"  Max n-gram repetition: {stats['max_ngram_repetition']}")
        else:
            logger.debug(f"Text quality filter failed for {url}: {reason}")
        return None

    # Create base record (before enrichment)
    now_iso = datetime.utcnow().isoformat() + "Z"

    base_record = {
        "url": url,
        "title": title,
        "source_type": infer_source_type(url),
        "raw_html": html,
        "main_text": main_text,
        "language": "en",
        "fetched_at": now_iso,
        "http_status": status,
        "image_urls": [],
        "video_urls": video_urls or [],
        "image_details": image_details or [],
        "video_metadata": video_metadata or [],
    }

    # Note: Image filtering happens later in main() after images are downloaded
    # For now, just store image URLs
    base_record["image_urls"] = image_urls or []

    return base_record


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw file not found: {RAW_PATH}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    kept = 0
    skipped_empty = 0
    skipped_quality = 0
    skipped_other = 0
    total = 0

    # Initialize CLIP alignment scorer once (model loading is expensive)
    # This is Phase-3.7: CLIP text-image alignment scoring
    alignment_scorer = CLIPAlignmentScorer(config.quality.alignment)
    if alignment_scorer.is_available():
        logger.info("CLIP alignment scorer initialized successfully")
    else:
        logger.info("CLIP alignment scorer not available (will skip alignment filtering)")

    # Initialize enrichment pipeline (Phase 4.1/4.2: Structured extraction)
    enrichment_pipeline = EnrichmentPipeline(
        extraction_method=config.enrichment.extraction.method,
        enable_tools_extraction=config.enrichment.extraction.enable_tools_extraction,
        enable_steps_extraction=config.enrichment.extraction.enable_steps_extraction,
        min_steps_confidence=config.enrichment.extraction.min_steps_confidence,
        # NER config
        ner_model_name=config.enrichment.extraction.ner.model_name,
        # LLM config
        llm_provider=config.enrichment.extraction.llm.provider,
        llm_model=config.enrichment.extraction.llm.model,
        llm_api_key=config.enrichment.extraction.llm.api_key,
        llm_temperature=config.enrichment.extraction.llm.temperature,
        llm_max_tokens=config.enrichment.extraction.llm.max_tokens,
        llm_enable_caching=config.enrichment.extraction.llm.enable_caching,
        llm_cache_ttl_days=config.enrichment.extraction.llm.cache_ttl_days,
    )
    logger.info(f"Enrichment pipeline initialized (method: {config.enrichment.extraction.method})")

    # Initialize BLIP-2 captioner (Phase 4.3: Image captioning)
    if config.enrichment.captioning.enable:
        device = config.enrichment.captioning.device
        if device == "auto":
            device = None  # Let BLIP2Captioner auto-detect

        captioner = BLIP2Captioner(
            model_name=config.enrichment.captioning.model,
            device=device,
            max_length=config.enrichment.captioning.max_length,
            min_confidence=config.enrichment.captioning.min_confidence,
        )
        if captioner.is_available():
            logger.info(f"BLIP-2 captioner initialized (model: {config.enrichment.captioning.model})")
        else:
            logger.info("BLIP-2 captioner not available (will skip captioning)")
    else:
        captioner = None
        logger.info("Image captioning disabled in configuration")

    with RAW_PATH.open() as fin, OUT_PATH.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            total += 1
            obj = json.loads(line)
            url = obj.get("url")
            title = obj.get("title", "")
            image_urls = obj.get("image_urls", [])
            video_urls = obj.get("video_urls", [])
            image_details = obj.get("image_details", [])
            video_metadata = obj.get("video_metadata", [])
            if not url:
                skipped_other += 1
                continue

            record = process_url(url, title, image_urls, video_urls, image_details, video_metadata)
            if record is None:
                # Track different failure reasons
                skipped_quality += 1
                continue

            # Apply enrichment (Phase 4.1: Structured extraction)
            # This extracts: surface_type, dirt_type, cleaning_method, tools, steps
            record = enrichment_pipeline.enrich(record)

            # Apply image quality filters if images metadata is available
            images_metadata = obj.get("images", [])
            if images_metadata:
                image_filter = ImageQualityFilter(config.quality.image)
                passed_images, failed_images = image_filter.filter_images(images_metadata)

                # Apply CLIP text-image alignment scoring (Phase-3.7)
                # This is a key differentiator for multi-modal quality
                if passed_images and record.get("main_text"):
                    if alignment_scorer.is_available():
                        aligned_images, misaligned_images = alignment_scorer.filter_by_alignment(
                            record["main_text"], passed_images
                        )

                        # Update passed_images with aligned images
                        passed_images = aligned_images

                        # Add misaligned images to failed_images for logging
                        if misaligned_images:
                            failed_images.extend(misaligned_images)
                            logger.debug(
                                f"CLIP alignment filtered out {len(misaligned_images)} images for {url} "
                                f"(low relevance scores)"
                            )
                            for misaligned_img in misaligned_images[:3]:  # Log first 3
                                score = misaligned_img.get("clip_score", "N/A")
                                reason = misaligned_img.get("filter_reason", "unknown")
                                logger.debug(f"  - {misaligned_img.get('url', 'unknown')}: {reason} (score: {score})")
                    # If CLIP not available, passed_images remain unchanged (graceful fallback)

                # Apply image captioning (Phase 4.3: BLIP-2 captioning)
                if passed_images and captioner and captioner.is_available():
                    prompt = config.enrichment.captioning.prompt
                    captioned_images = captioner.caption_images(passed_images, prompt=prompt)
                    passed_images = captioned_images

                    # Log captioning stats
                    captioned_count = sum(1 for img in captioned_images if img.get("caption"))
                    if captioned_count > 0:
                        logger.debug(
                            f"Generated captions for {captioned_count}/{len(captioned_images)} images for {url}"
                        )

                # Update record with filtered images
                record["images"] = passed_images

                if failed_images:
                    # Count duplicates separately
                    duplicates = [f for f in failed_images if "duplicate" in f.get("filter_reason", "").lower()]
                    # Count misaligned separately
                    misaligned = [f for f in failed_images if "score_too_low" in f.get("filter_reason", "")]
                    other_failures = [
                        f for f in failed_images
                        if "duplicate" not in f.get("filter_reason", "").lower()
                        and "score_too_low" not in f.get("filter_reason", "")
                    ]

                    logger.debug(
                        f"Filtered out {len(failed_images)} images for {url} "
                        f"({len(duplicates)} duplicates, {len(misaligned)} misaligned, {len(other_failures)} quality failures)"
                    )
                    for failed_img in failed_images[:3]:  # Log first 3 failures
                        reason = failed_img.get('filter_reason', 'unknown')
                        logger.debug(f"  - {failed_img.get('url', 'unknown')}: {reason}")

            kept += 1
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(f"Total raw records: {total}")
    logger.info(f"Kept after filtering: {kept}")
    logger.info(f"Skipped (quality filters): {skipped_quality}")
    logger.info(f"Skipped (other): {skipped_other}")

if __name__ == "__main__":
    main()

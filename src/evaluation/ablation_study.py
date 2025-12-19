"""
Quality ablation study module for Phase 5.2.

This module performs research-style ablation studies to measure the impact
of each quality filter on dataset size and quality.
"""

import json
import pathlib
import copy
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime

from src.config import Config, TextQualityConfig, ImageQualityConfig, AlignmentConfig, get_config
from src.quality.text_filters import TextQualityFilter
from src.quality.image_filters import ImageQualityFilter
from src.quality.alignment import CLIPAlignmentScorer


class AblationStudy:
    """
    Ablation study to measure filter impact.
    
    Tests each filter individually and in combinations to understand:
    - Retention rate (how much data is kept)
    - Filter overlap (which filters remove the same items)
    - Quality impact (aggregate quality metrics)
    """
    
    # Define all filter names
    TEXT_FILTERS = [
        "word_count",
        "avg_word_length",
        "language",
        "repetition",
        "perplexity",
    ]
    
    IMAGE_FILTERS = [
        "resolution",
        "aspect_ratio",
        "format",
        "duplicate_detection",
    ]
    
    ALIGNMENT_FILTERS = [
        "clip_alignment",
    ]
    
    ALL_FILTERS = TEXT_FILTERS + IMAGE_FILTERS + ALIGNMENT_FILTERS
    
    def __init__(self, processed_data_path: pathlib.Path, config: Optional[Config] = None):
        """
        Initialize ablation study.
        
        Args:
            processed_data_path: Path to processed JSONL file (with extracted text)
            config: Configuration object (uses default if None)
        """
        self.processed_data_path = processed_data_path
        self.config = config or get_config()
        self.documents = []
        self.results = []
        self.filter_overlap = defaultdict(set)  # filter_name -> set of document indices removed
        
    def load_data(self) -> None:
        """Load processed documents from JSONL file."""
        if not self.processed_data_path.exists():
            raise FileNotFoundError(f"Processed data file not found: {self.processed_data_path}")
        
        self.documents = []
        with self.processed_data_path.open(encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line)
                    self.documents.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON line: {e}")
                    continue
        
        print(f"Loaded {len(self.documents)} documents")
    
    def _apply_text_filter(
        self, 
        text: str, 
        enabled_filters: Set[str],
        config: TextQualityConfig
    ) -> Tuple[bool, str, Dict]:
        """
        Apply text filters selectively.
        
        Args:
            text: Text to filter
            enabled_filters: Set of filter names to enable
            config: Text quality config
            
        Returns:
            Tuple of (passed: bool, reason: str, stats: dict)
        """
        if not text or not text.strip():
            return False, "empty_text", {}
        
        # Normalize text
        words = text.split()
        normalized_text = text.strip()
        
        stats = {}
        
        # Word count filter
        if "word_count" in enabled_filters:
            word_count = len(words)
            if word_count < config.min_words or word_count > config.max_words:
                if word_count < config.min_words:
                    reason = f"word_count_too_low: {word_count} < {config.min_words}"
                else:
                    reason = f"word_count_too_high: {word_count} > {config.max_words}"
                return False, reason, {"word_count": word_count}
            stats["word_count"] = word_count
        
        # Average word length filter
        if "avg_word_length" in enabled_filters:
            if not words:
                return False, "no_words", {}
            avg_length = sum(len(word) for word in words) / len(words)
            if avg_length < config.min_avg_word_length:
                return False, f"avg_word_length_too_low: {avg_length:.2f} < {config.min_avg_word_length:.2f}", \
                       {"avg_word_length": avg_length}
            stats["avg_word_length"] = avg_length
        
        # Language filter
        if "language" in enabled_filters:
            try:
                from langdetect import detect
                detected_lang = detect(normalized_text)
                if detected_lang != config.language:
                    return False, f"language_mismatch: {detected_lang} != {config.language}", \
                           {"detected_language": detected_lang}
                stats["detected_language"] = detected_lang
            except (ImportError, Exception):
                # If langdetect unavailable, skip this filter
                pass
        
        # Repetition filter
        if "repetition" in enabled_filters:
            # Simplified repetition check - use TextQualityFilter for full logic
            filter_obj = TextQualityFilter(config)
            repetition_passed, repetition_stats = filter_obj.check_repetition(normalized_text)
            stats.update(repetition_stats)
            if not repetition_passed:
                reason = repetition_stats.get("reason", "repetition_failed")
                return False, reason, stats
        
        # Perplexity filter
        if "perplexity" in enabled_filters:
            if not config.enable_perplexity_filter or not config.kenlm_model_path:
                # Skip if not configured
                pass
            else:
                filter_obj = TextQualityFilter(config)
                perplexity_passed, perplexity_stats = filter_obj.check_perplexity(normalized_text)
                stats.update(perplexity_stats)
                if not perplexity_passed:
                    perplexity = perplexity_stats.get("perplexity", 0.0)
                    return False, f"perplexity_too_high: {perplexity:.2f}", stats
        
        return True, "passed", stats
    
    def _apply_image_filters(
        self,
        images: List[Dict],
        enabled_filters: Set[str],
        config: ImageQualityConfig
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Apply image filters selectively.
        
        Args:
            images: List of image metadata dictionaries
            enabled_filters: Set of filter names to enable
            config: Image quality config
            
        Returns:
            Tuple of (passed_images, failed_images)
        """
        if not images:
            return [], []
        
        passed = []
        failed = []
        
        for img in images:
            if "error" in img:
                failed.append(img)
                continue
            
            width = img.get("width")
            height = img.get("height")
            path = img.get("path", "")
            url = img.get("url", "")
            
            # Resolution filter
            if "resolution" in enabled_filters:
                min_width, min_height = config.min_resolution
                if width is None or height is None:
                    # Unknown dimensions - be lenient
                    pass
                elif width < min_width or height < min_height:
                    failed.append({**img, "filter_reason": f"resolution_too_small: {width}x{height}"})
                    continue
            
            # Aspect ratio filter
            if "aspect_ratio" in enabled_filters:
                if width and height and height > 0:
                    aspect_ratio = max(width, height) / min(width, height)
                    if aspect_ratio > config.max_aspect_ratio:
                        failed.append({**img, "filter_reason": f"aspect_ratio_too_extreme: {aspect_ratio:.2f}"})
                        continue
            
            # Format filter
            if "format" in enabled_filters:
                ext = None
                if path:
                    ext = pathlib.Path(path).suffix.lower().lstrip('.')
                elif url:
                    ext = pathlib.Path(url).suffix.lower().lstrip('.')
                
                if ext and ext not in config.allowed_formats:
                    failed.append({**img, "filter_reason": f"format_not_allowed: {ext}"})
                    continue
            
            # If passed all individual checks, add to passed list
            passed.append(img)
        
        # Apply duplicate detection if enabled and we have multiple images
        if "duplicate_detection" in enabled_filters and len(passed) >= config.min_images_for_duplicate_check:
            image_filter = ImageQualityFilter(config)
            unique_images, duplicate_images = image_filter.filter_images(passed)
            # Replace passed with unique images, add duplicates to failed
            passed = unique_images
            failed.extend(duplicate_images)
        
        return passed, failed
    
    def _apply_alignment_filter(
        self,
        text: str,
        images: List[Dict],
        enabled_filters: Set[str],
        config: AlignmentConfig
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Apply CLIP alignment filter selectively.
        
        Args:
            text: Text content
            images: List of images
            enabled_filters: Set of filter names to enable
            config: Alignment config
            
        Returns:
            Tuple of (aligned_images, misaligned_images)
        """
        if "clip_alignment" not in enabled_filters:
            return images, []
        
        if not images or not text:
            return images, []
        
        alignment_scorer = CLIPAlignmentScorer(config)
        if not alignment_scorer.is_available():
            # CLIP not available - pass all images
            return images, []
        
        aligned, misaligned = alignment_scorer.filter_by_alignment(text, images)
        return aligned, misaligned
    
    def _process_document_with_filters(
        self,
        doc: Dict,
        enabled_filters: Set[str]
    ) -> Tuple[bool, str, Dict]:
        """
        Process a single document with specified filters enabled.
        
        Args:
            doc: Processed document dictionary (with extracted text)
            enabled_filters: Set of filter names to enable
            
        Returns:
            Tuple of (passed: bool, reason: str, stats: dict)
        """
        # Get text from processed document
        text = doc.get("main_text", "") or ""
        if not text:
            return False, "no_text", {}
        
        # Apply text filters
        text_passed, text_reason, text_stats = self._apply_text_filter(
            text,
            enabled_filters,
            self.config.quality.text
        )
        
        if not text_passed:
            return False, text_reason, text_stats
        
        # Apply image filters if images exist
        images = doc.get("images", [])
        if images:
            passed_images, failed_images = self._apply_image_filters(
                images,
                enabled_filters,
                self.config.quality.image
            )
            
            # Apply alignment filter
            if passed_images:
                aligned_images, misaligned_images = self._apply_alignment_filter(
                    text,
                    passed_images,
                    enabled_filters,
                    self.config.quality.alignment
                )
                passed_images = aligned_images
            
            # If all images were filtered out, we might want to fail the document
            # For now, we'll pass documents even if images are filtered
            # (This is a design choice - adjust as needed)
        
        return True, "passed", text_stats
    
    def run_ablation(self) -> Dict:
        """
        Run complete ablation study.
        
        Returns:
            Dictionary with ablation results
        """
        if not self.documents:
            self.load_data()
        
        baseline_count = len(self.documents)
        results = []
        
        # Baseline: no filters
        print("Running baseline (no filters)...")
        baseline_passed = []
        for idx, doc in enumerate(self.documents):
            passed, reason, stats = self._process_document_with_filters(doc, set())
            if passed:
                baseline_passed.append(idx)
        
        baseline_retention = len(baseline_passed) / baseline_count if baseline_count > 0 else 0
        results.append({
            "filter_combination": "baseline",
            "enabled_filters": [],
            "documents_passed": len(baseline_passed),
            "documents_failed": baseline_count - len(baseline_passed),
            "retention_rate": baseline_retention,
            "rejection_rate": 1 - baseline_retention,
        })
        
        # Individual filters
        print("Testing individual filters...")
        for filter_name in self.ALL_FILTERS:
            print(f"  Testing filter: {filter_name}")
            enabled = {filter_name}
            passed_indices = []
            failed_reasons = defaultdict(int)
            
            for idx, doc in enumerate(self.documents):
                passed, reason, stats = self._process_document_with_filters(doc, enabled)
                if passed:
                    passed_indices.append(idx)
                else:
                    failed_reasons[reason] += 1
                    self.filter_overlap[filter_name].add(idx)
            
            retention = len(passed_indices) / baseline_count if baseline_count > 0 else 0
            results.append({
                "filter_combination": filter_name,
                "enabled_filters": [filter_name],
                "documents_passed": len(passed_indices),
                "documents_failed": baseline_count - len(passed_indices),
                "retention_rate": retention,
                "rejection_rate": 1 - retention,
                "failed_reasons": dict(failed_reasons),
            })
        
        # All filters together
        print("Testing all filters together...")
        all_enabled = set(self.ALL_FILTERS)
        passed_indices = []
        for idx, doc in enumerate(self.documents):
            passed, reason, stats = self._process_document_with_filters(doc, all_enabled)
            if passed:
                passed_indices.append(idx)
        
        retention = len(passed_indices) / baseline_count if baseline_count > 0 else 0
        results.append({
            "filter_combination": "all_filters",
            "enabled_filters": list(all_enabled),
            "documents_passed": len(passed_indices),
            "documents_failed": baseline_count - len(passed_indices),
            "retention_rate": retention,
            "rejection_rate": 1 - retention,
        })
        
        # Filter overlap analysis
        overlap_analysis = self._analyze_filter_overlap()
        
        self.results = results
        
        return {
            "metadata": {
                "computed_at": datetime.now().isoformat(),
                "processed_data_file": str(self.processed_data_path),
                "baseline_documents": baseline_count,
            },
            "results": results,
            "filter_overlap": overlap_analysis,
        }
    
    def _analyze_filter_overlap(self) -> Dict:
        """Analyze which filters remove the same documents."""
        overlap_matrix = {}
        
        filter_names = list(self.filter_overlap.keys())
        for i, filter1 in enumerate(filter_names):
            for filter2 in filter_names[i+1:]:
                set1 = self.filter_overlap[filter1]
                set2 = self.filter_overlap[filter2]
                
                intersection = set1 & set2
                union = set1 | set2
                
                if union:
                    jaccard = len(intersection) / len(union)
                else:
                    jaccard = 0.0
                
                overlap_matrix[f"{filter1}_x_{filter2}"] = {
                    "filter1_removed": len(set1),
                    "filter2_removed": len(set2),
                    "both_removed": len(intersection),
                    "either_removed": len(union),
                    "jaccard_similarity": round(jaccard, 4),
                }
        
        return overlap_matrix
    
    def save_json(self, output_path: pathlib.Path) -> None:
        """Save ablation results as JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results_dict = {
            "metadata": {
                "computed_at": datetime.now().isoformat(),
                "processed_data_file": str(self.processed_data_path),
            },
            "results": self.results,
            "filter_overlap": self._analyze_filter_overlap(),
        }
        
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
    
    def save_text_report(self, output_path: pathlib.Path) -> None:
        """Save ablation results as human-readable text report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        lines.append("=" * 80)
        lines.append("QUALITY FILTER ABLATION STUDY")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Processed data file: {self.processed_data_path}")
        lines.append("")
        
        # Summary table
        lines.append("FILTER IMPACT SUMMARY")
        lines.append("-" * 80)
        lines.append(f"{'Filter Combination':<30} {'Retention %':<15} {'Rejection %':<15} {'Passed':<10} {'Failed':<10}")
        lines.append("-" * 80)
        
        for result in self.results:
            combo = result["filter_combination"]
            retention_pct = result["retention_rate"] * 100
            rejection_pct = result["rejection_rate"] * 100
            passed = result["documents_passed"]
            failed = result["documents_failed"]
            
            lines.append(f"{combo:<30} {retention_pct:>13.2f}% {rejection_pct:>13.2f}% {passed:>9} {failed:>9}")
        
        lines.append("")
        
        # Filter overlap
        lines.append("FILTER OVERLAP ANALYSIS")
        lines.append("-" * 80)
        overlap = self._analyze_filter_overlap()
        for pair, metrics in sorted(overlap.items()):
            lines.append(f"{pair}:")
            lines.append(f"  Filter 1 removed: {metrics['filter1_removed']}")
            lines.append(f"  Filter 2 removed: {metrics['filter2_removed']}")
            lines.append(f"  Both removed: {metrics['both_removed']}")
            lines.append(f"  Jaccard similarity: {metrics['jaccard_similarity']:.4f}")
            lines.append("")
        
        with output_path.open('w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def save_csv(self, output_path: pathlib.Path) -> None:
        """Save ablation results as CSV."""
        import csv
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "filter_combination",
                "enabled_filters",
                "documents_passed",
                "documents_failed",
                "retention_rate",
                "rejection_rate",
            ])
            
            # Data rows
            for result in self.results:
                writer.writerow([
                    result["filter_combination"],
                    ",".join(result.get("enabled_filters", [])),
                    result["documents_passed"],
                    result["documents_failed"],
                    result["retention_rate"],
                    result["rejection_rate"],
                ])


def main():
    """Main entry point for ablation study."""
    root = pathlib.Path(__file__).resolve().parents[2]
    processed_data_path = root / "data" / "processed" / "cleaning_docs.jsonl"
    output_dir = root / "data" / "evaluation"
    
    if not processed_data_path.exists():
        print(f"Error: Processed data file not found: {processed_data_path}")
        print("Please run the text processor first to generate processed data.")
        return
    
    # Create ablation study
    study = AblationStudy(processed_data_path)
    
    # Run ablation
    print("Starting ablation study...")
    results = study.run_ablation()
    
    # Save outputs
    print("\nSaving reports...")
    study.save_json(output_dir / "ablation_study.json")
    study.save_text_report(output_dir / "ablation_study.txt")
    study.save_csv(output_dir / "ablation_study.csv")
    
    print(f"\nAblation study complete!")
    print(f"Results saved to:")
    print(f"  - {output_dir / 'ablation_study.json'}")
    print(f"  - {output_dir / 'ablation_study.txt'}")
    print(f"  - {output_dir / 'ablation_study.csv'}")


if __name__ == "__main__":
    main()

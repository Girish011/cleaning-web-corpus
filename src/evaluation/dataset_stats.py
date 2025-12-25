"""
Comprehensive dataset statistics module for Phase 5.1.

This module provides detailed statistics about the processed corpus including:
- Basic counts and totals
- Text statistics (word counts, lengths, distributions)
- Image statistics (resolutions, formats, duplicates)
- Coverage analysis (surface_type × dirt_type × cleaning_method)
- Enrichment statistics (tools, steps extraction rates)
- Quality metrics (filter pass/fail rates)
"""

import json
import pathlib
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class DatasetStatistics:
    """
    Comprehensive dataset statistics calculator.
    
    Computes detailed statistics about the processed corpus including
    distributions, coverage analysis, and quality metrics.
    """

    def __init__(self, data_path: pathlib.Path):
        """
        Initialize statistics calculator.
        
        Args:
            data_path: Path to processed JSONL file (cleaning_docs.jsonl)
        """
        self.data_path = data_path
        self.documents = []
        self.stats = {}

    def load_data(self) -> None:
        """Load all documents from JSONL file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        self.documents = []
        with self.data_path.open(encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line)
                    self.documents.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON line: {e}")
                    continue

    def compute_all(self) -> Dict:
        """
        Compute all statistics.
        
        Returns:
            Dictionary containing all computed statistics
        """
        if not self.documents:
            self.load_data()

        self.stats = {
            "metadata": {
                "computed_at": datetime.now().isoformat(),
                "data_file": str(self.data_path),
                "total_documents": len(self.documents),
            },
            "basic": self.compute_basic_stats(),
            "text": self.compute_text_stats(),
            "image": self.compute_image_stats(),
            "coverage": self.compute_coverage_analysis(),
            "enrichment": self.compute_enrichment_stats(),
            "quality": self.compute_quality_metrics(),
        }

        return self.stats

    def compute_basic_stats(self) -> Dict:
        """Compute basic counts and totals."""
        source_counts = Counter()
        language_counts = Counter()
        total_images = 0
        total_videos = 0
        docs_with_images = 0
        docs_with_videos = 0

        for doc in self.documents:
            source_counts[doc.get("source_type", "unknown")] += 1
            language_counts[doc.get("language", "unknown")] += 1

            images = doc.get("images", [])
            if images:
                docs_with_images += 1
                total_images += len(images)

            video_urls = doc.get("video_urls", [])
            if video_urls:
                docs_with_videos += 1
                total_videos += len(video_urls)

        return {
            "total_documents": len(self.documents),
            "source_type_distribution": dict(source_counts),
            "language_distribution": dict(language_counts),
            "images": {
                "total_images": total_images,
                "documents_with_images": docs_with_images,
                "documents_without_images": len(self.documents) - docs_with_images,
                "avg_images_per_doc": round(total_images / len(self.documents), 2) if self.documents else 0,
            },
            "videos": {
                "total_videos": total_videos,
                "documents_with_videos": docs_with_videos,
                "documents_without_videos": len(self.documents) - docs_with_videos,
            },
        }

    def compute_text_stats(self) -> Dict:
        """Compute text statistics including distributions."""
        word_counts = []
        char_counts = []
        avg_word_lengths = []

        for doc in self.documents:
            text = doc.get("main_text", "") or ""
            words = text.split()
            word_count = len(words)
            char_count = len(text)

            word_counts.append(word_count)
            char_counts.append(char_count)

            if words:
                avg_word_length = sum(len(word) for word in words) / len(words)
                avg_word_lengths.append(avg_word_length)

        def compute_percentiles(values: List[float]) -> Dict:
            """Compute percentiles for a list of values."""
            if not values:
                return {}
            sorted_vals = sorted(values)
            return {
                "min": min(values),
                "p25": sorted_vals[len(sorted_vals) // 4],
                "p50": sorted_vals[len(sorted_vals) // 2],  # median
                "p75": sorted_vals[3 * len(sorted_vals) // 4],
                "p95": sorted_vals[95 * len(sorted_vals) // 100] if len(sorted_vals) > 20 else sorted_vals[-1],
                "p99": sorted_vals[99 * len(sorted_vals) // 100] if len(sorted_vals) > 100 else sorted_vals[-1],
                "max": max(values),
                "mean": round(statistics.mean(values), 2),
                "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
            }

        return {
            "word_count": compute_percentiles(word_counts),
            "character_count": compute_percentiles(char_counts),
            "avg_word_length": compute_percentiles(avg_word_lengths) if avg_word_lengths else {},
            "total_words": sum(word_counts),
            "total_characters": sum(char_counts),
        }

    def compute_image_stats(self) -> Dict:
        """Compute image statistics."""
        resolutions = []
        aspect_ratios = []
        formats = Counter()
        file_sizes = []
        total_images = 0

        for doc in self.documents:
            images = doc.get("images", [])
            for img in images:
                if "error" in img:
                    continue

                width = img.get("width")
                height = img.get("height")
                file_size = img.get("file_size")

                if width and height:
                    resolutions.append((width, height))
                    if height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        aspect_ratios.append(aspect_ratio)

                if file_size:
                    file_sizes.append(file_size)

                # Extract format from path or URL
                path = img.get("path", "")
                url = img.get("url", "")
                if path:
                    ext = pathlib.Path(path).suffix.lower().lstrip('.')
                    if ext:
                        formats[ext] += 1
                elif url:
                    ext = pathlib.Path(url).suffix.lower().lstrip('.')
                    if ext:
                        formats[ext] += 1

                total_images += 1

        def compute_resolution_stats(resolutions: List[Tuple[int, int]]) -> Dict:
            """Compute statistics for image resolutions."""
            if not resolutions:
                return {}

            widths = [r[0] for r in resolutions]
            heights = [r[1] for r in resolutions]

            return {
                "width": {
                    "min": min(widths),
                    "max": max(widths),
                    "mean": round(statistics.mean(widths), 2),
                },
                "height": {
                    "min": min(heights),
                    "max": max(heights),
                    "mean": round(statistics.mean(heights), 2),
                },
                "total_images": len(resolutions),
            }

        def compute_percentiles(values: List[float]) -> Dict:
            """Compute percentiles."""
            if not values:
                return {}
            sorted_vals = sorted(values)
            return {
                "min": round(min(values), 2),
                "p25": round(sorted_vals[len(sorted_vals) // 4], 2),
                "p50": round(sorted_vals[len(sorted_vals) // 2], 2),
                "p75": round(sorted_vals[3 * len(sorted_vals) // 4], 2),
                "p95": round(sorted_vals[95 * len(sorted_vals) // 100], 2) if len(sorted_vals) > 20 else round(sorted_vals[-1], 2),
                "max": round(max(values), 2),
                "mean": round(statistics.mean(values), 2),
            }

        return {
            "total_images": total_images,
            "resolutions": compute_resolution_stats(resolutions),
            "aspect_ratios": compute_percentiles(aspect_ratios) if aspect_ratios else {},
            "formats": dict(formats),
            "file_sizes_bytes": compute_percentiles(file_sizes) if file_sizes else {},
        }

    def compute_coverage_analysis(self) -> Dict:
        """Compute coverage analysis (surface × dirt × method)."""
        surface_counts = Counter()
        dirt_counts = Counter()
        method_counts = Counter()

        # Joint distributions
        surface_dirt = defaultdict(lambda: defaultdict(int))
        surface_method = defaultdict(lambda: defaultdict(int))
        dirt_method = defaultdict(lambda: defaultdict(int))
        surface_dirt_method = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for doc in self.documents:
            surface = doc.get("surface_type", "unknown")
            dirt = doc.get("dirt_type", "unknown")
            method = doc.get("cleaning_method", "unknown")

            surface_counts[surface] += 1
            dirt_counts[dirt] += 1
            method_counts[method] += 1

            surface_dirt[surface][dirt] += 1
            surface_method[surface][method] += 1
            dirt_method[dirt][method] += 1
            surface_dirt_method[surface][dirt][method] += 1

        # Convert nested defaultdicts to regular dicts for JSON serialization
        def to_dict(d):
            if isinstance(d, defaultdict):
                return {k: to_dict(v) for k, v in d.items()}
            return d

        return {
            "surface_type_distribution": dict(surface_counts),
            "dirt_type_distribution": dict(dirt_counts),
            "cleaning_method_distribution": dict(method_counts),
            "surface_x_dirt": to_dict(surface_dirt),
            "surface_x_method": to_dict(surface_method),
            "dirt_x_method": to_dict(dirt_method),
            "surface_x_dirt_x_method": to_dict(surface_dirt_method),
            "coverage_summary": {
                "unique_surfaces": len(surface_counts),
                "unique_dirt_types": len(dirt_counts),
                "unique_methods": len(method_counts),
                "total_combinations": sum(
                    sum(sum(1 for _ in methods.values()) for methods in dirts.values())
                    for dirts in surface_dirt_method.values()
                ),
            },
        }

    def compute_enrichment_stats(self) -> Dict:
        """Compute enrichment statistics (tools, steps extraction)."""
        docs_with_tools = 0
        docs_with_steps = 0
        total_tools = 0
        total_steps = 0
        tools_counter = Counter()
        extraction_methods = Counter()

        for doc in self.documents:
            tools = doc.get("tools", [])
            steps = doc.get("steps", [])
            extraction_metadata = doc.get("extraction_metadata", {})

            if tools:
                docs_with_tools += 1
                total_tools += len(tools)
                for tool in tools:
                    if isinstance(tool, str):
                        tools_counter[tool] += 1
                    elif isinstance(tool, dict):
                        tools_counter[tool.get("name", "unknown")] += 1

            if steps:
                docs_with_steps += 1
                total_steps += len(steps)

            method = extraction_metadata.get("extraction_method", "unknown")
            extraction_methods[method] += 1

        return {
            "tools": {
                "documents_with_tools": docs_with_tools,
                "documents_without_tools": len(self.documents) - docs_with_tools,
                "total_tools_extracted": total_tools,
                "avg_tools_per_doc": round(total_tools / docs_with_tools, 2) if docs_with_tools > 0 else 0,
                "most_common_tools": dict(tools_counter.most_common(20)),
            },
            "steps": {
                "documents_with_steps": docs_with_steps,
                "documents_without_steps": len(self.documents) - docs_with_steps,
                "total_steps_extracted": total_steps,
                "avg_steps_per_doc": round(total_steps / docs_with_steps, 2) if docs_with_steps > 0 else 0,
            },
            "extraction_methods": dict(extraction_methods),
        }

    def compute_quality_metrics(self) -> Dict:
        """Compute quality metrics (CLIP scores, filter stats)."""
        clip_scores = []
        docs_with_clip_scores = 0

        for doc in self.documents:
            images = doc.get("images", [])
            for img in images:
                clip_score = img.get("clip_score")
                if clip_score is not None:
                    clip_scores.append(clip_score)
                    docs_with_clip_scores += 1

        def compute_percentiles(values: List[float]) -> Dict:
            """Compute percentiles."""
            if not values:
                return {}
            sorted_vals = sorted(values)
            return {
                "min": round(min(values), 4),
                "p25": round(sorted_vals[len(sorted_vals) // 4], 4),
                "p50": round(sorted_vals[len(sorted_vals) // 2], 4),
                "p75": round(sorted_vals[3 * len(sorted_vals) // 4], 4),
                "p95": round(sorted_vals[95 * len(sorted_vals) // 100], 4) if len(sorted_vals) > 20 else round(sorted_vals[-1], 4),
                "max": round(max(values), 4),
                "mean": round(statistics.mean(values), 4),
            }

        return {
            "clip_scores": {
                "distribution": compute_percentiles(clip_scores) if clip_scores else {},
                "total_images_scored": len(clip_scores),
                "documents_with_scored_images": docs_with_clip_scores,
            },
        }

    def save_json(self, output_path: pathlib.Path) -> None:
        """Save statistics as JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

    def save_text_report(self, output_path: pathlib.Path) -> None:
        """Save statistics as human-readable text report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        lines.append("=" * 80)
        lines.append("DATASET STATISTICS REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.stats['metadata']['computed_at']}")
        lines.append(f"Data file: {self.stats['metadata']['data_file']}")
        lines.append(f"Total documents: {self.stats['metadata']['total_documents']}")
        lines.append("")

        # Basic stats
        lines.append("BASIC STATISTICS")
        lines.append("-" * 80)
        basic = self.stats['basic']
        lines.append(f"Total documents: {basic['total_documents']}")
        lines.append(f"Total images: {basic['images']['total_images']}")
        lines.append(f"Documents with images: {basic['images']['documents_with_images']}")
        lines.append(f"Average images per document: {basic['images']['avg_images_per_doc']}")
        lines.append("")
        lines.append("Source type distribution:")
        for source, count in sorted(basic['source_type_distribution'].items(), key=lambda x: -x[1]):
            lines.append(f"  {source}: {count}")
        lines.append("")

        # Text stats
        lines.append("TEXT STATISTICS")
        lines.append("-" * 80)
        text = self.stats['text']
        if text['word_count']:
            wc = text['word_count']
            lines.append("Word count distribution:")
            lines.append(f"  Min: {wc['min']}, Max: {wc['max']}, Mean: {wc['mean']}")
            lines.append(f"  Percentiles: P25={wc['p25']}, P50={wc['p50']}, P75={wc['p75']}, P95={wc['p95']}")
        lines.append(f"Total words: {text['total_words']:,}")
        lines.append("")

        # Coverage
        lines.append("COVERAGE ANALYSIS")
        lines.append("-" * 80)
        coverage = self.stats['coverage']
        lines.append(f"Unique surface types: {coverage['coverage_summary']['unique_surfaces']}")
        lines.append(f"Unique dirt types: {coverage['coverage_summary']['unique_dirt_types']}")
        lines.append(f"Unique cleaning methods: {coverage['coverage_summary']['unique_methods']}")
        lines.append(f"Total combinations: {coverage['coverage_summary']['total_combinations']}")
        lines.append("")
        lines.append("Surface type distribution:")
        for surface, count in sorted(coverage['surface_type_distribution'].items(), key=lambda x: -x[1]):
            lines.append(f"  {surface}: {count}")
        lines.append("")
        lines.append("Dirt type distribution:")
        for dirt, count in sorted(coverage['dirt_type_distribution'].items(), key=lambda x: -x[1]):
            lines.append(f"  {dirt}: {count}")
        lines.append("")
        lines.append("Cleaning method distribution:")
        for method, count in sorted(coverage['cleaning_method_distribution'].items(), key=lambda x: -x[1]):
            lines.append(f"  {method}: {count}")
        lines.append("")

        # Enrichment
        lines.append("ENRICHMENT STATISTICS")
        lines.append("-" * 80)
        enrichment = self.stats['enrichment']
        lines.append(f"Documents with tools: {enrichment['tools']['documents_with_tools']}")
        lines.append(f"Total tools extracted: {enrichment['tools']['total_tools_extracted']}")
        lines.append(f"Documents with steps: {enrichment['steps']['documents_with_steps']}")
        lines.append(f"Total steps extracted: {enrichment['steps']['total_steps_extracted']}")
        lines.append("Extraction methods:")
        for method, count in sorted(enrichment['extraction_methods'].items(), key=lambda x: -x[1]):
            lines.append(f"  {method}: {count}")
        lines.append("")

        with output_path.open('w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def save_coverage_csv(self, output_path: pathlib.Path) -> None:
        """Save coverage matrix as CSV file."""
        import csv

        output_path.parent.mkdir(parents=True, exist_ok=True)
        coverage = self.stats['coverage']

        # Create surface × dirt × method matrix
        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            surfaces = sorted(coverage['surface_type_distribution'].keys())
            dirts = sorted(coverage['dirt_type_distribution'].keys())
            methods = sorted(coverage['cleaning_method_distribution'].keys())

            header = ['surface_type', 'dirt_type', 'cleaning_method', 'count']
            writer.writerow(header)

            # Data rows
            for surface in surfaces:
                for dirt in dirts:
                    for method in methods:
                        count = coverage['surface_x_dirt_x_method'].get(surface, {}).get(dirt, {}).get(method, 0)
                        if count > 0:
                            writer.writerow([surface, dirt, method, count])


def main():
    """Main entry point for dataset statistics."""
    import sys

    # Determine paths
    root = pathlib.Path(__file__).resolve().parents[2]
    data_path = root / "data" / "processed" / "cleaning_docs.jsonl"
    output_dir = root / "data" / "evaluation"

    # Create statistics calculator
    stats = DatasetStatistics(data_path)

    # Compute all statistics
    print("Loading data...")
    stats.load_data()
    print(f"Loaded {len(stats.documents)} documents")

    print("Computing statistics...")
    stats.compute_all()

    # Save outputs
    print("Saving reports...")
    stats.save_json(output_dir / "dataset_stats.json")
    stats.save_text_report(output_dir / "dataset_stats.txt")
    stats.save_coverage_csv(output_dir / "coverage_matrix.csv")

    print(f"\nStatistics saved to:")
    print(f"  - {output_dir / 'dataset_stats.json'}")
    print(f"  - {output_dir / 'dataset_stats.txt'}")
    print(f"  - {output_dir / 'coverage_matrix.csv'}")


if __name__ == "__main__":
    main()

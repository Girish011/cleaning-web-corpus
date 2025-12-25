"""
Visualization module for Phase 5.4.

Creates matplotlib charts to visualize dataset statistics and ablation study results.
Makes statistics tangible through visual representations.
"""

import json
import pathlib
from typing import Dict, List, Optional, Tuple
from collections import Counter

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")


class DatasetVisualizer:
    """
    Creates visualizations for dataset statistics.
    
    Generates charts for:
    - Text statistics (word count distributions, histograms)
    - Coverage analysis (bar charts, heatmaps)
    - Enrichment statistics (tool/step distributions)
    - Image statistics (if available)
    """

    def __init__(self, stats_json_path: pathlib.Path, output_dir: pathlib.Path):
        """
        Initialize visualizer.
        
        Args:
            stats_json_path: Path to dataset_stats.json
            output_dir: Directory to save visualization files
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib is required for visualizations. Install with: pip install matplotlib")

        self.stats_json_path = stats_json_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = None

    def load_stats(self) -> None:
        """Load statistics from JSON file."""
        if not self.stats_json_path.exists():
            raise FileNotFoundError(f"Stats file not found: {self.stats_json_path}")

        with self.stats_json_path.open(encoding='utf-8') as f:
            self.stats = json.load(f)

    def plot_text_distributions(self) -> pathlib.Path:
        """
        Create histogram and box plot for word count distribution.
        
        Returns:
            Path to saved figure
        """
        if not self.stats:
            self.load_stats()

        text_stats = self.stats.get('text', {})
        word_count = text_stats.get('word_count', {})

        if not word_count:
            print("Warning: No word count data available")
            return None

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Box plot
        percentiles = {
            'Min': word_count.get('min', 0),
            'P25': word_count.get('p25', 0),
            'P50': word_count.get('p50', 0),
            'P75': word_count.get('p75', 0),
            'P95': word_count.get('p95', 0),
            'Max': word_count.get('max', 0),
        }

        values = list(percentiles.values())
        labels = list(percentiles.keys())

        bp = ax1.boxplot([values], labels=['Word Count'], patch_artist=True,
                         showmeans=True, meanline=True)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][0].set_alpha(0.7)

        ax1.set_ylabel('Word Count', fontsize=12)
        ax1.set_title('Word Count Distribution (Percentiles)', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')

        # Add percentile labels
        for i, (label, value) in enumerate(percentiles.items()):
            ax1.text(1, value, f'{label}: {value}', ha='left', va='bottom' if i % 2 == 0 else 'top',
                    fontsize=9, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

        # Bar chart of percentiles
        colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))
        bars = ax2.bar(labels, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Word Count', fontsize=12)
        ax2.set_xlabel('Percentile', fontsize=12)
        ax2.set_title('Word Count Percentiles', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(value)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Add mean line
        mean_val = word_count.get('mean', 0)
        ax2.axhline(y=mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}')
        ax2.legend()

        plt.tight_layout()

        output_path = self.output_dir / 'text_distributions.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved text distributions plot: {output_path}")
        return output_path

    def plot_coverage_distributions(self) -> pathlib.Path:
        """
        Create bar charts for coverage distributions (surface, dirt, method).
        
        Returns:
            Path to saved figure
        """
        if not self.stats:
            self.load_stats()

        coverage = self.stats.get('coverage', {})

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # Surface type distribution
        surface_dist = coverage.get('surface_type_distribution', {})
        if surface_dist:
            surfaces = list(surface_dist.keys())
            counts = list(surface_dist.values())
            colors1 = plt.cm.Set3(np.linspace(0, 1, len(surfaces)))
            axes[0].bar(surfaces, counts, color=colors1, alpha=0.7, edgecolor='black', linewidth=1.5)
            axes[0].set_ylabel('Count', fontsize=12)
            axes[0].set_xlabel('Surface Type', fontsize=12)
            axes[0].set_title('Surface Type Distribution', fontsize=14, fontweight='bold')
            axes[0].tick_params(axis='x', rotation=45, ha='right')
            axes[0].grid(True, alpha=0.3, axis='y')

            # Add value labels
            for i, (surface, count) in enumerate(zip(surfaces, counts)):
                axes[0].text(i, count, str(count), ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Dirt type distribution
        dirt_dist = coverage.get('dirt_type_distribution', {})
        if dirt_dist:
            dirts = list(dirt_dist.keys())
            counts = list(dirt_dist.values())
            colors2 = plt.cm.Set2(np.linspace(0, 1, len(dirts)))
            axes[1].bar(dirts, counts, color=colors2, alpha=0.7, edgecolor='black', linewidth=1.5)
            axes[1].set_ylabel('Count', fontsize=12)
            axes[1].set_xlabel('Dirt Type', fontsize=12)
            axes[1].set_title('Dirt Type Distribution', fontsize=14, fontweight='bold')
            axes[1].tick_params(axis='x', rotation=45, ha='right')
            axes[1].grid(True, alpha=0.3, axis='y')

            # Add value labels
            for i, (dirt, count) in enumerate(zip(dirts, counts)):
                axes[1].text(i, count, str(count), ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Cleaning method distribution
        method_dist = coverage.get('cleaning_method_distribution', {})
        if method_dist:
            methods = list(method_dist.keys())
            counts = list(method_dist.values())
            colors3 = plt.cm.Pastel1(np.linspace(0, 1, len(methods)))
            axes[2].bar(methods, counts, color=colors3, alpha=0.7, edgecolor='black', linewidth=1.5)
            axes[2].set_ylabel('Count', fontsize=12)
            axes[2].set_xlabel('Cleaning Method', fontsize=12)
            axes[2].set_title('Cleaning Method Distribution', fontsize=14, fontweight='bold')
            axes[2].tick_params(axis='x', rotation=45, ha='right')
            axes[2].grid(True, alpha=0.3, axis='y')

            # Add value labels
            for i, (method, count) in enumerate(zip(methods, counts)):
                axes[2].text(i, count, str(count), ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()

        output_path = self.output_dir / 'coverage_distributions.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved coverage distributions plot: {output_path}")
        return output_path

    def plot_coverage_heatmap(self) -> pathlib.Path:
        """
        Create heatmap for surface × dirt × method coverage matrix.
        
        Returns:
            Path to saved figure
        """
        if not self.stats:
            self.load_stats()

        coverage = self.stats.get('coverage', {})
        matrix_3d = coverage.get('surface_x_dirt_x_method', {})

        if not matrix_3d:
            print("Warning: No 3D coverage matrix available")
            return None

        # Flatten 3D matrix to 2D for visualization
        # We'll create a heatmap for surface × dirt (aggregating over methods)
        surface_dirt = coverage.get('surface_x_dirt', {})

        if not surface_dirt:
            print("Warning: No surface × dirt matrix available")
            return None

        surfaces = sorted(coverage.get('surface_type_distribution', {}).keys())
        dirts = sorted(coverage.get('dirt_type_distribution', {}).keys())

        # Build 2D matrix
        matrix_2d = []
        for surface in surfaces:
            row = []
            for dirt in dirts:
                count = surface_dirt.get(surface, {}).get(dirt, 0)
                row.append(count)
            matrix_2d.append(row)

        matrix_2d = np.array(matrix_2d)

        fig, ax = plt.subplots(figsize=(10, 8))

        # Create heatmap
        im = ax.imshow(matrix_2d, cmap='YlOrRd', aspect='auto', interpolation='nearest')

        # Set ticks and labels
        ax.set_xticks(np.arange(len(dirts)))
        ax.set_yticks(np.arange(len(surfaces)))
        ax.set_xticklabels(dirts, rotation=45, ha='right')
        ax.set_yticklabels(surfaces)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Document Count', fontsize=12)

        # Add text annotations
        for i in range(len(surfaces)):
            for j in range(len(dirts)):
                text = ax.text(j, i, matrix_2d[i, j],
                             ha="center", va="center", color="black", fontsize=12, fontweight='bold')

        ax.set_xlabel('Dirt Type', fontsize=12, fontweight='bold')
        ax.set_ylabel('Surface Type', fontsize=12, fontweight='bold')
        ax.set_title('Coverage Matrix: Surface Type × Dirt Type', fontsize=14, fontweight='bold')

        plt.tight_layout()

        output_path = self.output_dir / 'coverage_heatmap.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved coverage heatmap: {output_path}")
        return output_path

    def plot_enrichment_stats(self) -> pathlib.Path:
        """
        Create charts for enrichment statistics (tools, steps).
        
        Returns:
            Path to saved figure
        """
        if not self.stats:
            self.load_stats()

        enrichment = self.stats.get('enrichment', {})
        tools = enrichment.get('tools', {})
        steps = enrichment.get('steps', {})

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Tools chart
        if tools:
            most_common = tools.get('most_common_tools', {})
            if most_common:
                tool_names = list(most_common.keys())[:10]  # Top 10
                tool_counts = list(most_common.values())[:10]

                colors = plt.cm.coolwarm(np.linspace(0, 1, len(tool_names)))
                bars = axes[0].barh(tool_names, tool_counts, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
                axes[0].set_xlabel('Frequency', fontsize=12)
                axes[0].set_ylabel('Tool', fontsize=12)
                axes[0].set_title('Most Common Tools (Top 10)', fontsize=14, fontweight='bold')
                axes[0].grid(True, alpha=0.3, axis='x')

                # Add value labels
                for i, (tool, count) in enumerate(zip(tool_names, tool_counts)):
                    axes[0].text(count, i, f' {count}', va='center', fontsize=10, fontweight='bold')

        # Steps statistics
        if steps:
            docs_with = steps.get('documents_with_steps', 0)
            docs_without = steps.get('documents_without_steps', 0)
            total_steps = steps.get('total_steps_extracted', 0)
            avg_steps = steps.get('avg_steps_per_doc', 0)

            # Pie chart for documents with/without steps
            if docs_with + docs_without > 0:
                sizes = [docs_with, docs_without]
                labels = ['With Steps', 'Without Steps']
                colors = ['#66b3ff', '#ff9999']
                explode = (0.05, 0)

                axes[1].pie(sizes, explode=explode, labels=labels, colors=colors,
                          autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 11})
                axes[1].set_title('Documents with Steps Extraction', fontsize=14, fontweight='bold')

                # Add text box with statistics
                stats_text = f'Total Steps: {total_steps}\nAvg Steps/Doc: {avg_steps:.1f}'
                axes[1].text(1.3, 0, stats_text, fontsize=10, verticalalignment='center',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        output_path = self.output_dir / 'enrichment_stats.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved enrichment stats plot: {output_path}")
        return output_path

    def plot_basic_stats(self) -> pathlib.Path:
        """
        Create overview chart for basic statistics.
        
        Returns:
            Path to saved figure
        """
        if not self.stats:
            self.load_stats()

        basic = self.stats.get('basic', {})
        metadata = self.stats.get('metadata', {})

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Total documents
        total_docs = basic.get('total_documents', 0)
        axes[0, 0].text(0.5, 0.5, f'{total_docs}', ha='center', va='center',
                        fontsize=48, fontweight='bold', color='#2E86AB')
        axes[0, 0].set_title('Total Documents', fontsize=16, fontweight='bold', pad=20)
        axes[0, 0].axis('off')

        # Source type distribution
        source_dist = basic.get('source_type_distribution', {})
        if source_dist:
            sources = list(source_dist.keys())
            counts = list(source_dist.values())
            colors = plt.cm.Pastel2(np.linspace(0, 1, len(sources)))
            axes[0, 1].pie(counts, labels=sources, colors=colors, autopct='%1.1f%%',
                          startangle=90, textprops={'fontsize': 10})
            axes[0, 1].set_title('Source Type Distribution', fontsize=14, fontweight='bold')

        # Images statistics
        images = basic.get('images', {})
        if images:
            total_images = images.get('total_images', 0)
            docs_with = images.get('documents_with_images', 0)
            docs_without = images.get('documents_without_images', 0)

            if docs_with + docs_without > 0:
                sizes = [docs_with, docs_without]
                labels = ['With Images', 'Without Images']
                colors = ['#4CAF50', '#F44336']
                axes[1, 0].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                              startangle=90, textprops={'fontsize': 11})
                axes[1, 0].set_title('Documents with Images', fontsize=14, fontweight='bold')

                # Add total images text
                axes[1, 0].text(0, -1.3, f'Total Images: {total_images}', ha='center',
                               fontsize=12, fontweight='bold',
                               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))

        # Language distribution
        lang_dist = basic.get('language_distribution', {})
        if lang_dist:
            langs = list(lang_dist.keys())
            counts = list(lang_dist.values())
            colors = plt.cm.Set1(np.linspace(0, 1, len(langs)))
            bars = axes[1, 1].bar(langs, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
            axes[1, 1].set_ylabel('Count', fontsize=12)
            axes[1, 1].set_xlabel('Language', fontsize=12)
            axes[1, 1].set_title('Language Distribution', fontsize=14, fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3, axis='y')

            # Add value labels
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                               str(count), ha='center', va='bottom', fontsize=11, fontweight='bold')

        # Add title
        fig.suptitle('Dataset Overview Statistics', fontsize=18, fontweight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        output_path = self.output_dir / 'basic_stats.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved basic stats plot: {output_path}")
        return output_path

    def generate_all(self) -> List[pathlib.Path]:
        """
        Generate all visualizations.
        
        Returns:
            List of paths to saved figures
        """
        if not self.stats:
            self.load_stats()

        outputs = []

        print("Generating visualizations...")

        try:
            outputs.append(self.plot_basic_stats())
        except Exception as e:
            print(f"Error generating basic stats: {e}")

        try:
            outputs.append(self.plot_text_distributions())
        except Exception as e:
            print(f"Error generating text distributions: {e}")

        try:
            outputs.append(self.plot_coverage_distributions())
        except Exception as e:
            print(f"Error generating coverage distributions: {e}")

        try:
            outputs.append(self.plot_coverage_heatmap())
        except Exception as e:
            print(f"Error generating coverage heatmap: {e}")

        try:
            outputs.append(self.plot_enrichment_stats())
        except Exception as e:
            print(f"Error generating enrichment stats: {e}")

        # Filter out None values
        outputs = [o for o in outputs if o is not None]

        print(f"\nGenerated {len(outputs)} visualization(s)")
        return outputs


class AblationVisualizer:
    """
    Creates visualizations for ablation study results.
    
    Generates charts for:
    - Filter retention rates (bar charts)
    - Filter overlap (heatmap)
    - Cumulative filter impact
    """

    def __init__(self, ablation_json_path: pathlib.Path, output_dir: pathlib.Path):
        """
        Initialize ablation visualizer.
        
        Args:
            ablation_json_path: Path to ablation_study.json
            output_dir: Directory to save visualization files
        """
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib is required for visualizations. Install with: pip install matplotlib")

        self.ablation_json_path = ablation_json_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data = None

    def load_data(self) -> None:
        """Load ablation study results from JSON file."""
        if not self.ablation_json_path.exists():
            raise FileNotFoundError(f"Ablation file not found: {self.ablation_json_path}")

        with self.ablation_json_path.open(encoding='utf-8') as f:
            self.data = json.load(f)

    def plot_retention_rates(self) -> pathlib.Path:
        """
        Create bar chart showing retention rates for each filter.
        
        Returns:
            Path to saved figure
        """
        if not self.data:
            self.load_data()

        results = self.data.get('results', [])

        if not results:
            print("Warning: No ablation results available")
            return None

        # Filter out baseline and all_filters for individual filter view
        individual_filters = [r for r in results if r['filter_combination'] not in ['baseline', 'all_filters']]

        # Also include baseline and all_filters for comparison
        filter_names = [r['filter_combination'] for r in results]
        retention_rates = [r['retention_rate'] * 100 for r in results]  # Convert to percentage
        rejection_rates = [r['rejection_rate'] * 100 for r in results]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Retention rates bar chart
        colors = plt.cm.viridis(np.linspace(0, 1, len(filter_names)))
        bars1 = ax1.barh(filter_names, retention_rates, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax1.set_xlabel('Retention Rate (%)', fontsize=12)
        ax1.set_ylabel('Filter Combination', fontsize=12)
        ax1.set_title('Filter Retention Rates', fontsize=14, fontweight='bold')
        ax1.set_xlim(0, 105)
        ax1.grid(True, alpha=0.3, axis='x')

        # Add value labels
        for i, (name, rate) in enumerate(zip(filter_names, retention_rates)):
            ax1.text(rate, i, f' {rate:.1f}%', va='center', fontsize=9, fontweight='bold')

        # Rejection rates bar chart
        bars2 = ax2.barh(filter_names, rejection_rates, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax2.set_xlabel('Rejection Rate (%)', fontsize=12)
        ax2.set_ylabel('Filter Combination', fontsize=12)
        ax2.set_title('Filter Rejection Rates', fontsize=14, fontweight='bold')
        ax2.set_xlim(0, 105)
        ax2.grid(True, alpha=0.3, axis='x')

        # Add value labels
        for i, (name, rate) in enumerate(zip(filter_names, rejection_rates)):
            ax2.text(rate, i, f' {rate:.1f}%', va='center', fontsize=9, fontweight='bold')

        plt.tight_layout()

        output_path = self.output_dir / 'ablation_retention_rates.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved retention rates plot: {output_path}")
        return output_path

    def plot_filter_overlap(self) -> pathlib.Path:
        """
        Create heatmap showing filter overlap (Jaccard similarity).
        
        Returns:
            Path to saved figure
        """
        if not self.data:
            self.load_data()

        overlap = self.data.get('filter_overlap', {})

        if not overlap:
            print("Warning: No filter overlap data available")
            return None

        # Extract filter pairs and Jaccard similarities
        filter_pairs = []
        jaccard_values = []

        for pair_key, metrics in overlap.items():
            filter_pairs.append(pair_key)
            jaccard_values.append(metrics.get('jaccard_similarity', 0.0))

        if not filter_pairs:
            print("Warning: No filter pairs found")
            return None

        # Create a matrix (simplified - showing pairs as a bar chart instead)
        fig, ax = plt.subplots(figsize=(12, max(6, len(filter_pairs) * 0.5)))

        # Sort by Jaccard similarity
        sorted_data = sorted(zip(filter_pairs, jaccard_values), key=lambda x: x[1], reverse=True)
        filter_pairs, jaccard_values = zip(*sorted_data)

        # Create color map based on Jaccard values
        colors = plt.cm.RdYlGn(np.array(jaccard_values))

        bars = ax.barh(filter_pairs, jaccard_values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax.set_xlabel('Jaccard Similarity', fontsize=12)
        ax.set_ylabel('Filter Pair', fontsize=12)
        ax.set_title('Filter Overlap Analysis (Jaccard Similarity)', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 1.1)
        ax.grid(True, alpha=0.3, axis='x')

        # Add value labels
        for i, (pair, jaccard) in enumerate(zip(filter_pairs, jaccard_values)):
            ax.text(jaccard, i, f' {jaccard:.3f}', va='center', fontsize=9, fontweight='bold')

        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label('Jaccard Similarity', fontsize=11)

        plt.tight_layout()

        output_path = self.output_dir / 'ablation_filter_overlap.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved filter overlap plot: {output_path}")
        return output_path

    def plot_documents_passed_failed(self) -> pathlib.Path:
        """
        Create stacked bar chart showing documents passed vs failed for each filter.
        
        Returns:
            Path to saved figure
        """
        if not self.data:
            self.load_data()

        results = self.data.get('results', [])
        metadata = self.data.get('metadata', {})
        baseline_count = metadata.get('baseline_documents', 0)

        if not results:
            print("Warning: No ablation results available")
            return None

        filter_names = [r['filter_combination'] for r in results]
        passed = [r['documents_passed'] for r in results]
        failed = [r['documents_failed'] for r in results]

        fig, ax = plt.subplots(figsize=(14, 8))

        x = np.arange(len(filter_names))
        width = 0.6

        bars1 = ax.bar(x, passed, width, label='Passed', color='#4CAF50', alpha=0.8, edgecolor='black', linewidth=1.5)
        bars2 = ax.bar(x, failed, width, bottom=passed, label='Failed',
                       color='#F44336', alpha=0.8, edgecolor='black', linewidth=1.5)

        ax.set_ylabel('Number of Documents', fontsize=12)
        ax.set_xlabel('Filter Combination', fontsize=12)
        ax.set_title('Documents Passed vs Failed by Filter', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(filter_names, rotation=45, ha='right')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for i, (p, f) in enumerate(zip(passed, failed)):
            if p > 0:
                ax.text(i, p/2, str(p), ha='center', va='center', fontsize=9, fontweight='bold', color='white')
            if f > 0:
                ax.text(i, p + f/2, str(f), ha='center', va='center', fontsize=9, fontweight='bold', color='white')

        # Add baseline line
        if baseline_count > 0:
            ax.axhline(y=baseline_count, color='blue', linestyle='--',
                       linewidth=2, alpha=0.5, label=f'Baseline: {baseline_count}')
            ax.legend(fontsize=11)

        plt.tight_layout()

        output_path = self.output_dir / 'ablation_documents_passed_failed.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Saved documents passed/failed plot: {output_path}")
        return output_path

    def generate_all(self) -> List[pathlib.Path]:
        """
        Generate all ablation visualizations.
        
        Returns:
            List of paths to saved figures
        """
        if not self.data:
            self.load_data()

        outputs = []

        print("Generating ablation visualizations...")

        try:
            outputs.append(self.plot_retention_rates())
        except Exception as e:
            print(f"Error generating retention rates: {e}")

        try:
            outputs.append(self.plot_filter_overlap())
        except Exception as e:
            print(f"Error generating filter overlap: {e}")

        try:
            outputs.append(self.plot_documents_passed_failed())
        except Exception as e:
            print(f"Error generating documents passed/failed: {e}")

        # Filter out None values
        outputs = [o for o in outputs if o is not None]

        print(f"\nGenerated {len(outputs)} ablation visualization(s)")
        return outputs


def main():
    """Main entry point for generating all visualizations."""
    root = pathlib.Path(__file__).resolve().parents[2]
    evaluation_dir = root / "data" / "evaluation"
    output_dir = evaluation_dir / "visualizations"

    print("=" * 80)
    print("PHASE 5.4: DATASET VISUALIZATIONS")
    print("=" * 80)
    print()

    # Dataset statistics visualizations
    stats_json = evaluation_dir / "dataset_stats.json"
    if stats_json.exists():
        print("Generating dataset statistics visualizations...")
        try:
            visualizer = DatasetVisualizer(stats_json, output_dir)
            visualizer.generate_all()
        except Exception as e:
            print(f"Error generating dataset visualizations: {e}")
    else:
        print(f"Warning: Dataset stats file not found: {stats_json}")
        print("Run: python -m src.evaluation.dataset_stats")

    print()

    # Ablation study visualizations
    ablation_json = evaluation_dir / "ablation_study.json"
    if ablation_json.exists():
        print("Generating ablation study visualizations...")
        try:
            ablation_viz = AblationVisualizer(ablation_json, output_dir)
            ablation_viz.generate_all()
        except Exception as e:
            print(f"Error generating ablation visualizations: {e}")
    else:
        print(f"Warning: Ablation study file not found: {ablation_json}")
        print("Run: python -m src.evaluation.ablation_study")

    print()
    print("=" * 80)
    print(f"Visualizations saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()

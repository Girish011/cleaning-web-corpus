"""
Unified pipeline orchestrator.

This module provides a single entry point to run the complete pipeline
from discovery to evaluation.
"""

import logging
import pathlib
import subprocess
import sys
from typing import Optional

from src.config import get_config, reload_config
from src.crawlers.search_discovery import SearchEngineDiscovery
from src.processors.text_processor import main as process_main
from src.evaluation.dataset_stats import DatasetStatistics

# Try to import visualizations (optional dependency)
try:
    from src.evaluation.visualizations import DatasetVisualizer
    HAS_VISUALIZATIONS = True
except ImportError:
    HAS_VISUALIZATIONS = False
    DatasetVisualizer = None

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Unified orchestrator for the complete cleaning corpus pipeline.
    
    Orchestrates the following stages:
    1. Discovery (optional) - Search engine URL discovery
    2. Crawl - Scrapy spider to crawl discovered/manual seed URLs
    3. Process - Text extraction and quality filtering
    4. Enrich - Structured extraction and image captioning (done in process step)
    5. Evaluate - Dataset statistics and analysis
    """

    def __init__(self, config_path: Optional[pathlib.Path] = None):
        """
        Initialize the pipeline orchestrator.
        
        Args:
            config_path: Optional path to config file. If None, uses default.
        """
        # Reload config to ensure we have the latest version
        # This is important because text_processor uses module-level config
        if config_path:
            self.config = reload_config(config_path)
        else:
            # Even for default, reload to ensure fresh config
            self.config = reload_config(None)
        self.root = pathlib.Path(__file__).resolve().parents[2]  # Project root

        # Setup logging
        log_level = getattr(logging, self.config.logging.level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format=self.config.logging.format,
        )

        # Paths
        self.seeds_file = self.root / self.config.crawler.seeds_file
        self.discovered_seeds_file = self.root / "data" / "seeds_discovered.txt"
        self.raw_output = self.root / "data" / "raw" / "seed_pages.jsonl"
        self.processed_output = self.root / "data" / "processed" / "cleaning_docs.jsonl"
        self.evaluation_output_dir = self.root / "data" / "evaluation"

        logger.info(f"Pipeline orchestrator initialized")
        logger.info(f"  Project root: {self.root}")
        logger.info(f"  Seeds file: {self.seeds_file}")
        logger.info(f"  Raw output: {self.raw_output}")
        logger.info(f"  Processed output: {self.processed_output}")

    def discover(self) -> bool:
        """
        Stage 1: Discover URLs using search engines (optional).
        
        Returns:
            True if discovery was successful or skipped, False on error
        """
        discovery_config = self.config.crawler.search_discovery

        if not discovery_config.enable:
            logger.info("Search discovery is disabled in config. Skipping discovery stage.")
            return True

        logger.info("=" * 80)
        logger.info("STAGE 1: URL DISCOVERY")
        logger.info("=" * 80)

        try:
            # Initialize discovery
            discovery = SearchEngineDiscovery(
                provider=discovery_config.provider,
                api_key=discovery_config.api_key,
                search_engine_id=discovery_config.search_engine_id,
                max_results_per_query=discovery_config.max_results_per_query,
                delay_seconds=discovery_config.delay_seconds,
                allowed_domains=self.config.allowed_domains if self.config.allowed_domains else None,
            )

            # Discover URLs
            logger.info(f"Starting URL discovery with provider: {discovery_config.provider}")
            logger.info(f"  Max URLs: {discovery_config.max_urls or 'unlimited'}")
            logger.info(f"  Allowed domains: {self.config.allowed_domains or 'all'}")

            urls = discovery.discover_urls(max_urls=discovery_config.max_urls)

            # Save discovered URLs
            self.discovered_seeds_file.parent.mkdir(parents=True, exist_ok=True)
            discovery.save_urls(self.discovered_seeds_file)

            # Save query history
            history_path = self.evaluation_output_dir / "discovery_history.json"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            discovery.save_query_history(history_path)

            logger.info(f"✓ Discovery complete!")
            logger.info(f"  Found: {len(urls)} unique URLs")
            logger.info(f"  Saved to: {self.discovered_seeds_file}")

            # Merge with existing seeds if auto_discover is enabled
            if discovery_config.auto_discover and self.discovered_seeds_file.exists():
                logger.info("Merging discovered URLs with existing seeds...")
                self._merge_seeds()

            return True

        except Exception as e:
            logger.error(f"Discovery failed: {e}", exc_info=True)
            return False

    def _filter_blacklisted_seeds(self) -> None:
        """Filter out URLs from blacklisted domains from seeds file."""
        if not self.seeds_file.exists() or not self.config.crawler.timeout_blacklist:
            return

        # Read all seeds
        all_urls = []
        filtered_urls = []
        blacklisted_domains = set(self.config.crawler.timeout_blacklist)

        with self.seeds_file.open() as f:
            for line in f:
                url = line.strip()
                if not url or url.startswith("#"):
                    continue

                # Check if URL domain is blacklisted
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.lower()

                is_blacklisted = any(blacklisted in domain for blacklisted in blacklisted_domains)

                if is_blacklisted:
                    filtered_urls.append(url)
                    logger.debug(f"Skipping blacklisted URL: {url}")
                else:
                    all_urls.append(url)

        if filtered_urls:
            logger.info(f"  Filtered out {len(filtered_urls)} URLs from blacklisted domains")
            # Write back filtered seeds
            with self.seeds_file.open("w") as f:
                for url in all_urls:
                    f.write(f"{url}\n")

    def _merge_seeds(self) -> None:
        """Merge discovered URLs with existing seeds file."""
        if not self.discovered_seeds_file.exists():
            return

        # Read existing seeds
        existing_urls = set()
        if self.seeds_file.exists():
            with self.seeds_file.open() as f:
                existing_urls = {line.strip() for line in f if line.strip()}

        # Read discovered URLs
        discovered_urls = set()
        with self.discovered_seeds_file.open() as f:
            discovered_urls = {line.strip() for line in f if line.strip()}

        # Merge (union)
        all_urls = existing_urls | discovered_urls

        # Write merged seeds
        self.seeds_file.parent.mkdir(parents=True, exist_ok=True)
        with self.seeds_file.open("w") as f:
            for url in sorted(all_urls):
                f.write(f"{url}\n")

        new_count = len(all_urls) - len(existing_urls)
        logger.info(f"  Merged {new_count} new URLs into seeds file")
        logger.info(f"  Total URLs in seeds: {len(all_urls)}")

    def crawl(self) -> bool:
        """
        Stage 2: Crawl URLs using Scrapy spider.
        
        Returns:
            True if crawl was successful, False on error
        """
        logger.info("=" * 80)
        logger.info("STAGE 2: CRAWLING")
        logger.info("=" * 80)

        # Check if seeds file exists
        if not self.seeds_file.exists():
            logger.error(f"Seeds file not found: {self.seeds_file}")
            logger.error("Please create seeds file or enable discovery stage.")
            return False

        # Count URLs in seeds file
        with self.seeds_file.open() as f:
            url_count = sum(1 for line in f if line.strip())

        logger.info(f"Found {url_count} URLs in seeds file: {self.seeds_file}")

        # Ensure output directory exists
        self.raw_output.parent.mkdir(parents=True, exist_ok=True)

        # Run Scrapy crawl
        logger.info("Starting Scrapy crawl...")
        logger.info(f"  Output: {self.raw_output}")

        try:
            # Filter out blacklisted domains from seeds
            if self.config.crawler.timeout_blacklist:
                logger.info(f"Filtering blacklisted domains: {', '.join(self.config.crawler.timeout_blacklist)}")
                self._filter_blacklisted_seeds()

            # Build scrapy command
            cmd = [
                sys.executable, "-m", "scrapy", "crawl", "seed_spider",
                "-O", str(self.raw_output),
                "-s", f"DOWNLOAD_TIMEOUT={self.config.crawler.download_timeout}",
                "-s", f"RETRY_TIMES={self.config.crawler.timeout_retry_times}",
            ]

            # Add settings if needed
            if self.config.crawler.download_images:
                logger.info("  Image downloading: enabled")
            else:
                logger.info("  Image downloading: disabled")

            logger.info(f"  Download timeout: {self.config.crawler.download_timeout}s (polite timeout policy)")
            logger.info(f"  Retry times: {self.config.crawler.timeout_retry_times}")

            # Run command with real-time output streaming
            logger.info("")
            logger.info("Scrapy crawl output (real-time):")
            logger.info("-" * 80)

            # Use Popen to stream output in real-time
            process = subprocess.Popen(
                cmd,
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                bufsize=0,  # Unbuffered for immediate output
            )

            # Stream output in real-time
            output_lines = []
            try:
                # Read line by line and print immediately
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    line = line.rstrip()
                    if line:  # Only print non-empty lines
                        print(line, flush=True)  # Print to console immediately
                        output_lines.append(line)
            except Exception as e:
                logger.warning(f"Error reading output: {e}")

            # Wait for process to complete
            return_code = process.wait()

            logger.info("-" * 80)

            if return_code != 0:
                logger.error(f"Crawl failed with return code {return_code}")
                # Log last few lines for debugging
                if output_lines:
                    logger.error("Last output lines:")
                    for line in output_lines[-10:]:
                        logger.error(f"  {line}")
                return False

            # Check if output file was created
            if not self.raw_output.exists():
                logger.error(f"Output file not created: {self.raw_output}")
                return False

            # Count crawled items
            item_count = 0
            with self.raw_output.open() as f:
                item_count = sum(1 for line in f if line.strip())

            logger.info(f"✓ Crawl complete!")
            logger.info(f"  Crawled {item_count} pages")
            logger.info(f"  Output: {self.raw_output}")

            return True

        except Exception as e:
            logger.error(f"Crawl failed: {e}", exc_info=True)
            return False

    def process(self) -> bool:
        """
        Stage 3: Process crawled data (text extraction, quality filtering, enrichment).
        
        This stage:
        - Extracts main text from HTML
        - Applies text quality filters
        - Applies image quality filters
        - Applies CLIP alignment scoring
        - Enriches with structured extraction (tools, steps)
        - Applies image captioning
        
        Note: This stage uses the config that was loaded when text_processor
        module was imported. If a custom config was provided to the orchestrator,
        ensure that text_processor will use the same config (typically the default).
        
        Returns:
            True if processing was successful, False on error
        """
        logger.info("=" * 80)
        logger.info("STAGE 3: PROCESSING & ENRICHMENT")
        logger.info("=" * 80)

        # Check if raw input exists
        if not self.raw_output.exists():
            logger.error(f"Raw input file not found: {self.raw_output}")
            logger.error("Please run crawl stage first.")
            return False

        logger.info(f"Processing raw data from: {self.raw_output}")
        logger.info(f"  Output: {self.processed_output}")

        try:
            # Ensure output directory exists
            self.processed_output.parent.mkdir(parents=True, exist_ok=True)

            # Run text processor (this handles processing + enrichment)
            # Note: text_processor.main() uses global config, so we need to ensure
            # config is loaded before calling it
            process_main()

            # Check if output was created
            if not self.processed_output.exists():
                logger.error(f"Processed output file not created: {self.processed_output}")
                return False

            # Count processed items
            item_count = 0
            with self.processed_output.open() as f:
                item_count = sum(1 for line in f if line.strip())

            logger.info(f"✓ Processing complete!")
            logger.info(f"  Processed {item_count} documents")
            logger.info(f"  Output: {self.processed_output}")

            return True

        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            return False

    def evaluate(self) -> bool:
        """
        Stage 4: Evaluate processed dataset (statistics and analysis).
        
        This stage:
        - Computes comprehensive dataset statistics
        - Generates visualizations
        - Saves statistics to JSON and text files
        
        Returns:
            True if evaluation was successful, False on error
        """
        logger.info("=" * 80)
        logger.info("STAGE 4: EVALUATION")
        logger.info("=" * 80)

        # Check if processed input exists
        if not self.processed_output.exists():
            logger.error(f"Processed input file not found: {self.processed_output}")
            logger.error("Please run process stage first.")
            return False

        logger.info(f"Evaluating dataset from: {self.processed_output}")

        try:
            # Ensure output directory exists
            self.evaluation_output_dir.mkdir(parents=True, exist_ok=True)

            # Initialize statistics calculator
            stats_calculator = DatasetStatistics(self.processed_output)

            # Compute all statistics
            logger.info("Computing dataset statistics...")
            stats = stats_calculator.compute_all()

            # Save statistics to JSON
            stats_json_path = self.evaluation_output_dir / "dataset_stats.json"
            import json
            with stats_json_path.open("w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            logger.info(f"  Saved JSON: {stats_json_path}")

            # Save statistics to text
            stats_txt_path = self.evaluation_output_dir / "dataset_stats.txt"
            stats_calculator.save_text_report(stats_txt_path)

            logger.info(f"  Saved text: {stats_txt_path}")

            # Generate visualizations (if available)
            if HAS_VISUALIZATIONS and DatasetVisualizer:
                try:
                    logger.info("Generating visualizations...")
                    visualizations_dir = self.evaluation_output_dir / "visualizations"
                    visualizations_dir.mkdir(parents=True, exist_ok=True)

                    visualizer = DatasetVisualizer(stats_json_path, visualizations_dir)
                    generated_files = visualizer.generate_all()

                    if generated_files:
                        logger.info(f"  Generated {len(generated_files)} visualization(s):")
                        for viz_file in generated_files:
                            if viz_file:
                                logger.info(f"    - {viz_file.name}")
                    else:
                        logger.warning("  No visualizations were generated")

                except Exception as e:
                    logger.warning(f"  Visualization generation failed: {e}")
                    logger.warning("  Statistics are still available in JSON and text formats")
            else:
                logger.info("  Visualizations skipped (matplotlib not available)")
                logger.info("  Install with: pip install matplotlib numpy")

            logger.info(f"✓ Evaluation complete!")
            logger.info(f"  Statistics saved to: {self.evaluation_output_dir}")
            if HAS_VISUALIZATIONS:
                logger.info(f"  Visualizations saved to: {self.evaluation_output_dir / 'visualizations'}")

            return True

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return False

    def run(self, stages: Optional[list[str]] = None) -> bool:
        """
        Run the complete pipeline or specified stages.
        
        Args:
            stages: List of stage names to run. If None, runs all stages.
                   Valid stages: "discover", "crawl", "process", "evaluate"
        
        Returns:
            True if all requested stages completed successfully, False otherwise
        """
        if stages is None:
            stages = ["discover", "crawl", "process", "evaluate"]

        logger.info("=" * 80)
        logger.info("PIPELINE ORCHESTRATOR")
        logger.info("=" * 80)
        logger.info(f"Running stages: {', '.join(stages)}")
        logger.info("")

        stage_functions = {
            "discover": self.discover,
            "crawl": self.crawl,
            "process": self.process,
            "evaluate": self.evaluate,
        }

        results = {}
        for stage in stages:
            if stage not in stage_functions:
                logger.error(f"Unknown stage: {stage}")
                logger.error(f"Valid stages: {list(stage_functions.keys())}")
                results[stage] = False
                continue

            func = stage_functions[stage]
            success = func()
            results[stage] = success

            if not success:
                logger.error(f"Stage '{stage}' failed. Stopping pipeline.")
                break

            logger.info("")

        # Summary
        logger.info("=" * 80)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 80)
        for stage, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {stage}")

        all_success = all(results.values())
        if all_success:
            logger.info("")
            logger.info("✓ Pipeline completed successfully!")
        else:
            logger.info("")
            logger.error("✗ Pipeline completed with errors")

        return all_success


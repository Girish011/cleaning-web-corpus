#!/usr/bin/env python3
"""Script to discover URLs using search engines."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.crawlers.search_discovery import SearchEngineDiscovery
from src.config import get_config

def main():
    config = get_config()
    discovery_config = config.crawler.search_discovery
    
    if not discovery_config.enable:
        print("Search discovery is disabled in config.")
        print("Set crawler.search_discovery.enable: true in configs/default.yaml")
        print("\nAlternatively, use command line arguments:")
        print("  python -m src.crawlers.search_discovery --provider google --max-urls 100")
        return
    
    # Initialize discovery
    discovery = SearchEngineDiscovery(
        provider=discovery_config.provider,
        api_key=discovery_config.api_key,
        search_engine_id=discovery_config.search_engine_id,
        max_results_per_query=discovery_config.max_results_per_query,
        delay_seconds=discovery_config.delay_seconds,
        allowed_domains=config.allowed_domains if config.allowed_domains else None,
    )
    
    # Discover URLs
    output_path = ROOT / "data" / "seeds_discovered.txt"
    print(f"Starting URL discovery...")
    print(f"  Provider: {discovery_config.provider}")
    print(f"  Max URLs: {discovery_config.max_urls or 'unlimited'}")
    print(f"  Allowed domains: {config.allowed_domains or 'all'}")
    print()
    
    urls = discovery.discover_urls(max_urls=discovery_config.max_urls)
    
    # Save results
    discovery.save_urls(output_path)
    
    # Save query history
    history_path = ROOT / "data" / "evaluation" / "discovery_history.json"
    discovery.save_query_history(history_path)
    
    print(f"\n✓ Discovery complete!")
    print(f"  Found: {len(urls)} unique URLs")
    print(f"  Saved to: {output_path}")
    print(f"  Query history: {history_path}")
    print(f"\nTo use discovered URLs, merge with existing seeds:")
    print(f"  cat {output_path} >> {ROOT / config.crawler.seeds_file}")

if __name__ == "__main__":
    main()

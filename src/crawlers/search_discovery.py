"""
Search engine integration for automatic URL discovery.

This module provides search engine APIs to automatically discover
cleaning-related URLs instead of relying solely on manual seed lists.

Supports:
- Google Custom Search API
- Bing Search API
- SerpAPI (aggregator)
"""

import json
import logging
import os
import pathlib
import time
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class SearchEngineDiscovery:
    """
    Search engine integration for discovering cleaning-related URLs.
    
    Automatically generates search queries and extracts URLs from results.
    """

    def __init__(
        self,
        provider: str = "google",
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,  # For Google Custom Search
        max_results_per_query: int = 100,
        delay_seconds: float = 1.0,
        allowed_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ):
        """
        Initialize search engine discovery.
        
        Args:
            provider: Search provider ("google", "bing", "serpapi")
            api_key: API key (if None, tries environment variables)
            search_engine_id: Google Custom Search Engine ID (for Google provider)
            max_results_per_query: Maximum results to fetch per query
            delay_seconds: Delay between API calls (rate limiting)
            allowed_domains: Only include URLs from these domains (None = all)
            exclude_domains: Exclude URLs from these domains
        """
        self.provider = provider.lower()
        self.max_results_per_query = max_results_per_query
        self.delay_seconds = delay_seconds
        self.allowed_domains = set(allowed_domains) if allowed_domains else None
        self.exclude_domains = set(exclude_domains) if exclude_domains else set()

        # Get API credentials
        if provider == "google":
            self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
            self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
            if not self.api_key or not self.search_engine_id:
                raise ValueError(
                    "Google Custom Search requires GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID. "
                    "Set via parameters or environment variables."
                )
            self.base_url = "https://www.googleapis.com/customsearch/v1"
        elif provider == "bing":
            self.api_key = api_key or os.getenv("BING_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Bing Search requires BING_API_KEY. Set via parameter or environment variable."
                )
            self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        elif provider == "serpapi":
            self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "SerpAPI requires SERPAPI_API_KEY. Set via parameter or environment variable."
                )
            self.base_url = "https://serpapi.com/search"
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'google', 'bing', or 'serpapi'")

        self.discovered_urls: Set[str] = set()
        self.query_history: List[Dict] = []

    def generate_cleaning_queries(self) -> List[str]:
        """
        Generate search queries for cleaning-related content.
        
        Returns:
            List of search query strings
        """
        queries = []

        # Surface types
        surfaces = [
            "pillows", "bedding", "carpets", "floors", "clothes", "fabric",
            "sofa", "upholstery", "curtains", "blankets", "mattress",
            "rugs", "tiles", "wood floors", "leather", "suede"
        ]

        # Dirt types
        dirt_types = [
            "stain", "dust", "odor", "mold", "mildew", "pet hair",
            "grease", "ink", "wine", "coffee", "blood", "sweat"
        ]

        # Cleaning methods
        methods = [
            "how to clean", "how to remove", "cleaning guide", "cleaning tips",
            "stain removal", "deep clean", "maintenance"
        ]

        # Generate combinations
        for surface in surfaces:
            # Surface + dirt
            for dirt in dirt_types:
                queries.append(f"how to remove {dirt} from {surface}")
                queries.append(f"{surface} {dirt} removal")

            # Surface + method
            for method in methods[:3]:  # Limit combinations
                queries.append(f"{method} {surface}")

        # General cleaning queries
        general_queries = [
            "household cleaning tips",
            "cleaning hacks",
            "stain removal guide",
            "deep cleaning methods",
            "fabric care guide",
            "carpet cleaning techniques",
            "upholstery cleaning",
            "laundry tips",
            "home maintenance cleaning",
        ]
        queries.extend(general_queries)

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)

        return unique_queries

    def _search_google(self, query: str, start: int = 1) -> Dict:
        """Search using Google Custom Search API."""
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(10, self.max_results_per_query - start + 1),  # Google max is 10 per request
            "start": start,
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Google search error for query '{query}': {e}")
            return {}

    def _search_bing(self, query: str, count: int = 50) -> Dict:
        """Search using Bing Search API."""
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        params = {
            "q": query,
            "count": min(count, self.max_results_per_query),
            "offset": 0,
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Bing search error for query '{query}': {e}")
            return {}

    def _search_serpapi(self, query: str) -> Dict:
        """Search using SerpAPI."""
        params = {
            "api_key": self.api_key,
            "q": query,
            "num": min(100, self.max_results_per_query),
            "engine": "google",
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"SerpAPI search error for query '{query}': {e}")
            return {}

    def _extract_urls_from_google(self, results: Dict) -> List[str]:
        """Extract URLs from Google Custom Search results."""
        urls = []
        items = results.get("items", [])
        for item in items:
            url = item.get("link", "")
            if url:
                urls.append(url)
        return urls

    def _extract_urls_from_bing(self, results: Dict) -> List[str]:
        """Extract URLs from Bing Search results."""
        urls = []
        web_pages = results.get("webPages", {}).get("value", [])
        for page in web_pages:
            url = page.get("url", "")
            if url:
                urls.append(url)
        return urls

    def _extract_urls_from_serpapi(self, results: Dict) -> List[str]:
        """Extract URLs from SerpAPI results."""
        urls = []
        organic_results = results.get("organic_results", [])
        for result in organic_results:
            url = result.get("link", "")
            if url:
                urls.append(url)
        return urls

    def _filter_url(self, url: str) -> bool:
        """
        Filter URL based on allowed/excluded domains.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL should be included, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix for comparison
            if domain.startswith("www."):
                domain = domain[4:]

            # Check excluded domains
            for excluded in self.exclude_domains:
                excluded_clean = excluded.lower().replace("www.", "")
                if domain == excluded_clean or domain.endswith(f".{excluded_clean}"):
                    return False

            # Check allowed domains
            if self.allowed_domains:
                for allowed in self.allowed_domains:
                    allowed_clean = allowed.lower().replace("www.", "")
                    if domain == allowed_clean or domain.endswith(f".{allowed_clean}"):
                        return True
                return False  # Not in allowed list

            return True  # No restrictions
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return False

    def search(self, query: str) -> List[str]:
        """
        Search for a query and return discovered URLs.
        
        Args:
            query: Search query string
            
        Returns:
            List of discovered URLs
        """
        logger.info(f"Searching for: {query}")

        urls = []

        try:
            if self.provider == "google":
                # Google Custom Search returns max 10 per request, need pagination
                total_fetched = 0
                start = 1

                while total_fetched < self.max_results_per_query:
                    results = self._search_google(query, start=start)
                    batch_urls = self._extract_urls_from_google(results)

                    if not batch_urls:
                        break

                    # Filter URLs
                    for url in batch_urls:
                        if self._filter_url(url):
                            urls.append(url)

                    total_fetched += len(batch_urls)

                    # Check if there are more results
                    search_info = results.get("searchInformation", {})
                    total_results = int(search_info.get("totalResults", 0))

                    if start + len(batch_urls) > total_results or len(batch_urls) < 10:
                        break

                    start += 10
                    time.sleep(self.delay_seconds)  # Rate limiting

            elif self.provider == "bing":
                results = self._search_bing(query)
                batch_urls = self._extract_urls_from_bing(results)

                # Filter URLs
                for url in batch_urls:
                    if self._filter_url(url):
                        urls.append(url)

            elif self.provider == "serpapi":
                results = self._search_serpapi(query)
                batch_urls = self._extract_urls_from_serpapi(results)

                # Filter URLs
                for url in batch_urls:
                    if self._filter_url(url):
                        urls.append(url)

            # Rate limiting
            time.sleep(self.delay_seconds)

            # Track query
            self.query_history.append({
                "query": query,
                "urls_found": len(urls),
                "timestamp": time.time(),
            })

            logger.info(f"Found {len(urls)} URLs for query: {query}")

        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")

        return urls

    def discover_urls(self, queries: Optional[List[str]] = None, max_urls: Optional[int] = None) -> Set[str]:
        """
        Discover URLs from multiple search queries.
        
        Args:
            queries: List of search queries (if None, generates automatically)
            max_urls: Maximum total URLs to discover (None = no limit)
            
        Returns:
            Set of discovered URLs
        """
        if queries is None:
            queries = self.generate_cleaning_queries()

        logger.info(f"Starting URL discovery with {len(queries)} queries")

        for query in queries:
            if max_urls and len(self.discovered_urls) >= max_urls:
                logger.info(f"Reached max URLs limit ({max_urls})")
                break

            urls = self.search(query)

            for url in urls:
                self.discovered_urls.add(url)

                if max_urls and len(self.discovered_urls) >= max_urls:
                    break

        logger.info(f"Discovery complete: {len(self.discovered_urls)} unique URLs found")
        return self.discovered_urls

    def save_urls(self, output_path: pathlib.Path, append: bool = False) -> None:
        """
        Save discovered URLs to a file (one per line).
        
        Args:
            output_path: Path to output file
            append: If True, append to existing file; if False, overwrite
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        with output_path.open(mode, encoding="utf-8") as f:
            for url in sorted(self.discovered_urls):
                f.write(f"{url}\n")

        logger.info(f"Saved {len(self.discovered_urls)} URLs to {output_path}")

    def save_query_history(self, output_path: pathlib.Path) -> None:
        """
        Save query history to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(self.query_history, f, indent=2)

        logger.info(f"Saved query history to {output_path}")


def main():
    """Main entry point for search discovery."""
    import argparse

    parser = argparse.ArgumentParser(description="Discover cleaning-related URLs via search engines")
    parser.add_argument(
        "--provider",
        choices=["google", "bing", "serpapi"],
        default="google",
        help="Search engine provider"
    )
    parser.add_argument(
        "--api-key",
        help="API key (or set via environment variable)"
    )
    parser.add_argument(
        "--search-engine-id",
        help="Google Custom Search Engine ID (for Google provider)"
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        help="Custom search queries (if not provided, generates automatically)"
    )
    parser.add_argument(
        "--max-urls",
        type=int,
        help="Maximum URLs to discover"
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("data/seeds_discovered.txt"),
        help="Output file for discovered URLs"
    )
    parser.add_argument(
        "--allowed-domains",
        nargs="+",
        help="Only include URLs from these domains"
    )
    parser.add_argument(
        "--exclude-domains",
        nargs="+",
        help="Exclude URLs from these domains"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to output file instead of overwriting"
    )

    args = parser.parse_args()

    # Initialize discovery
    discovery = SearchEngineDiscovery(
        provider=args.provider,
        api_key=args.api_key,
        search_engine_id=args.search_engine_id,
        allowed_domains=args.allowed_domains,
        exclude_domains=args.exclude_domains,
    )

    # Discover URLs
    urls = discovery.discover_urls(queries=args.queries, max_urls=args.max_urls)

    # Save results
    discovery.save_urls(args.output, append=args.append)

    # Save query history
    history_path = args.output.parent / f"{args.output.stem}_history.json"
    discovery.save_query_history(history_path)

    print(f"\n✓ Discovery complete!")
    print(f"  Found: {len(urls)} unique URLs")
    print(f"  Saved to: {args.output}")
    print(f"  Query history: {history_path}")


if __name__ == "__main__":
    main()

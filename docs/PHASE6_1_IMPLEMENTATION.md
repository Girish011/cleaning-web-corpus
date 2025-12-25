# Phase 6.1: Search Engine Integration for Automatic URL Discovery - Implementation Summary

## ✅ Implementation Complete

Phase 6.1 has been successfully implemented! This adds search engine integration to automatically discover cleaning-related URLs instead of relying solely on manual seed lists.

## What Was Implemented

### 1. SearchEngineDiscovery Class (`src/crawlers/search_discovery.py`)

**Features:**
- Multiple search engine providers: Google Custom Search, Bing Search, SerpAPI
- Automatic query generation for cleaning-related content
- Domain filtering (allow/exclude specific domains)
- Rate limiting and error handling
- Query history tracking
- URL deduplication

**Key Methods:******

1. **`generate_cleaning_queries()`** - Automatic query generation
   - Generates 200+ cleaning-focused search queries
   - Combines surface types × dirt types × cleaning methods
   - Includes general cleaning queries
   - Removes duplicates

2. **`search(query)`** - Search for a single query
   - Supports Google, Bing, and SerpAPI
   - Handles pagination (Google returns max 10 per request)
   - Filters URLs by allowed/excluded domains
   - Tracks query history

3. **`discover_urls(queries, max_urls)`** - Discover URLs from multiple queries
   - Runs multiple searches automatically
   - Respects max_urls limit
   - Deduplicates URLs
   - Returns set of unique URLs

4. **`save_urls(output_path, append)`** - Save discovered URLs
   - Saves to text file (one URL per line)
   - Can append to existing file
   - Sorted output

5. **`save_query_history(output_path)`** - Save query history
   - JSON format with query, URLs found, timestamp
   - Useful for analysis and debugging

**Supported Providers:**

- **Google Custom Search API**: Requires API key + Search Engine ID
- **Bing Search API**: Requires API key
- **SerpAPI**: Requires API key (easiest to use, aggregates multiple engines)

### 2. Configuration Integration

**SearchDiscoveryConfig** (`src/config.py`):
- `enable`: Enable/disable search discovery
- `provider`: Search engine provider ("google", "bing", "serpapi")
- `api_key`: API key (or use environment variables)
- `search_engine_id`: Google Custom Search Engine ID
- `max_results_per_query`: Maximum results per query
- `delay_seconds`: Rate limiting delay
- `max_urls`: Maximum total URLs to discover
- `auto_discover`: Automatically discover before crawling

**Updated `CrawlerConfig`**:
- Added `search_discovery` field with SearchDiscoveryConfig

**Updated `default.yaml`**:
- Added search_discovery configuration section
- Defaults to disabled (enable: false)

### 3. Integration Script (`scripts/discover_urls.py`)

**Features:**
- Easy-to-use script that reads from config
- Automatic initialization from config file
- Saves discovered URLs to `data/seeds_discovered.txt`
- Saves query history to `data/evaluation/discovery_history.json`
- Provides helpful instructions for merging URLs

## Usage

### Setup

#### 1. Get API Credentials

**Google Custom Search (Recommended):**
1. Go to https://console.cloud.google.com/
2. Create a project (or use existing)
3. Enable "Custom Search API"
4. Create credentials (API Key)
5. Go to https://programmablesearchengine.google.com/
6. Create a Custom Search Engine
7. Get your Search Engine ID

**Bing Search:**
1. Go to https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
2. Get a free API key (3,000 queries/month free)

**SerpAPI (Easiest):**
1. Go to https://serpapi.com/
2. Sign up for free tier (100 searches/month)
3. Get API key

#### 2. Set Environment Variables

```bash
# For Google Custom Search
export GOOGLE_API_KEY="your-api-key"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"

# For Bing Search
export BING_API_KEY="your-api-key"

# For SerpAPI
export SERPAPI_API_KEY="your-api-key"
```

#### 3. Update Configuration (Optional)

Edit `configs/default.yaml`:

```yaml
crawler:
  search_discovery:
    enable: true
    provider: "google"  # or "bing" or "serpapi"
    max_results_per_query: 100
    delay_seconds: 1.0
    max_urls: 500  # Limit total URLs
    auto_discover: false
```

### Command Line Usage

#### Using the Module Directly

```bash
# Discover URLs using Google (with env vars)
python -m src.crawlers.search_discovery \
    --provider google \
    --max-urls 500 \
    --output data/seeds_discovered.txt

# Discover URLs using Bing
python -m src.crawlers.search_discovery \
    --provider bing \
    --api-key "your-key" \
    --max-urls 200 \
    --allowed-domains puffy.com maidbrigade.com

# Discover URLs using SerpAPI
python -m src.crawlers.search_discovery \
    --provider serpapi \
    --max-urls 100 \
    --queries "how to clean carpets" "stain removal guide"
```

#### Using the Integration Script

```bash
# Uses configuration from configs/default.yaml
python scripts/discover_urls.py
```

### Python API Usage

```python
from src.crawlers.search_discovery import SearchEngineDiscovery
import pathlib

# Initialize discovery
discovery = SearchEngineDiscovery(
    provider="google",
    allowed_domains=["puffy.com", "maidbrigade.com"],
    exclude_domains=["spam.com"],
)

# Discover URLs
urls = discovery.discover_urls(max_urls=100)

# Save results
discovery.save_urls(pathlib.Path("data/seeds_discovered.txt"))

# Save query history
discovery.save_query_history(pathlib.Path("data/discovery_history.json"))
```

### Merging Discovered URLs

After discovery, merge with existing seeds:

```bash
# Append discovered URLs to existing seeds
cat data/seeds_discovered.txt >> data/seeds.txt

# Or deduplicate first
sort -u data/seeds.txt data/seeds_discovered.txt > data/seeds_combined.txt
```

## Query Generation

The system automatically generates 200+ cleaning-focused queries by combining:

- **Surface Types**: pillows, bedding, carpets, floors, clothes, fabric, sofa, upholstery, curtains, blankets, mattress, rugs, tiles, wood floors, leather, suede
- **Dirt Types**: stain, dust, odor, mold, mildew, pet hair, grease, ink, wine, coffee, blood, sweat
- **Cleaning Methods**: how to clean, how to remove, cleaning guide, cleaning tips, stain removal, deep clean, maintenance

**Example Generated Queries:**
- "how to remove stain from pillows"
- "carpets dust removal"
- "how to clean clothes"
- "household cleaning tips"
- "stain removal guide"

## Features

### 1. Multiple Providers
- **Google Custom Search**: Most comprehensive, requires setup
- **Bing Search**: Easy setup, good free tier
- **SerpAPI**: Easiest, aggregates multiple engines

### 2. Domain Filtering
- **Allowed Domains**: Only include URLs from specified domains
- **Excluded Domains**: Exclude URLs from specified domains
- **Automatic**: Uses `allowed_domains` from config if set

### 3. Rate Limiting
- Configurable delay between API calls
- Prevents API quota exhaustion
- Default: 1.0 second delay

### 4. Error Handling
- Graceful handling of API errors
- Continues with next query on failure
- Logs errors for debugging

### 5. Query History
- Tracks all queries executed
- Records URLs found per query
- Timestamps for analysis
- Saved as JSON

## Output Files

1. **`data/seeds_discovered.txt`**: Discovered URLs (one per line)
2. **`data/evaluation/discovery_history.json`**: Query history with metadata

## Integration with Existing System

### Automatic Discovery Before Crawling

To automatically discover URLs before crawling, set in config:

```yaml
crawler:
  search_discovery:
    enable: true
    auto_discover: true
```

Then modify the crawler to check for auto_discover and run discovery first.

### Manual Workflow

1. Run discovery: `python scripts/discover_urls.py`
2. Review discovered URLs: `cat data/seeds_discovered.txt`
3. Merge with seeds: `cat data/seeds_discovered.txt >> data/seeds.txt`
4. Run crawler: `scrapy crawl seed_spider`

## API Limits and Costs

### Google Custom Search
- **Free Tier**: 100 queries/day
- **Paid**: $5 per 1,000 queries
- **Rate Limit**: 100 queries/day (free)

### Bing Search
- **Free Tier**: 3,000 queries/month
- **Paid**: $4 per 1,000 queries
- **Rate Limit**: 3 queries/second

### SerpAPI
- **Free Tier**: 100 searches/month
- **Paid**: $50/month for 5,000 searches
- **Rate Limit**: Varies by plan

## Troubleshooting

### Error: "Google Custom Search requires GOOGLE_API_KEY"

**Solution**: Set environment variables:
```bash
export GOOGLE_API_KEY="your-key"
export GOOGLE_SEARCH_ENGINE_ID="your-id"
```

### Error: "No results found"

**Possible Causes**:
- API key invalid
- Search Engine ID incorrect (Google)
- Queries too specific
- Rate limit exceeded

**Solution**: Check API credentials, try broader queries, check rate limits

### Error: "Rate limit exceeded"

**Solution**: Increase `delay_seconds` in config, or wait before retrying

### No URLs Found

**Possible Causes**:
- Domain filtering too restrictive
- Queries not matching content
- API returning empty results

**Solution**: Check `allowed_domains`, try different queries, check API response

## Files Created/Modified

### New Files
- `src/crawlers/search_discovery.py` - Search engine discovery module
- `scripts/discover_urls.py` - Integration script
- `docs/PHASE6_1_IMPLEMENTATION.md` - This document

### Modified Files
- `src/config.py` - Added SearchDiscoveryConfig and updated CrawlerConfig
- `configs/default.yaml` - Added search_discovery configuration

## Next Steps

- **Phase 6.2**: Sitemap crawler (discover all pages from known sites)
- **Phase 6.3**: External API integrations (product databases, Wikipedia)
- **Phase 6.4**: Advanced crawling strategies (ML-guided discovery)

## Notes

- **API Keys**: Never commit API keys to git. Use environment variables.
- **Rate Limits**: Be mindful of API rate limits to avoid quota exhaustion.
- **Costs**: Monitor API usage, especially for paid tiers.
- **Query Quality**: Generated queries are domain-specific and cleaning-focused.
- **Deduplication**: URLs are automatically deduplicated across queries.
- **Domain Filtering**: Use `allowed_domains` to focus on trusted sources.

## Example Output

```
Starting URL discovery...
  Provider: google
  Max URLs: 500
  Allowed domains: ['puffy.com', 'maidbrigade.com']

Searching for: how to remove stain from pillows
Found 8 URLs for query: how to remove stain from pillows
Searching for: carpets dust removal
Found 12 URLs for query: carpets dust removal
...

Discovery complete: 487 unique URLs found

✓ Discovery complete!
  Found: 487 unique URLs
  Saved to: data/seeds_discovered.txt
  Query history: data/evaluation/discovery_history.json
```

This implementation makes the system a true "one-stop shop" for cleaning data by automatically discovering new content sources!

# Seed URL Sources Analysis

**Generated:** 2025-12-24  
**Analysis Date:** After T4 pipeline run  
**Total Seed URLs:** 45  
**Successfully Processed:** 8 (17.8%)  
**Failed:** 37 (82.2%)

## Executive Summary

The current seed URL collection has a **high failure rate** (82.2%), primarily due to:
- **404 Not Found errors** (30 URLs, 66.7% of all seeds)
- **Quality filtering** (4 URLs, 8.9% of all seeds)
- **Timeout/Slow responses** (1 URL, 2.2%)
- **Unknown issues** (2 URLs, 4.4%)

Most failures are from URLs that were **constructed/guessed** rather than verified. Many major cleaning websites (Bob Vila, The Spruce, Good Housekeeping, Hunker, Homedit) returned 404s, suggesting these URLs don't exist or have changed.

## Successfully Processed URLs (8)

These URLs were successfully crawled and passed all quality filters:

1. ✅ `https://www.ariel.in/en-in/how-to-wash/stain-removal`
2. ✅ `https://www.mycleaners.in/list-blog-post/how-and-when-to-clean-carpets-at-home`
3. ✅ `https://www.vanish.co.in/stain-removal/stains-on-clothes/how-to-hand-wash-clothes/`
4. ✅ `https://knowingfabric.com/how-to-remove-stains-from-delicate-fabrics/`
5. ✅ `https://puffy.com/blogs/best-sleep/how-to-get-dust-out-of-pillows`
6. ✅ `https://bigbrandwholesale.com/wholesale-101/online-sellers-how-to-remove-dust-from-clothing-without-washing/`
7. ✅ `https://www.maidbrigade.com/blog/green-cleaning-tips/how-to-clean-pillows-and-bedding/`
8. ✅ `https://www.bobvila.com/articles/how-to-clean-upholstery/`

**Patterns in successful URLs:**
- Manufacturer/brand sites (Ariel, Vanish, Puffy)
- Regional cleaning services (mycleaners.in)
- Specialized fabric care sites (knowingfabric.com, thelaundress.com)
- One major home improvement site (bobvila.com) - but only 1 of 7 URLs worked

## Failure Categories

### 1. 404 Not Found (30 URLs, 66.7%)

These URLs returned HTTP 404 errors, indicating the pages don't exist or have been moved.

#### Bob Vila (6 URLs)
All `/articles/` URLs failed:
- `https://www.bobvila.com/articles/how-to-clean-bathroom-tile/`
- `https://www.bobvila.com/articles/how-to-clean-kitchen-countertops/`
- `https://www.bobvila.com/articles/how-to-clean-refrigerator/`
- `https://www.bobvila.com/articles/how-to-remove-mold-from-carpet/`
- `https://www.bobvila.com/articles/how-to-remove-water-stains/`
- `https://www.bobvila.com/articles/how-to-steam-clean-carpet/`

**Note:** Only `https://www.bobvila.com/articles/how-to-clean-upholstery/` succeeded. Bob Vila's URL structure may have changed, or these specific articles don't exist.

#### The Spruce (6 URLs)
All URLs failed:
- `https://www.thespruce.com/how-to-clean-greasy-oven/`
- `https://www.thespruce.com/how-to-remove-grease-from-countertops/`
- `https://www.thespruce.com/how-to-remove-ink-stain/`
- `https://www.thespruce.com/how-to-remove-mold-from-shower/`
- `https://www.thespruce.com/how-to-remove-pet-hair-from-carpet/`
- `https://www.thespruce.com/how-to-remove-stains-from-upholstery/`
- `https://www.thespruce.com/how-to-spot-clean-carpet/`

**Note:** The Spruce URLs were constructed based on common patterns but don't appear to exist.

#### Good Housekeeping (6 URLs)
All `/home/cleaning/` URLs failed:
- `https://www.goodhousekeeping.com/home/cleaning/how-to-clean-outdoor-furniture/`
- `https://www.goodhousekeeping.com/home/cleaning/how-to-remove-odor-from-carpet/`
- `https://www.goodhousekeeping.com/home/cleaning/how-to-remove-odor-from-dishwasher/`
- `https://www.goodhousekeeping.com/home/cleaning/how-to-remove-pet-hair-from-furniture/`
- `https://www.goodhousekeeping.com/home/cleaning/how-to-remove-water-stains-from-bathroom/`
- `https://www.goodhousekeeping.com/home/cleaning/how-to-remove-water-stains-from-tile/`
- `https://www.goodhousekeeping.com/home/cleaning/how-to-wipe-surfaces/`

**Note:** Good Housekeeping's URL structure may be different, or these articles don't exist.

#### Hunker (6 URLs)
All URLs failed:
- `https://www.hunker.com/how-to-clean-greasy-appliances`
- `https://www.hunker.com/how-to-clean-greasy-stove`
- `https://www.hunker.com/how-to-remove-mold-from-deck`
- `https://www.hunker.com/how-to-remove-odor-from-upholstery`
- `https://www.hunker.com/how-to-scrub-bathroom-grout`
- `https://www.hunker.com/how-to-scrub-stains`

**Note:** Hunker URLs were constructed but don't appear to exist.

#### Homedit (4 URLs)
All URLs failed:
- `https://www.homedit.com/how-to-dry-clean-delicate-fabrics/`
- `https://www.homedit.com/how-to-remove-mold-from-bathroom/`
- `https://www.homedit.com/how-to-spot-clean-upholstery/`
- `https://www.homedit.com/how-to-wipe-hard-surfaces/`

**Note:** Homedit URLs were constructed but don't appear to exist.

#### Other 404s (2 URLs)
- `https://www.vanish.co.in/stain-removal/stains-on-clothes/how-to-remove-grease-from-clothes/`
- `https://www.marthastewart.com/1541278/how-wash-all-your-clothes-hand` (likely typo in URL)

### 2. Quality Filter Failures (4 URLs, 8.9%)

These URLs were successfully crawled (HTTP 200) but failed quality filters during processing:

1. **`https://www.floorworld.com.au/blog/carpet-care-and-maintenance-a-step-by-step-guide`**
   - **Reason:** `word_repetition_too_high: 0.668 (max: 0.600)`
   - **Issue:** High word repetition indicates low-quality or repetitive content

2. **`https://www.vanish.co.in/stain-removal/stains-on-things/how-to-clean-carpet-stain/`**
   - **Reason:** `ngram_repetition_too_high: 11 (max: 8)`
   - **Issue:** High n-gram repetition indicates repetitive phrases/sentences

3. **`https://www.vanish.co.in/stain-removal/stains-on-fabrics/how-to-clean-carpet-stains-effectively/`**
   - **Reason:** `ngram_repetition_too_high: 13 (max: 8)`
   - **Issue:** High n-gram repetition indicates repetitive phrases/sentences

4. **`https://www.thelaundress.com/blogs/tips/how-to-stain-guide-delicate-stain-guide`**
   - **Reason:** Unknown (likely quality filter)
   - **Issue:** Content didn't meet quality thresholds

**Note:** Vanish.co.in URLs have a pattern of high repetition, possibly due to SEO-optimized content or template issues.

## Quality Filter Failure Analysis (T5a)

**Analysis Date:** After T4d pipeline run  
**Filtered URLs:** 7 out of 15 crawled (46.7% filtered rate)

### Summary

From the most recent crawl (T4d), 7 URLs were successfully crawled but filtered during processing due to quality issues. This represents a **46.7% quality filter failure rate** among successfully crawled pages, indicating a need for better URL curation.

### Failure Patterns

#### 1. N-gram Repetition (3 URLs, 42.9% of filtered)

**Threshold:** Max 8 repetitions of any 3-word phrase  
**Common Issue:** SEO-optimized content with repetitive phrases

**Affected URLs:**
- `vanish.co.in/stain-removal/stains-on-things/how-to-clean-carpet-stain/` - 11 repetitions (exceeds 8)
- `vanish.co.in/stain-removal/stains-on-fabrics/how-to-clean-carpet-stains-effectively/` - 13 repetitions (exceeds 8)
- `knowingfabric.com/how-to-remove-mold-and-mildew-from-upholstery/` - 9 repetitions (exceeds 8)

**Pattern:** Manufacturer/brand sites (Vanish, Knowing Fabric) often use repetitive SEO phrases like "how to clean", "stain removal", "effective cleaning" multiple times throughout the content.

**Recommendation:** 
- Avoid URLs with obvious SEO keyword stuffing
- Prefer tutorial/guide content over product pages
- Look for URLs with natural, varied language

#### 2. Word Repetition (2 URLs, 28.6% of filtered)

**Threshold:** Max 60% of content words can be duplicates  
**Common Issue:** Repetitive vocabulary, possibly from templates or low-quality content

**Affected URLs:**
- `floorworld.com.au/blog/carpet-care-and-maintenance-a-step-by-step-guide` - 66.8% repetition (exceeds 60%)
- `knowingfabric.com/how-to-remove-grease-stains-from-clothing/` - 63.8% repetition (exceeds 60%)

**Pattern:** Some blog posts repeat the same words excessively, possibly due to:
- Template-based content generation
- Copy-paste from multiple sources
- Low editorial quality

**Recommendation:**
- Prefer well-edited content from reputable sources
- Avoid blog posts that appear template-generated
- Check for natural language variation

#### 3. Non-Content Pages (1 URL, 14.3% of filtered)

**Affected URL:**
- `maidbrigade.com/we-have-updated-our-content/` - Redirect/update page, not actual cleaning content

**Pattern:** Some URLs are redirects, update notices, or placeholder pages rather than actual content.

**Recommendation:**
- Verify URLs point to actual content pages
- Avoid URLs with patterns like "updated", "redirect", "coming-soon"
- Test URLs before adding to seeds

#### 4. Unknown Quality Issues (1 URL, 14.3% of filtered)

**Affected URL:**
- `thelaundress.com/blogs/tips/how-to-stain-guide-delicate-stain-guide` - Unknown filter reason

**Pattern:** Some URLs fail quality filters for reasons not explicitly logged (may be length, language, or other criteria).

### Domain-Specific Patterns

#### Vanish.co.in
- **Pattern:** High n-gram repetition (11-13 repetitions)
- **Issue:** SEO-optimized product pages with repetitive phrases
- **Success Rate:** 1/4 URLs (25%)
- **Recommendation:** Prefer Vanish URLs that are actual guides/tutorials, not product pages

#### Knowing Fabric
- **Pattern:** Mixed issues - both word repetition (63.8%) and n-gram repetition (9)
- **Issue:** Some content has quality issues despite being from a reliable domain
- **Success Rate:** 1/3 URLs from recent crawl (33%)
- **Recommendation:** Verify content quality before adding, even from reliable domains

#### Floorworld.com.au
- **Pattern:** High word repetition (66.8%)
- **Issue:** Repetitive vocabulary, possibly template-based
- **Recommendation:** Avoid this domain or verify content quality

#### Maid Brigade
- **Pattern:** Non-content pages (redirects/updates)
- **Issue:** Some URLs are not actual content
- **Recommendation:** Verify URLs point to actual articles, not redirect pages

### Common Failure Characteristics

1. **SEO-Optimized Content:**
   - Repetitive keyword phrases
   - Template-based structure
   - Low editorial quality

2. **Product Pages:**
   - Focus on selling rather than educating
   - Repetitive marketing language
   - Less useful for workflow planning

3. **Template Content:**
   - Generated from templates
   - Low word variety
   - Repetitive structure

4. **Non-Content Pages:**
   - Redirects, updates, placeholders
   - Not actual cleaning guides

### Recommendations for URL Curation

1. **Prefer Tutorial/Guide Content:**
   - Look for URLs with "guide", "tutorial", "how-to" in natural contexts
   - Avoid obvious SEO keyword stuffing
   - Prefer step-by-step instructions

2. **Verify Content Quality:**
   - Check for natural language variation
   - Avoid template-generated content
   - Prefer well-edited, original content

3. **Avoid Product Pages:**
   - Skip manufacturer product pages
   - Prefer independent guides and tutorials
   - Look for educational content, not sales content

4. **Test URLs Before Adding:**
   - Verify URLs point to actual content
   - Check for redirects or placeholder pages
   - Ensure content is substantial (>500 words)

5. **Domain-Specific Guidelines:**
   - **Vanish.co.in:** Prefer guide/tutorial URLs, avoid product pages
   - **Knowing Fabric:** Verify content quality, some pages have repetition issues
   - **Maid Brigade:** Verify URLs are actual articles, not redirects
   - **Floorworld.com.au:** Avoid or verify content quality

### Quality Filter Thresholds

Current thresholds (from `configs/default.yaml`):
- **Word Repetition:** Max 60% of content words can be duplicates
- **N-gram Repetition:** Max 8 repetitions of any 3-word phrase
- **Min Words:** 500 words minimum
- **Max Words:** 50,000 words maximum

These thresholds are appropriate for filtering low-quality content while allowing legitimate cleaning guides.

### 3. Timeout/Slow Responses (1 URL, 2.2%)

1. **`https://www.electrolux.in/blog/how-to-clean-a-fabric-sofa-with-a-vacuum-cleaner-at-home/`**
   - **Reason:** Timeout after 180 seconds (3 retries failed)
   - **Issue:** Server is extremely slow or unresponsive
   - **Domain Note:** `electrolux.in` appears to have connectivity issues

**Recommendation:** Add `electrolux.in` to a timeout blacklist or use a shorter timeout for this domain.

### 4. Unknown Issues (2 URLs, 4.4%)

These URLs were not crawled and don't fit the above categories:
- Likely network issues or other errors not captured in logs

## Domain-Specific Analysis

### Reliable Domains (High Success Rate)

1. **`vanish.co.in`** - 1/4 succeeded (25%)
   - Success: `/stains-on-clothes/how-to-hand-wash-clothes/`
   - Failures: 2 quality filters, 1 404
   - **Note:** URLs that succeed have good content, but some have repetition issues

2. **`puffy.com`** - 1/1 succeeded (100%)
   - **Recommendation:** Good source, add more URLs from this domain

3. **`knowingfabric.com`** - 1/1 succeeded (100%)
   - **Recommendation:** Good source, add more URLs from this domain

4. **`mycleaners.in`** - 1/1 succeeded (100%)
   - **Recommendation:** Good source, add more URLs from this domain

5. **`maidbrigade.com`** - 1/1 succeeded (100%)
   - **Recommendation:** Good source, add more URLs from this domain

### Unreliable Domains (Low Success Rate)

1. **`bobvila.com`** - 1/7 succeeded (14.3%)
   - **Issue:** `/articles/` URLs mostly don't exist
   - **Recommendation:** Verify URLs before adding, or use search to find actual article URLs

2. **`thespruce.com`** - 0/7 succeeded (0%)
   - **Issue:** All constructed URLs returned 404
   - **Recommendation:** Don't use constructed URLs; verify actual article URLs exist

3. **`goodhousekeeping.com`** - 0/7 succeeded (0%)
   - **Issue:** All `/home/cleaning/` URLs returned 404
   - **Recommendation:** Verify URL structure before adding URLs

4. **`hunker.com`** - 0/6 succeeded (0%)
   - **Issue:** All constructed URLs returned 404
   - **Recommendation:** Verify URLs exist before adding

5. **`homedit.com`** - 0/4 succeeded (0%)
   - **Issue:** All constructed URLs returned 404
   - **Recommendation:** Verify URLs exist before adding

6. **`electrolux.in`** - 0/1 succeeded (0%)
   - **Issue:** Timeout/slow response
   - **Recommendation:** Add to timeout blacklist or use shorter timeout

## Timeout Policy (T4c Implementation)

**Status:** ✅ Implemented

A **polite timeout policy** has been implemented to prevent slow URLs from blocking the crawl:

### Configuration

- **Download Timeout:** 30 seconds (reduced from default 180 seconds)
- **Retry Times:** 1 retry (reduced from default 3 retries)
- **Timeout Blacklist:** Domains that frequently timeout are automatically skipped

### Implementation Details

1. **Shorter Timeout:** URLs that don't respond within 30 seconds are classified as `timeout/slow` and skipped
2. **Reduced Retries:** Only 1 retry attempt for timeout errors (instead of 3) to avoid blocking
3. **Domain Blacklist:** Domains in `timeout_blacklist` are filtered from seeds before crawling

### Blacklisted Domains

The following domains are automatically skipped due to frequent timeouts:

- **`electrolux.in`** - Consistently times out (>180s), added to blacklist

### Configuration Location

Timeout settings are configured in `configs/default.yaml`:

```yaml
crawler:
  download_timeout: 30.0  # Polite timeout: 30 seconds
  timeout_retry_times: 1  # Retry once for timeouts
  timeout_blacklist:
    - electrolux.in
```

### Benefits

- **Faster Crawls:** Slow URLs don't block the entire crawl
- **Better Resource Usage:** Time isn't wasted waiting for unresponsive servers
- **Automatic Classification:** Timeout errors are clearly identified in logs
- **Configurable:** Easy to adjust timeout and add more domains to blacklist

### Adding New Blacklisted Domains

To add a domain to the timeout blacklist:

1. Identify domains that consistently timeout (check crawl logs)
2. Add domain to `timeout_blacklist` in `configs/default.yaml`
3. Domains will be automatically filtered from seeds before crawling

## Recommendations

### Immediate Actions

1. **Remove all 404 URLs from `data/seeds.txt`**
   - 30 URLs that consistently fail
   - Replace with verified, working URLs

2. **✅ Timeout Policy Implemented (T4c)**
   - Shorter timeout (30s) prevents blocking
   - Blacklist for known slow domains
   - See "Timeout Policy" section above

3. **Verify URLs before adding**
   - Don't construct URLs based on patterns
   - Use search engines or site search to find actual article URLs
   - Test URLs manually or with a quick HEAD request before adding

### URL Curation Strategy

1. **Use verified sources:**
   - Manufacturer/brand sites (Ariel, Vanish, etc.)
   - Regional cleaning services
   - Specialized cleaning blogs

2. **Verify before adding:**
   - Test URLs with `curl -I` or similar
   - Use site search functions
   - Check if URLs are accessible

3. **Avoid pattern-based URL construction:**
   - Don't guess URL structures
   - Don't assume `/articles/how-to-X/` patterns work

4. **Prioritize domains with high success rates:**
   - `puffy.com` (100%)
   - `knowingfabric.com` (100%)
   - `mycleaners.in` (100%)
   - `maidbrigade.com` (100%)

### Quality Filter Improvements

1. **Review repetition thresholds:**
   - Some Vanish URLs have high repetition but may still be useful
   - Consider domain-specific thresholds

2. **Document quality filter reasons:**
   - Add logging for why URLs are filtered
   - Help identify patterns in quality issues

## Next Steps (T4b)

For T4b, focus on finding **verified, working URLs** for high-priority missing combinations:

1. **Use search engines** to find actual article URLs
2. **Test URLs** before adding to seeds.txt
3. **Prioritize reliable domains** (puffy.com, knowingfabric.com, etc.)
4. **Target missing combinations** from `docs/COVERAGE_GAPS.md`:
   - Upholstery cleaning (need more than 1)
   - Hard surfaces (countertops, tiles)
   - Bathroom cleaning (mold, water stains)
   - Appliances (grease, odor)
   - More dirt types (grease, pet_hair, mold, odor)
   - More methods (spot_clean, steam_clean, wipe, scrub)

## Statistics Summary

| Category | Count | Percentage |
|----------|-------|------------|
| **Total Seeds** | 45 | 100% |
| **Successfully Processed** | 8 | 17.8% |
| **404 Not Found** | 30 | 66.7% |
| **Quality Filtered** | 4 | 8.9% |
| **Timeout/Slow** | 1 | 2.2% |
| **Unknown** | 2 | 4.4% |

## Domain Success Rates

| Domain | Success | Total | Success Rate |
|--------|---------|-------|--------------|
| puffy.com | 1 | 1 | 100% |
| knowingfabric.com | 1 | 1 | 100% |
| mycleaners.in | 1 | 1 | 100% |
| maidbrigade.com | 1 | 1 | 100% |
| bobvila.com | 1 | 7 | 14.3% |
| vanish.co.in | 1 | 4 | 25% |
| thespruce.com | 0 | 7 | 0% |
| goodhousekeeping.com | 0 | 7 | 0% |
| hunker.com | 0 | 6 | 0% |
| homedit.com | 0 | 4 | 0% |
| electrolux.in | 0 | 1 | 0% |


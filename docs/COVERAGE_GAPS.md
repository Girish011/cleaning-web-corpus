# Coverage Gaps Analysis

**Generated:** 2025-12-21  
**Dataset:** `data/processed/cleaning_docs.jsonl`  
**Total Documents:** 7 (target: ≥50)

## Executive Summary

The current dataset has significant coverage gaps across all dimensions:
- **Surface Types:** 3/8 covered (37.5%)
- **Dirt Types:** 2/8 covered (25%)
- **Cleaning Methods:** 3/8 covered (37.5%)
- **Total Combinations:** 6/512 possible (1.2%)

## Supported Categories

### Surface Types (8 total)
1. ✅ `pillows_bedding` - **Covered** (2 documents)
2. ✅ `clothes` - **Covered** (4 documents)
3. ✅ `carpets_floors` - **Covered** (1 document)
4. ❌ `upholstery` - **Missing**
5. ❌ `hard_surfaces` - **Missing**
6. ❌ `appliances` - **Missing**
7. ❌ `bathroom` - **Missing**
8. ❌ `outdoor` - **Missing**

### Dirt Types (8 total)
1. ✅ `dust` - **Covered** (3 documents)
2. ✅ `stain` - **Covered** (4 documents)
3. ❌ `odor` - **Missing**
4. ❌ `grease` - **Missing**
5. ❌ `mold` - **Missing**
6. ❌ `pet_hair` - **Missing**
7. ❌ `water_stain` - **Missing**
8. ❌ `ink` - **Missing**

### Cleaning Methods (8 total)
1. ✅ `vacuum` - **Covered** (3 documents)
2. ✅ `washing_machine` - **Covered** (2 documents)
3. ✅ `hand_wash` - **Covered** (2 documents)
4. ❌ `spot_clean` - **Missing**
5. ❌ `steam_clean` - **Missing**
6. ❌ `dry_clean` - **Missing**
7. ❌ `wipe` - **Missing**
8. ❌ `scrub` - **Missing**

## Currently Covered Combinations

| Surface Type | Dirt Type | Cleaning Method | Count |
|--------------|-----------|-----------------|-------|
| carpets_floors | stain | vacuum | 1 |
| clothes | dust | vacuum | 1 |
| clothes | stain | hand_wash | 2 |
| pillows_bedding | dust | vacuum | 1 |
| pillows_bedding | dust | washing_machine | 1 |

**Total:** 6 unique combinations

## Missing Combinations by Priority

### High Priority (Common Real-World Scenarios)

#### Missing Surface Types × Common Dirt × Common Methods

1. **Upholstery** (sofa, couch, chairs)
   - `upholstery × stain × spot_clean` - Very common
   - `upholstery × pet_hair × vacuum` - Very common
   - `upholstery × odor × steam_clean` - Common
   - `upholstery × dust × vacuum` - Common

2. **Hard Surfaces** (countertops, tables, tiles)
   - `hard_surfaces × grease × wipe` - Very common (kitchen)
   - `hard_surfaces × water_stain × scrub` - Common (bathroom)
   - `hard_surfaces × stain × wipe` - Common
   - `hard_surfaces × dust × wipe` - Common

3. **Bathroom** (shower, bathtub, sink, toilet)
   - `bathroom × mold × scrub` - Very common
   - `bathroom × water_stain × scrub` - Very common
   - `bathroom × grease × scrub` - Common
   - `bathroom × odor × scrub` - Common

4. **Appliances** (oven, refrigerator, dishwasher)
   - `appliances × grease × scrub` - Very common
   - `appliances × odor × wipe` - Common
   - `appliances × water_stain × wipe` - Common

#### Missing Dirt Types × Existing Surfaces

5. **Grease** (kitchen-related)
   - `hard_surfaces × grease × wipe` - High priority
   - `appliances × grease × scrub` - High priority
   - `clothes × grease × hand_wash` - Medium priority

6. **Mold** (bathroom, damp areas)
   - `bathroom × mold × scrub` - High priority
   - `carpets_floors × mold × steam_clean` - Medium priority

7. **Pet Hair** (furniture, carpets)
   - `upholstery × pet_hair × vacuum` - High priority
   - `carpets_floors × pet_hair × vacuum` - High priority
   - `clothes × pet_hair × vacuum` - Medium priority

8. **Odor** (various surfaces)
   - `upholstery × odor × steam_clean` - High priority
   - `carpets_floors × odor × steam_clean` - High priority
   - `appliances × odor × wipe` - Medium priority

#### Missing Cleaning Methods × Existing Combinations

9. **Spot Clean** (targeted cleaning)
   - `upholstery × stain × spot_clean` - High priority
   - `clothes × stain × spot_clean` - Medium priority
   - `carpets_floors × stain × spot_clean` - Medium priority

10. **Steam Clean** (deep cleaning)
    - `carpets_floors × odor × steam_clean` - High priority
    - `upholstery × odor × steam_clean` - High priority
    - `bathroom × mold × steam_clean` - Medium priority

11. **Wipe** (hard surfaces)
    - `hard_surfaces × grease × wipe` - High priority
    - `hard_surfaces × dust × wipe` - High priority
    - `appliances × grease × wipe` - High priority

12. **Scrub** (tough stains, bathroom)
    - `bathroom × mold × scrub` - High priority
    - `bathroom × water_stain × scrub` - High priority
    - `hard_surfaces × grease × scrub` - High priority

### Medium Priority (Less Common but Important)

13. **Dry Clean** (delicate fabrics)
    - `clothes × stain × dry_clean` - Medium priority
    - `upholstery × stain × dry_clean` - Medium priority

14. **Ink** (specialized removal)
    - `clothes × ink × spot_clean` - Medium priority
    - `upholstery × ink × spot_clean` - Medium priority

15. **Water Stain** (bathroom, hard surfaces)
    - `bathroom × water_stain × scrub` - Medium priority
    - `hard_surfaces × water_stain × scrub` - Medium priority

16. **Outdoor** (patio, deck, driveway)
    - `outdoor × stain × scrub` - Medium priority
    - `outdoor × mold × scrub` - Medium priority
    - `outdoor × dust × wipe` - Low priority

### Low Priority (Niche Scenarios)

17. Combinations involving `outdoor` surface type (less common in typical household cleaning)
18. Rare combinations like `pillows_bedding × ink × spot_clean`
19. Combinations with `dry_clean` method (requires professional context)

## Recommended Seed URL Targets

### Priority 1: High-Value Missing Combinations

1. **Upholstery cleaning guides**
   - "how to remove stain from sofa"
   - "how to remove pet hair from couch"
   - "upholstery odor removal"
   - "spot clean upholstery"

2. **Kitchen hard surfaces**
   - "how to remove grease from countertop"
   - "clean greasy stove"
   - "kitchen counter cleaning"

3. **Bathroom cleaning**
   - "how to remove mold from shower"
   - "bathroom tile cleaning"
   - "remove water stains from bathroom"
   - "clean bathroom grout"

4. **Appliance cleaning**
   - "how to clean greasy oven"
   - "refrigerator cleaning guide"
   - "remove odor from dishwasher"

### Priority 2: Expand Existing Categories

5. **More dirt types on existing surfaces**
   - "remove grease from clothes"
   - "remove pet hair from carpet"
   - "remove mold from carpet"
   - "remove odor from carpet"

6. **More methods for existing combinations**
   - "spot clean clothes stain"
   - "steam clean carpet"
   - "scrub carpet stain"

### Priority 3: Complete Coverage

7. **Outdoor cleaning**
   - "clean patio furniture"
   - "remove mold from deck"
   - "outdoor surface cleaning"

8. **Specialized scenarios**
   - "dry clean delicate fabric"
   - "remove ink stain"
   - "water stain removal"

## Coverage Goals

### Short-term (Phase 1)
- **Target:** 50+ documents
- **Focus:** High-priority missing combinations
- **Goal:** Cover at least 5/8 surface types, 5/8 dirt types, 5/8 methods
- **Target combinations:** 30-40 unique combinations

### Medium-term
- **Target:** 100+ documents
- **Focus:** Medium-priority combinations
- **Goal:** Cover 7/8 surface types, 7/8 dirt types, 7/8 methods
- **Target combinations:** 100+ unique combinations

### Long-term
- **Target:** 200+ documents
- **Focus:** Complete coverage
- **Goal:** Cover all 8 surface types, 8 dirt types, 8 methods
- **Target combinations:** 200+ unique combinations (out of 512 possible)

## High-Quality Content Criteria

**Based on analysis from `docs/SEED_SOURCES.md` (T5a quality filter analysis)**

To ensure new seed URLs result in high-quality documents that pass quality filters, the following criteria should be applied when curating URLs:

### ✅ Preferred Content Types

1. **Tutorial/Guide Content:**
   - Step-by-step cleaning instructions
   - Educational content with natural language variation
   - Well-edited, original articles
   - URLs with "guide", "tutorial", "how-to" in natural contexts

2. **Independent Guides:**
   - Non-product pages from reputable sources
   - Content focused on education, not sales
   - Natural language without keyword stuffing

3. **Substantial Content:**
   - Minimum 500 words (meets quality filter threshold)
   - Maximum 50,000 words (avoids overly long pages)
   - Meaningful content, not just boilerplate

### ❌ Avoid These Content Types

1. **SEO-Optimized/Spam Content:**
   - Repetitive keyword phrases (e.g., "how to clean" repeated 10+ times)
   - Template-based content generation
   - Low editorial quality
   - **Pattern:** N-gram repetition >8, word repetition >60%

2. **Product Pages:**
   - Manufacturer product pages focused on selling
   - Repetitive marketing language
   - Less useful for workflow planning
   - **Example:** Vanish.co.in product pages with 11-13 n-gram repetitions

3. **Template/Generated Content:**
   - Content generated from templates
   - Low word variety (high word repetition)
   - Repetitive structure
   - **Example:** Floorworld.com.au with 66.8% word repetition

4. **Non-Content Pages:**
   - Redirects, update notices, placeholder pages
   - URLs with "updated", "redirect", "coming-soon" patterns
   - Not actual cleaning guides
   - **Example:** `maidbrigade.com/we-have-updated-our-content/`

### Domain-Specific Guidelines

Based on quality filter analysis:

- **Vanish.co.in:** Prefer guide/tutorial URLs, avoid product pages (high n-gram repetition in product pages)
- **Knowing Fabric:** Verify content quality before adding (some pages have repetition issues)
- **Maid Brigade:** Verify URLs are actual articles, not redirects
- **Floorworld.com.au:** Avoid or verify content quality (high word repetition)
- **Reliable domains (100% success):** `puffy.com`, `mycleaners.in` - prefer these

### Quality Filter Thresholds

Current thresholds (from `configs/default.yaml`):
- **Word Repetition:** Max 60% of content words can be duplicates
- **N-gram Repetition:** Max 8 repetitions of any 3-word phrase
- **Min Words:** 500 words minimum
- **Max Words:** 50,000 words maximum

### URL Verification Checklist

Before adding a URL to `data/seeds.txt`:

- [ ] URL points to actual content (not redirect/placeholder)
- [ ] Content is substantial (>500 words)
- [ ] Content is educational/tutorial (not product page)
- [ ] Natural language variation (not template-generated)
- [ ] No obvious SEO keyword stuffing
- [ ] From reputable source or verified reliable domain
- [ ] Matches high-priority missing combination from coverage gaps

### References

- See `docs/SEED_SOURCES.md` section "Quality Filter Failure Analysis (T5a)" for detailed failure patterns
- See `docs/SEED_SOURCES.md` section "Domain-Specific Patterns" for domain-specific recommendations

## Notes

- The current dataset is very small (7 documents) and needs significant expansion.
- Some combinations may be naturally rare (e.g., `outdoor × ink × dry_clean`), which is acceptable.
- Focus should be on realistic, common cleaning scenarios that would be useful for robot/agent planning.
- The goal is not to cover every possible combination, but to have good coverage of practical, real-world cleaning workflows.
- **New URLs must meet High-Quality Content Criteria above to avoid quality filter failures.**


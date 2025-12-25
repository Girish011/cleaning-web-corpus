# Data Warehouse Design

## Purpose

The data warehouse serves as the analytical backbone for the Cleaning Workflow Planner Platform. It provides:

1. **Structured Storage**: Normalized, queryable storage of cleaning procedures, tools, steps, and quality metrics from the web corpus
2. **Analytical Capabilities**: Support for complex queries about coverage gaps, tool usage patterns, method effectiveness, and corpus quality
3. **Agent Grounding**: Fast, structured access to cleaning knowledge for the workflow planner agent
4. **Research & Planning**: Enable data-driven decisions about corpus expansion, quality improvements, and coverage optimization

The warehouse uses **ClickHouse** for its columnar storage and analytical query performance, combined with **dbt** for data transformation, modeling, and documentation.

## Logical ClickHouse Tables

### 1. `raw_documents`

Stores the raw crawled and processed documents with all metadata.

**Columns:**
- `document_id` (String, Primary Key) - Unique identifier (hash of URL or UUID)
- `url` (String) - Source URL
- `title` (String) - Document title
- `main_text` (String) - Full extracted text content
- `raw_html` (String, Nullable) - Original HTML (optional, for debugging)
- `source` (String) - Crawler source identifier (e.g., "seed_spider")
- `language` (String) - Detected language code (e.g., "en")
- `http_status` (UInt16) - HTTP status code (200, 404, etc.)
- `fetched_at` (DateTime) - Timestamp when document was crawled
- `processed_at` (DateTime) - Timestamp when document was processed
- `surface_type` (String) - Normalized surface type (e.g., "carpets_floors", "clothes")
- `dirt_type` (String) - Normalized dirt type (e.g., "stain", "dust", "grease")
- `cleaning_method` (String) - Normalized cleaning method (e.g., "vacuum", "hand_wash", "spot_clean")
- `extraction_method` (String) - Method used for extraction ("rule_based", "ner", "llm")
- `extraction_confidence` (Float32, Nullable) - Overall extraction confidence score
- `image_count` (UInt16) - Number of images in document
- `video_count` (UInt16) - Number of videos in document
- `word_count` (UInt32) - Word count of main_text
- `character_count` (UInt32) - Character count of main_text

**Primary Key:** `document_id`

**Grain:** One row per document

**Indexes:**
- Index on `(surface_type, dirt_type, cleaning_method)` for coverage queries
- Index on `fetched_at` for time-based analysis
- Index on `extraction_method` for extraction quality analysis

### 2. `steps`

Stores individual cleaning steps extracted from documents.

**Columns:**
- `step_id` (String, Primary Key) - Unique identifier (UUID or hash)
- `document_id` (String) - Foreign key to `raw_documents.document_id`
- `step_order` (UInt16) - Sequential order of step within document (1, 2, 3, ...)
- `step_text` (String) - Full text of the cleaning step
- `step_summary` (String, Nullable) - Short summary/action description
- `confidence` (Float32) - Extraction confidence score (0.0-1.0)
- `extraction_method` (String) - Method used ("rule_based", "ner", "llm")
- `created_at` (DateTime) - Timestamp when step was extracted

**Primary Key:** `step_id`

**Grain:** One row per step per document

**Indexes:**
- Index on `document_id` for document-level queries
- Index on `(document_id, step_order)` for ordered retrieval
- Index on `confidence` for quality filtering

### 3. `tools`

Stores cleaning tools/equipment mentioned or extracted from documents.

**Columns:**
- `tool_id` (String, Primary Key) - Unique identifier (UUID or hash)
- `document_id` (String) - Foreign key to `raw_documents.document_id`
- `tool_name` (String) - Normalized tool name (e.g., "vinegar", "microfiber_cloth", "vacuum")
- `tool_category` (String, Nullable) - Tool category (e.g., "chemical", "equipment", "cloth", "brush")
- `confidence` (Float32) - Extraction confidence score (0.0-1.0)
- `extraction_method` (String) - Method used ("rule_based", "ner", "llm")
- `mentioned_in_step_id` (String, Nullable) - If tool was mentioned in a specific step, reference to `steps.step_id`
- `created_at` (DateTime) - Timestamp when tool was extracted

**Primary Key:** `tool_id`

**Grain:** One row per tool mention per document (same tool can appear multiple times if mentioned in different contexts)

**Indexes:**
- Index on `document_id` for document-level queries
- Index on `tool_name` for tool usage analysis
- Index on `tool_category` for category-based queries
- Index on `mentioned_in_step_id` for step-tool relationships

### 4. `quality_metrics`

Stores quality metrics computed for documents and images.

**Columns:**
- `metric_id` (String, Primary Key) - Unique identifier (UUID)
- `document_id` (String) - Foreign key to `raw_documents.document_id`
- `metric_type` (String) - Type of metric ("text_quality", "image_quality", "alignment", "filter_result")
- `metric_name` (String) - Specific metric name (e.g., "clip_score", "perplexity", "word_repetition_ratio")
- `metric_value` (Float32, Nullable) - Metric value (can be null for boolean metrics)
- `metric_bool` (UInt8, Nullable) - Boolean metric value (0/1, for pass/fail metrics)
- `threshold` (Float32, Nullable) - Threshold used for this metric
- `passed` (UInt8) - Whether metric passed threshold (0/1)
- `metadata` (String, Nullable) - JSON string with additional context (e.g., filter reason, extraction details)
- `computed_at` (DateTime) - Timestamp when metric was computed

**Primary Key:** `metric_id`

**Grain:** One row per metric per document (or per image if image-specific)

**Indexes:**
- Index on `document_id` for document-level quality analysis
- Index on `(metric_type, metric_name)` for metric-specific queries
- Index on `passed` for filtering by quality

**Note:** For image-specific metrics (e.g., CLIP scores), we can either:
- Store them in this table with `document_id` and include image path in metadata, OR
- Create a separate `image_quality_metrics` table with `image_id` foreign key

## dbt Model Layers

### Sources Layer

**Purpose:** Define external data sources (raw JSONL files or ClickHouse raw tables)

**Models:**
- `source_raw_documents` - Points to `raw_documents` table in ClickHouse
- `source_steps` - Points to `steps` table
- `source_tools` - Points to `tools` table
- `source_quality_metrics` - Points to `quality_metrics` table

**Configuration:**
```yaml
sources:
  - name: cleaning_corpus
    database: cleaning_warehouse
    schema: raw
    tables:
      - name: raw_documents
      - name: steps
      - name: tools
      - name: quality_metrics
```

### Staging Layer

**Purpose:** Clean, normalize, and prepare raw data for dimensional modeling

**Models:**

1. **`stg_documents`**
   - Cleans and standardizes `raw_documents`
   - Handles nulls, normalizes surface_type/dirt_type/method values
   - Adds computed fields (e.g., `has_steps`, `has_tools`, `quality_score`)
   - Filters out invalid documents

2. **`stg_steps`**
   - Cleans step text (trim, normalize whitespace)
   - Validates step_order sequences
   - Adds step length metrics
   - Links to documents

3. **`stg_tools`**
   - Normalizes tool names (lowercase, remove duplicates)
   - Validates tool categories
   - Links to documents and steps

4. **`stg_quality_metrics`**
   - Pivots quality metrics for easier analysis
   - Computes aggregate quality scores per document
   - Separates text vs image quality metrics

### Dimensions Layer

**Purpose:** Create dimension tables for analytical queries

**Models:**

1. **`dim_surface`**
   - Surrogate key: `surface_key` (Int32)
   - Natural key: `surface_type` (String)
   - Attributes: `surface_name`, `surface_category`, `description`
   - Metadata: `created_at`, `updated_at`

2. **`dim_dirt`**
   - Surrogate key: `dirt_key` (Int32)
   - Natural key: `dirt_type` (String)
   - Attributes: `dirt_name`, `dirt_category`, `description`
   - Metadata: `created_at`, `updated_at`

3. **`dim_method`**
   - Surrogate key: `method_key` (Int32)
   - Natural key: `cleaning_method` (String)
   - Attributes: `method_name`, `method_category` (e.g., "mechanical", "chemical", "thermal")
   - Attributes: `description`, `typical_duration_minutes`
   - Metadata: `created_at`, `updated_at`

4. **`dim_tool`**
   - Surrogate key: `tool_key` (Int32)
   - Natural key: `tool_name` (String)
   - Attributes: `tool_category`, `tool_type` (e.g., "consumable", "equipment", "chemical")
   - Attributes: `description`, `typical_cost_range`
   - Metadata: `created_at`, `updated_at`

5. **`dim_document`** (optional, for document-level attributes)
   - Surrogate key: `document_key` (Int32)
   - Natural key: `document_id` (String)
   - Attributes: `url`, `title`, `source`, `language`, `fetched_at`
   - Attributes: `word_count`, `image_count`, `video_count`
   - Metadata: `created_at`, `updated_at`

### Facts Layer

**Purpose:** Create fact tables for analytical queries

**Models:**

1. **`fct_cleaning_procedures`**
   - **Grain:** One row per unique (surface × dirt × method) combination per document
   - **Dimensions:**
     - `surface_key` (FK to `dim_surface`)
     - `dirt_key` (FK to `dim_dirt`)
     - `method_key` (FK to `dim_method`)
     - `document_key` (FK to `dim_document`, optional)
   - **Measures:**
     - `document_count` - Number of documents for this combination
     - `step_count` - Average/total steps for this combination
     - `tool_count` - Average/total unique tools for this combination
     - `avg_extraction_confidence` - Average extraction confidence
     - `quality_score` - Aggregate quality score
   - **Metadata:**
     - `first_seen_at` - First time this combination appeared
     - `last_seen_at` - Most recent appearance
     - `total_occurrences` - Total number of times this combination appears

2. **`fct_tool_usage`**
   - **Grain:** One row per tool usage per document (or per procedure)
   - **Dimensions:**
     - `tool_key` (FK to `dim_tool`)
     - `surface_key` (FK to `dim_surface`)
     - `dirt_key` (FK to `dim_dirt`)
     - `method_key` (FK to `dim_method`)
     - `document_key` (FK to `dim_document`)
   - **Measures:**
     - `usage_count` - Number of times tool is mentioned
     - `avg_confidence` - Average extraction confidence
     - `is_primary_tool` - Whether tool is primary for this method (0/1)
   - **Metadata:**
     - `first_used_at` - First time tool was used for this combination
     - `last_used_at` - Most recent usage

3. **`fct_step_sequences`** (optional, for step ordering analysis)
   - **Grain:** One row per step in sequence per document
   - **Dimensions:**
     - `document_key` (FK to `dim_document`)
     - `surface_key`, `dirt_key`, `method_key`
   - **Measures:**
     - `step_order` - Position in sequence
     - `step_length` - Character/word count of step
     - `has_tool_mention` - Whether step mentions a tool (0/1)
   - **Metadata:**
     - `step_text` - Full step text (for reference)

4. **`fct_quality_scores`** (optional, for quality trend analysis)
   - **Grain:** One row per quality metric per document per time period
   - **Dimensions:**
     - `document_key` (FK to `dim_document`)
     - `metric_type` - Type of quality metric
   - **Measures:**
     - `metric_value` - Metric value
     - `passed` - Whether passed threshold (0/1)
     - `quality_score` - Normalized quality score (0-1)
   - **Metadata:**
     - `computed_at` - When metric was computed

## Analytical Questions the Warehouse Should Support

1. **Coverage Analysis**
   - "What surface × dirt × method combinations are missing or underrepresented?"
   - "Which combinations have the most/fewest documents?"
   - "What percentage of possible combinations are covered?"

2. **Tool Usage Patterns**
   - "What are the most common tools for cleaning [surface] with [method]?"
   - "Which tools are used together most frequently?"
   - "What tools are recommended for [dirt_type] on [surface_type]?"

3. **Method Effectiveness**
   - "Which cleaning methods are most commonly used for [surface] × [dirt]?"
   - "What is the average number of steps for [method]?"
   - "Which methods require the most tools?"

4. **Step Sequence Analysis**
   - "What is the typical step sequence for [surface] × [dirt] × [method]?"
   - "What are the most common first/last steps?"
   - "How many steps are typically needed for [method]?"

5. **Quality Metrics**
   - "What is the average extraction confidence for documents using [extraction_method]?"
   - "Which documents have the highest/lowest quality scores?"
   - "What percentage of documents pass all quality filters?"

6. **Corpus Growth & Trends**
   - "How has corpus coverage changed over time?"
   - "Which surface/dirt/method categories are growing fastest?"
   - "What is the average quality of newly added documents?"

7. **Gap Identification**
   - "Which high-priority combinations (from COVERAGE_GAPS.md) are still missing?"
   - "What combinations have only 1-2 documents and need more coverage?"
   - "Which surface types have the least coverage overall?"

8. **Extraction Quality**
   - "Which extraction method (rule_based, ner, llm) produces the highest confidence scores?"
   - "What percentage of documents have successfully extracted tools and steps?"
   - "Which documents need re-extraction with a different method?"

9. **Tool-Surface Compatibility**
   - "Which tools are never/rarely used with [surface_type]?"
   - "What tools are surface-specific vs. universal?"
   - "Are there tool combinations that are incompatible?"

10. **Reference Retrieval for Agent**
    - "Get the top 5 most relevant documents for [surface] × [dirt] × [method]"
    - "What are the most common steps for this combination?"
    - "What tools are recommended with high confidence for this scenario?"

## Implementation Notes

### ClickHouse-Specific Considerations

- Use **MergeTree** engine for `raw_documents`, `steps`, `tools` for efficient inserts and queries
- Use **ReplacingMergeTree** for `quality_metrics` if we want to update metrics over time
- Consider **Materialized Views** for pre-aggregated coverage matrices
- Use **Array** types for storing multiple values (e.g., `image_urls`, `video_urls`) if needed
- Consider **Nested** types for hierarchical data (e.g., `images` array with nested metadata)

### dbt-Specific Considerations

- Use **incremental models** for fact tables to handle growing data
- Add **tests** for referential integrity, uniqueness, and not-null constraints
- Use **snapshots** for slowly changing dimensions (e.g., if tool categories change)
- Document all models with `description` and `columns` in `schema.yml`
- Use **macros** for common transformations (e.g., normalizing surface types)

### Data Loading Strategy

1. **Initial Load**: Bulk insert from `cleaning_docs.jsonl` into `raw_documents`
2. **Incremental Load**: Append new documents as they are processed
3. **ETL Pipeline**: Use dbt to transform raw data into staging → dimensions → facts
4. **Refresh Frequency**: Daily or on-demand after corpus updates

### Query Performance

- Pre-aggregate coverage matrices in materialized views
- Create summary tables for common analytical queries
- Use ClickHouse's columnar storage for fast aggregations
- Consider partitioning large tables by `fetched_at` date


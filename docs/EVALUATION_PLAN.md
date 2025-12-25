# Evaluation Plan

## Overview

This document describes the evaluation framework for the Cleaning Workflow Planner Platform. Evaluation is organized into three main categories:

1. **Data Quality** - Assessing the quality and coverage of the corpus
2. **Extraction Quality** - Measuring accuracy of structured extraction (surface/dirt/method/tools/steps)
3. **Planner Quality** - Evaluating the workflow planner agent's output quality

All metrics are designed to be computed from the ClickHouse data warehouse and linked to the dbt models defined in `DATA_WAREHOUSE.md`. The planner quality metrics align with the agent design in `WORKFLOW_AGENT_DESIGN.md`.

## 1. Data Quality Evaluation

### 1.1 Coverage Metrics

**Purpose:** Measure how well the corpus covers the space of possible cleaning scenarios.

**Metrics:**

1. **Combination Coverage**
   - **Definition:** Percentage of possible surface × dirt × method combinations that have at least one document
   - **Formula:** `(unique_combinations / total_possible_combinations) × 100`
   - **Total Possible:** 8 surface types × 8 dirt types × 8 methods = 512 combinations
   - **Target:** ≥10% coverage (50+ unique combinations) for MVP
   - **ClickHouse Query:** Query `fct_cleaning_procedures` fact table
     ```sql
     SELECT 
       COUNT(DISTINCT CONCAT(surface_key, '_', dirt_key, '_', method_key)) as unique_combinations,
       512 as total_possible,
       (unique_combinations / 512.0) * 100 as coverage_percentage
     FROM fct_cleaning_procedures
     ```
   - **dbt Model:** `fct_cleaning_procedures` (see `DATA_WAREHOUSE.md`)

2. **Dimension Coverage**
   - **Surface Types Covered:** Count of unique surface types with documents
   - **Dirt Types Covered:** Count of unique dirt types with documents
   - **Methods Covered:** Count of unique cleaning methods with documents
   - **Target:** ≥5/8 for each dimension (62.5% coverage)
   - **ClickHouse Query:** Query dimension tables or `fct_cleaning_procedures`
     ```sql
     SELECT 
       COUNT(DISTINCT surface_key) as surface_types_covered,
       COUNT(DISTINCT dirt_key) as dirt_types_covered,
       COUNT(DISTINCT method_key) as methods_covered
     FROM fct_cleaning_procedures
     ```
   - **dbt Models:** `dim_surface`, `dim_dirt`, `dim_method`, `fct_cleaning_procedures`

3. **Document Distribution**
   - **Definition:** Distribution of documents across combinations
   - **Metrics:**
     - Average documents per combination
     - Combinations with only 1 document (low coverage)
     - Combinations with ≥3 documents (well-covered)
   - **Target:** ≥30% of combinations have ≥3 documents
   - **ClickHouse Query:**
     ```sql
     SELECT 
       document_count,
       COUNT(*) as combination_count
     FROM fct_cleaning_procedures
     GROUP BY document_count
     ORDER BY document_count
     ```
   - **dbt Model:** `fct_cleaning_procedures.document_count`

4. **Gap Analysis**
   - **Definition:** Identify missing high-priority combinations (from `COVERAGE_GAPS.md`)
   - **Metrics:**
     - Number of high-priority combinations missing
     - Number of medium-priority combinations missing
   - **ClickHouse Query:** Compare `fct_cleaning_procedures` against priority list
   - **dbt Model:** `fct_cleaning_procedures`

**Storage:** Metrics stored in `fct_quality_scores` with `metric_type='coverage'`

### 1.2 Repetition Metrics

**Purpose:** Measure text quality by detecting repetitive content (SEO spam, templates).

**Metrics:**

1. **Character Repetition Ratio**
   - **Definition:** Percentage of text that consists of repeated characters
   - **Formula:** `(repeated_char_count / total_char_count) × 100`
   - **Threshold:** Documents with >30% repetition are filtered (see `configs/default.yaml`)
   - **ClickHouse Query:** Query `quality_metrics` table
     ```sql
     SELECT 
       document_id,
       metric_value as repetition_ratio
     FROM quality_metrics
     WHERE metric_type = 'text_quality' 
       AND metric_name = 'char_repetition_ratio'
       AND metric_value > 0.3
     ```
   - **Storage:** `quality_metrics` table with `metric_type='text_quality'`, `metric_name='char_repetition_ratio'`

2. **Word Repetition Ratio**
   - **Definition:** Percentage of content words that are duplicates
   - **Formula:** `(duplicate_word_count / total_content_words) × 100`
   - **Threshold:** Documents with >60% word repetition are filtered
   - **ClickHouse Query:**
     ```sql
     SELECT 
       document_id,
       metric_value as word_repetition_ratio
     FROM quality_metrics
     WHERE metric_type = 'text_quality' 
       AND metric_name = 'word_repetition_ratio'
       AND metric_value > 0.6
     ```
   - **Storage:** `quality_metrics` table

3. **N-gram Repetition**
   - **Definition:** Number of times the same n-gram (3-word phrase) appears
   - **Threshold:** N-grams appearing >8 times indicate repetitive content
   - **ClickHouse Query:** Requires text analysis (stored in `quality_metrics` or computed on-demand)
   - **Storage:** `quality_metrics` table with `metric_name='ngram_repetition'`

4. **Repetition Filter Pass Rate**
   - **Definition:** Percentage of documents that pass all repetition filters
   - **Formula:** `(documents_passing / total_documents) × 100`
   - **Target:** ≥70% pass rate
   - **ClickHouse Query:**
     ```sql
     SELECT 
       COUNT(DISTINCT CASE WHEN passed = 1 THEN document_id END) * 100.0 / 
       COUNT(DISTINCT document_id) as pass_rate
     FROM quality_metrics
     WHERE metric_type = 'text_quality' 
       AND metric_name IN ('char_repetition_ratio', 'word_repetition_ratio', 'ngram_repetition')
     ```
   - **dbt Model:** `fct_quality_scores` aggregates these metrics

**Storage:** All repetition metrics in `quality_metrics` table, aggregated in `fct_quality_scores`

### 1.3 Perplexity Metrics

**Purpose:** Measure text quality using language model perplexity (detect gibberish, low-quality content).

**Metrics:**

1. **Average Perplexity**
   - **Definition:** Mean perplexity score across all documents (lower = better quality)
   - **Formula:** `AVG(perplexity_score)`
   - **Interpretation:**
     - 50-500: Good quality text
     - 500-1000: Acceptable quality
     - >1000: Low quality (gibberish, spam)
   - **Threshold:** Documents with perplexity >1000 are filtered (see `configs/default.yaml`)
   - **ClickHouse Query:**
     ```sql
     SELECT 
       AVG(metric_value) as avg_perplexity,
       MIN(metric_value) as min_perplexity,
       MAX(metric_value) as max_perplexity,
       COUNT(CASE WHEN metric_value > 1000 THEN 1 END) as high_perplexity_count
     FROM quality_metrics
     WHERE metric_type = 'text_quality' 
       AND metric_name = 'perplexity'
     ```
   - **Storage:** `quality_metrics` table with `metric_name='perplexity'`

2. **Perplexity Distribution**
   - **Definition:** Percentiles of perplexity scores (P25, P50, P75, P95)
   - **Purpose:** Understand distribution of text quality
   - **ClickHouse Query:** Use quantile functions
     ```sql
     SELECT 
       quantile(0.25)(metric_value) as p25,
       quantile(0.50)(metric_value) as p50,
       quantile(0.75)(metric_value) as p75,
       quantile(0.95)(metric_value) as p95
     FROM quality_metrics
     WHERE metric_type = 'text_quality' AND metric_name = 'perplexity'
     ```
   - **dbt Model:** `fct_quality_scores` can pre-compute percentiles

3. **Perplexity Filter Pass Rate**
   - **Definition:** Percentage of documents with perplexity ≤1000
   - **Target:** ≥80% pass rate
   - **ClickHouse Query:**
     ```sql
     SELECT 
       COUNT(DISTINCT CASE WHEN metric_value <= 1000 THEN document_id END) * 100.0 / 
       COUNT(DISTINCT document_id) as pass_rate
     FROM quality_metrics
     WHERE metric_type = 'text_quality' AND metric_name = 'perplexity'
     ```

**Storage:** `quality_metrics` table, aggregated in `fct_quality_scores`

### 1.4 Overall Data Quality Score

**Purpose:** Composite score combining coverage, repetition, and perplexity metrics.

**Formula:**
```
data_quality_score = (
  coverage_score × 0.4 +      # Weight: 40%
  repetition_score × 0.3 +    # Weight: 30%
  perplexity_score × 0.3       # Weight: 30%
)

Where:
- coverage_score = min(combination_coverage / 0.10, 1.0)  # Normalize to 10% target
- repetition_score = repetition_pass_rate / 100.0
- perplexity_score = perplexity_pass_rate / 100.0
```

**Target:** ≥0.70 (70%) for MVP

**ClickHouse Query:** Combine queries from above sections

**Storage:** Computed metric in `fct_quality_scores` with `metric_type='data_quality'`, `metric_name='overall_score'`

## 2. Extraction Quality Evaluation

### 2.1 Gold Standard Dataset

**Purpose:** Create a small, manually annotated gold standard for evaluation.

**Gold Standard Creation:**
- **Size:** 20-30 documents (10% of corpus, minimum 20)
- **Selection:** Randomly sample documents, ensuring diversity across surface/dirt/method combinations
- **Annotation:** Manual annotation by domain expert or careful review
- **Fields Annotated:**
  - `surface_type` (ground truth)
  - `dirt_type` (ground truth)
  - `cleaning_method` (ground truth)
  - `tools` (ground truth list)
  - `steps` (ground truth list with order)

**Storage:** Separate table `gold_standard_documents` in ClickHouse:
```sql
CREATE TABLE gold_standard_documents (
  document_id String,
  surface_type_gt String,
  dirt_type_gt String,
  cleaning_method_gt String,
  tools_gt Array(String),
  steps_gt Array(String),
  annotated_at DateTime,
  annotator String
) ENGINE = MergeTree()
ORDER BY document_id;
```

### 2.2 Surface/Dirt/Method Accuracy

**Purpose:** Measure accuracy of normalized field extraction.

**Metrics:**

1. **Surface Type Accuracy**
   - **Definition:** Percentage of documents where extracted `surface_type` matches gold standard
   - **Formula:** `(correct_matches / total_documents) × 100`
   - **ClickHouse Query:**
     ```sql
     SELECT 
       COUNT(CASE WHEN rd.surface_type = gsd.surface_type_gt THEN 1 END) * 100.0 / 
       COUNT(*) as accuracy
     FROM gold_standard_documents gsd
     JOIN raw_documents rd ON gsd.document_id = rd.document_id
     ```
   - **Target:** ≥85% accuracy

2. **Dirt Type Accuracy**
   - **Definition:** Percentage of documents where extracted `dirt_type` matches gold standard
   - **Formula:** Same as above
   - **ClickHouse Query:** Similar to surface type
   - **Target:** ≥85% accuracy

3. **Cleaning Method Accuracy**
   - **Definition:** Percentage of documents where extracted `cleaning_method` matches gold standard
   - **Formula:** Same as above
   - **ClickHouse Query:** Similar to surface type
   - **Target:** ≥80% accuracy (methods can be more ambiguous)

4. **Combined Accuracy**
   - **Definition:** Percentage of documents where all three fields (surface, dirt, method) match
   - **Formula:** `(all_three_correct / total_documents) × 100`
   - **ClickHouse Query:**
     ```sql
     SELECT 
       COUNT(CASE 
         WHEN rd.surface_type = gsd.surface_type_gt 
          AND rd.dirt_type = gsd.dirt_type_gt 
          AND rd.cleaning_method = gsd.cleaning_method_gt 
         THEN 1 
       END) * 100.0 / COUNT(*) as combined_accuracy
     FROM gold_standard_documents gsd
     JOIN raw_documents rd ON gsd.document_id = rd.document_id
     ```
   - **Target:** ≥70% accuracy

**Storage:** Results stored in evaluation table or computed on-demand

**dbt Models:** Join `raw_documents` with `gold_standard_documents` (external table)

### 2.3 Tools Extraction Quality

**Purpose:** Measure accuracy of tool extraction.

**Metrics:**

1. **Tool Precision**
   - **Definition:** Percentage of extracted tools that are correct (in gold standard)
   - **Formula:** `(correct_extracted_tools / total_extracted_tools) × 100`
   - **ClickHouse Query:**
     ```sql
     SELECT 
       SUM(CASE WHEN t.tool_name = ANY(gsd.tools_gt) THEN 1 ELSE 0 END) * 100.0 / 
       COUNT(*) as precision
     FROM tools t
     JOIN gold_standard_documents gsd ON t.document_id = gsd.document_id
     ```

2. **Tool Recall**
   - **Definition:** Percentage of gold standard tools that were extracted
   - **Formula:** `(extracted_gold_tools / total_gold_tools) × 100`
   - **ClickHouse Query:** Requires array operations to count matches
   - **Target:** ≥70% recall (some tools may be implicit)

3. **Tool F1 Score**
   - **Definition:** Harmonic mean of precision and recall
   - **Formula:** `2 × (precision × recall) / (precision + recall)`
   - **Target:** ≥0.70 F1 score

4. **Tool Extraction Coverage**
   - **Definition:** Percentage of documents with at least one tool extracted
   - **Formula:** `(documents_with_tools / total_documents) × 100`
   - **ClickHouse Query:**
     ```sql
     SELECT 
       COUNT(DISTINCT t.document_id) * 100.0 / 
       COUNT(DISTINCT gsd.document_id) as coverage
     FROM gold_standard_documents gsd
     LEFT JOIN tools t ON gsd.document_id = t.document_id
     ```
   - **Target:** ≥90% coverage

**Storage:** `tools` table joined with `gold_standard_documents`

**dbt Models:** `fct_tool_usage` can be used for aggregation

### 2.4 Steps Extraction Quality

**Purpose:** Measure accuracy of step extraction and ordering.

**Metrics:**

1. **Step Precision**
   - **Definition:** Percentage of extracted steps that are semantically correct (manual review or semantic similarity)
   - **Formula:** `(correct_steps / total_extracted_steps) × 100`
   - **Method:** Manual review or semantic similarity (embedding-based) against gold standard
   - **Target:** ≥75% precision

2. **Step Recall**
   - **Definition:** Percentage of gold standard steps that were extracted
   - **Formula:** `(extracted_gold_steps / total_gold_steps) × 100`
   - **Method:** Semantic matching (not exact string match, as wording may differ)
   - **Target:** ≥70% recall

3. **Step Order Accuracy**
   - **Definition:** For documents where steps are extracted, measure if order matches gold standard
   - **Formula:** Use Kendall's tau or Spearman correlation for step order
   - **Method:** Compare `step_order` in `steps` table with gold standard order
   - **ClickHouse Query:** Requires step-by-step comparison
   - **Target:** ≥0.60 correlation (some reordering acceptable)

4. **Step Extraction Coverage**
   - **Definition:** Percentage of documents with at least one step extracted
   - **Formula:** `(documents_with_steps / total_documents) × 100`
   - **ClickHouse Query:**
     ```sql
     SELECT 
       COUNT(DISTINCT s.document_id) * 100.0 / 
       COUNT(DISTINCT gsd.document_id) as coverage
     FROM gold_standard_documents gsd
     LEFT JOIN steps s ON gsd.document_id = s.document_id
     ```
   - **Target:** ≥85% coverage

**Storage:** `steps` table joined with `gold_standard_documents`

**dbt Models:** `fct_step_sequences` can be used for ordering analysis

### 2.5 Extraction Method Comparison

**Purpose:** Compare different extraction methods (rule_based, ner, llm).

**Metrics:**

1. **Method-Specific Accuracy**
   - **Definition:** Accuracy metrics broken down by `extraction_method`
   - **ClickHouse Query:**
     ```sql
     SELECT 
       rd.extraction_method,
       COUNT(CASE WHEN rd.surface_type = gsd.surface_type_gt THEN 1 END) * 100.0 / 
       COUNT(*) as surface_accuracy
     FROM gold_standard_documents gsd
     JOIN raw_documents rd ON gsd.document_id = rd.document_id
     GROUP BY rd.extraction_method
     ```

2. **Confidence Calibration**
   - **Definition:** Check if `extraction_confidence` correlates with actual accuracy
   - **Method:** Group by confidence bins (0-0.5, 0.5-0.7, 0.7-0.9, 0.9-1.0) and measure accuracy in each bin
   - **Target:** Higher confidence should correlate with higher accuracy

**Storage:** `raw_documents.extraction_method`, `raw_documents.extraction_confidence`

**dbt Models:** `stg_documents` includes extraction metadata

## 3. Planner Quality Evaluation

### 3.1 Step Coverage

**Purpose:** Measure how well agent-generated workflows cover the steps from reference corpus procedures.

**Metrics:**

1. **Step Coverage Ratio**
   - **Definition:** Percentage of reference corpus steps that appear (semantically) in generated workflow
   - **Formula:** `(covered_reference_steps / total_reference_steps) × 100`
   - **Method:**
     1. For a given query (surface, dirt, method), retrieve top 3-5 reference documents from corpus
     2. Extract all steps from reference documents (from `steps` table)
     3. Compare agent-generated workflow steps against reference steps using semantic similarity
     4. Count how many reference steps are covered
   - **ClickHouse Query:** Query `steps` table for reference procedures
     ```sql
     SELECT step_text, step_order
     FROM steps s
     JOIN raw_documents rd ON s.document_id = rd.document_id
     WHERE rd.surface_type = ? 
       AND rd.dirt_type = ? 
       AND rd.cleaning_method = ?
     ORDER BY rd.extraction_confidence DESC
     LIMIT 50
     ```
   - **Target:** ≥60% step coverage (agent may combine/summarize steps)

2. **Critical Step Coverage**
   - **Definition:** Coverage of critical steps (safety steps, preparation steps, final steps)
   - **Method:** Manually identify critical steps in reference procedures, measure coverage
   - **Target:** ≥80% critical step coverage

3. **Step Completeness**
   - **Definition:** Whether generated workflow has minimum required steps (prep, action, cleanup)
   - **Method:** Check if workflow contains at least one step from each category
   - **Target:** 100% completeness (all categories present)

**Reference Data:** `steps` table, `fct_step_sequences` for ordering

**Agent Output:** `workflow.steps` array from agent response (see `WORKFLOW_AGENT_DESIGN.md`)

### 3.2 Tool Correctness

**Purpose:** Measure accuracy of tools recommended in generated workflows.

**Metrics:**

1. **Tool Precision**
   - **Definition:** Percentage of tools in generated workflow that are correct (appear in reference corpus)
   - **Formula:** `(correct_tools / total_generated_tools) × 100`
   - **Method:**
     1. Extract tools from agent-generated workflow (`workflow.required_tools`)
     2. Query `fct_tool_usage` for reference tools for the same combination
     3. Count matches
   - **ClickHouse Query:**
     ```sql
     SELECT tool_name, usage_count
     FROM fct_tool_usage
     WHERE surface_key = ? 
       AND dirt_key = ? 
       AND method_key = ?
     ORDER BY usage_count DESC
     ```
   - **Target:** ≥80% precision (tools should be grounded in corpus)

2. **Tool Recall**
   - **Definition:** Percentage of reference corpus tools that appear in generated workflow
   - **Formula:** `(generated_reference_tools / total_reference_tools) × 100`
   - **Target:** ≥70% recall (agent may omit some optional tools)

3. **Tool Category Accuracy**
   - **Definition:** Accuracy of tool categorization (chemical, equipment, consumable, safety)
   - **Method:** Compare `tool.category` in agent output with `dim_tool.tool_category`
   - **Target:** ≥90% category accuracy

4. **Required vs Optional Tool Classification**
   - **Definition:** Accuracy of `is_required` flag in agent output
   - **Method:** Compare with tool usage frequency in corpus (high frequency = likely required)
   - **Target:** ≥75% classification accuracy

**Reference Data:** `fct_tool_usage`, `dim_tool`

**Agent Output:** `workflow.required_tools` array (see `WORKFLOW_AGENT_DESIGN.md`)

### 3.3 Constraint Adherence

**Purpose:** Measure how well agent respects user constraints.

**Metrics:**

1. **Constraint Violation Rate**
   - **Definition:** Percentage of workflows that violate user-specified constraints
   - **Formula:** `(violations / total_workflows) × 100`
   - **Constraints to Check:**
     - `no_bleach`: Workflow should not include bleach
     - `no_harsh_chemicals`: Workflow should use gentle methods
     - `gentle_only`: No scrubbing, minimal chemicals
     - `preferred_method`: Should use specified method if available
   - **Method:**
     1. Extract constraints from agent input (see `WORKFLOW_AGENT_DESIGN.md` input schema)
     2. Check agent output against constraints:
       - `no_bleach`: Check if "bleach" appears in `workflow.required_tools` or `workflow.steps`
       - `no_harsh_chemicals`: Check if harsh chemicals (bleach, ammonia) appear
       - `gentle_only`: Check if `workflow.difficulty` is "hard" or if "scrub" method used
       - `preferred_method`: Check if `scenario.cleaning_method` matches preferred
   - **Target:** ≤5% violation rate

2. **Constraint Satisfaction Score**
   - **Definition:** For each constraint, measure satisfaction rate
   - **Formula:** `(satisfied_constraints / total_constraints) × 100`
   - **Target:** ≥95% satisfaction rate

**Agent Input:** `constraints` object (see `WORKFLOW_AGENT_DESIGN.md`)

**Agent Output:** `workflow` object (see `WORKFLOW_AGENT_DESIGN.md`)

### 3.4 Workflow Quality Metrics

**Purpose:** Measure overall quality of generated workflows.

**Metrics:**

1. **Workflow Completeness**
   - **Definition:** Whether workflow has all required components
   - **Components:**
     - At least 3 steps
     - At least 1 required tool
     - Safety notes (if applicable)
     - Estimated duration
   - **Target:** 100% completeness

2. **Workflow Coherence**
   - **Definition:** Logical flow of steps (prep → action → cleanup)
   - **Method:** Manual review or rule-based checking:
     - First step should be preparation (blot, mix, prepare)
     - Middle steps should be actions (apply, scrub, vacuum)
     - Last step should be cleanup/finish (dry, rinse, final check)
   - **Target:** ≥80% coherence

3. **Source Grounding**
   - **Definition:** Whether workflow is grounded in corpus (not hallucinated)
   - **Method:** Check if `source_documents` array is non-empty and documents exist in corpus
   - **ClickHouse Query:** Verify `source_documents[].document_id` exists in `raw_documents`
   - **Target:** 100% grounding (all workflows must have source documents)

4. **Confidence Calibration**
   - **Definition:** Correlation between `metadata.confidence` and actual quality
   - **Method:** Measure quality metrics (step coverage, tool correctness) vs confidence scores
   - **Target:** Higher confidence should correlate with higher quality

**Agent Output:** Full workflow object (see `WORKFLOW_AGENT_DESIGN.md` output schema)

### 3.5 Evaluation Dataset

**Purpose:** Create test set for planner evaluation.

**Test Set Creation:**
- **Size:** 20-30 diverse queries
- **Selection Criteria:**
  - 10 queries with exact corpus matches (high coverage)
  - 10 queries with partial matches (medium coverage)
  - 5-10 queries with no matches (low coverage, test fallback)
- **Query Types:**
  - Simple queries (single surface, single dirt)
  - Complex queries (multiple constraints)
  - Edge cases (rare combinations, conflicting constraints)

**Storage:** Test queries stored in `evaluation_queries` table:
```sql
CREATE TABLE evaluation_queries (
  query_id String,
  query_text String,
  expected_surface_type String,
  expected_dirt_type String,
  expected_method String,
  constraints String,  -- JSON string
  expected_steps Array(String),
  expected_tools Array(String),
  created_at DateTime
) ENGINE = MergeTree()
ORDER BY query_id;
```

## 4. Evaluation Implementation

### 4.1 Evaluation Scripts

**Location:** `src/evaluation/`

**Scripts:**

1. **`evaluate_data_quality.py`**
   - Computes coverage, repetition, perplexity metrics
   - Queries ClickHouse warehouse
   - Outputs: JSON report, text summary

2. **`evaluate_extraction_quality.py`**
   - Compares extracted fields against gold standard
   - Computes accuracy, precision, recall for surface/dirt/method/tools/steps
   - Outputs: JSON report with per-field metrics

3. **`evaluate_planner_quality.py`**
   - Tests workflow planner agent on evaluation queries
   - Computes step coverage, tool correctness, constraint adherence
   - Outputs: JSON report with per-query and aggregate metrics

### 4.2 Evaluation Schedule

**Automated Evaluation:**
- **Data Quality:** Run after each corpus update (crawl + process)
- **Extraction Quality:** Run when extraction method changes or gold standard updated
- **Planner Quality:** Run weekly or when agent prompts/tools change

**Manual Evaluation:**
- **Gold Standard Creation:** One-time, then incremental updates
- **Workflow Review:** Sample 10% of generated workflows for manual quality check

### 4.3 Reporting

**Output Formats:**
- **JSON:** Machine-readable metrics for tracking over time
- **Text Report:** Human-readable summary
- **Visualizations:** Charts for trends (coverage over time, accuracy by method)

**Storage:** Evaluation results stored in `evaluation_results` table:
```sql
CREATE TABLE evaluation_results (
  evaluation_id String,
  evaluation_type String,  -- 'data_quality', 'extraction_quality', 'planner_quality'
  metrics String,  -- JSON string with all metrics
  computed_at DateTime,
  corpus_version String  -- Link to corpus snapshot
) ENGINE = MergeTree()
ORDER BY (evaluation_type, computed_at);
```

## 5. Success Criteria

### MVP Targets

**Data Quality:**
- Combination coverage: ≥10% (50+ unique combinations)
- Repetition pass rate: ≥70%
- Perplexity pass rate: ≥80%
- Overall data quality score: ≥0.70

**Extraction Quality:**
- Surface/dirt/method combined accuracy: ≥70%
- Tool F1 score: ≥0.70
- Step extraction coverage: ≥85%
- Step order correlation: ≥0.60

**Planner Quality:**
- Step coverage: ≥60%
- Tool precision: ≥80%
- Constraint violation rate: ≤5%
- Source grounding: 100%

### Long-term Targets

**Data Quality:**
- Combination coverage: ≥30% (150+ unique combinations)
- Overall data quality score: ≥0.85

**Extraction Quality:**
- Combined accuracy: ≥85%
- Tool F1 score: ≥0.85
- Step order correlation: ≥0.80

**Planner Quality:**
- Step coverage: ≥75%
- Tool precision: ≥90%
- Constraint violation rate: ≤2%

## 6. Links to Design Documents

### Data Warehouse Models

- **Coverage Metrics:** `fct_cleaning_procedures` (see `DATA_WAREHOUSE.md`)
- **Quality Metrics:** `quality_metrics` table, `fct_quality_scores` (see `DATA_WAREHOUSE.md`)
- **Tool Usage:** `fct_tool_usage` (see `DATA_WAREHOUSE.md`)
- **Step Sequences:** `fct_step_sequences` (see `DATA_WAREHOUSE.md`)

### Agent Design

- **Input Schema:** See `WORKFLOW_AGENT_DESIGN.md` - Input Schema section
- **Output Schema:** See `WORKFLOW_AGENT_DESIGN.md` - Output Schema section
- **Planning Strategy:** See `WORKFLOW_AGENT_DESIGN.md` - Planning Strategy section
- **Agent Tools:** See `WORKFLOW_AGENT_DESIGN.md` - Conceptual Tools section

### Configuration

- **Quality Filter Thresholds:** See `configs/default.yaml` - `quality` section
- **Extraction Methods:** See `configs/default.yaml` - `enrichment` section


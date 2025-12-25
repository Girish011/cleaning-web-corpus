# System Architecture

## Overview

The Cleaning Workflow Planner Platform is a research-grade system that transforms unstructured web content into structured, queryable cleaning knowledge for LLM agents and robots. The architecture follows a data pipeline pattern: **crawler → processing → warehouse → agent → API**.

```
┌─────────────┐
│   Web URLs  │
│ (seed.txt)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: DATA COLLECTION & PROCESSING                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │   Scrapy     │────────▶│  Text Processor  │        │
│  │   Crawler    │         │  + Enrichment     │        │
│  │              │         │  + Quality Filters│        │
│  └──────────────┘         └────────┬─────────┘        │
│                                    │                    │
│                                    ▼                    │
│                          ┌──────────────────┐          │
│                          │ cleaning_docs    │          │
│                          │ .jsonl           │          │
│                          └──────────────────┘          │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: DATA WAREHOUSE (ClickHouse + dbt)            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │  ClickHouse  │◀────────│   dbt Models     │        │
│  │   (Raw)      │         │   (Transform)     │        │
│  │              │         │                   │        │
│  │ - raw_docs   │         │ - staging         │        │
│  │ - steps      │         │ - dimensions      │        │
│  │ - tools      │         │ - facts           │        │
│  │ - quality    │         └───────────────────┘        │
│  └──────┬───────┘                                      │
│         │                                               │
│         ▼                                               │
│  ┌──────────────┐                                      │
│  │  Analytical  │                                      │
│  │   Views      │                                      │
│  │  (Materialized)                                     │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: WORKFLOW PLANNER AGENT (LangChain)           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │   LLM        │         │  Agent Tools      │        │
│  │  (GPT-4/     │         │                   │        │
│  │   Claude)    │         │ - fetch_methods   │        │
│  └──────┬───────┘         │ - fetch_steps     │        │
│         │                │ - fetch_tools     │        │
│         │                │ - fetch_context  │        │
│         └───────────────▶│ - search_similar  │        │
│                          └────────┬───────────┘        │
│                                   │                     │
│                                   ▼                     │
│                          ┌──────────────────┐           │
│                          │  ClickHouse      │           │
│                          │  Queries         │           │
│                          └──────────────────┘           │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 4: API LAYER (FastAPI)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │   FastAPI    │────────▶│  Workflow Agent   │        │
│  │   Server     │         │  (LangChain)      │        │
│  │              │         │                   │        │
│  │ /plan_workflow        │                   │        │
│  │ /search_procedures    │                   │        │
│  │ /stats/coverage       │                   │        │
│  └──────────────┘         └───────────────────┘        │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Clients   │
│ (Robots/    │
│  Agents)    │
└─────────────┘
```

## Component Details

### Phase 1: Data Collection & Processing

#### 1.1 Scrapy Crawler (`src/crawlers/`)

**Purpose:** Crawl web pages from seed URLs and extract raw HTML, images, and metadata.

**Components:**
- `seed_spider.py` - Main spider for crawling seed URLs
- `search_discovery.py` - Optional search engine-based URL discovery
- `pipelines.py` - Image download and metadata extraction
- `items.py` - Data structures for crawled items

**Output:** `data/raw/seed_pages.jsonl` - Raw crawled data with:
- URL, title, HTML
- Image URLs and metadata
- Video URLs
- HTTP status codes

**Data Flow:**
```
Seed URLs (data/seeds.txt)
    ↓
Scrapy Spider
    ↓
Raw JSONL (data/raw/seed_pages.jsonl)
```

#### 1.2 Text Processor (`src/processors/text_processor.py`)

**Purpose:** Extract main text from HTML, apply quality filters, and prepare documents for enrichment.

**Components:**
- HTML → text extraction (trafilatura)
- Text quality filters (`src/quality/text_filters.py`):
  - Length filters (min/max words)
  - Repetition detection
  - Perplexity filtering (KenLM)
  - Language detection
- Image quality filters (`src/quality/image_filters.py`):
  - Resolution checks
  - Format validation
  - Duplicate detection
- CLIP alignment scoring (`src/quality/alignment.py`):
  - Text-image semantic relevance

**Output:** Filtered documents ready for enrichment

**Data Flow:**
```
Raw JSONL (data/raw/seed_pages.jsonl)
    ↓
Text Extraction
    ↓
Quality Filters (text + image)
    ↓
Filtered Documents
```

#### 1.3 Enrichment Pipeline (`src/enrichment/`)

**Purpose:** Extract structured information from cleaned text.

**Components:**
- `enricher.py` - Main enrichment orchestrator
- `extractors.py` - Rule-based extraction (Phase 4.1)
- `ner_extractor.py` - NER-based extraction (Phase 4.2)
- `llm_extractor.py` - LLM-based extraction (Phase 4.2)
- `captioner.py` - Image captioning (Phase 4.3)

**Extracted Fields:**
- `surface_type` - Normalized surface category (8 types)
- `dirt_type` - Normalized dirt category (8 types)
- `cleaning_method` - Normalized method (8 methods)
- `tools` - List of cleaning tools/equipment
- `steps` - List of cleaning procedure steps
- `extraction_metadata` - Confidence scores, method used

**Output:** `data/processed/cleaning_docs.jsonl` - Enriched documents

**Data Flow:**
```
Filtered Documents
    ↓
Enrichment Pipeline
    ↓
Structured Extraction (surface, dirt, method, tools, steps)
    ↓
Enriched JSONL (data/processed/cleaning_docs.jsonl)
```

### Phase 2: Data Warehouse (ClickHouse + dbt)

#### 2.1 ClickHouse Database

**Purpose:** Analytical database for fast queries on structured cleaning knowledge.

**Tables (see `DATA_WAREHOUSE.md` for full schema):**

1. **`raw_documents`** - Core document storage
   - Primary key: `document_id`
   - Contains: URL, title, text, metadata, normalized fields (surface, dirt, method)
   - Indexed on: `(surface_type, dirt_type, cleaning_method)`, `fetched_at`

2. **`steps`** - Individual cleaning steps
   - Primary key: `step_id`
   - Foreign key: `document_id`
   - Contains: step text, order, confidence, extraction method

3. **`tools`** - Cleaning tools/equipment
   - Primary key: `tool_id`
   - Foreign key: `document_id`
   - Contains: tool name, category, confidence, step associations

4. **`quality_metrics`** - Quality scores and filter results
   - Primary key: `metric_id`
   - Foreign key: `document_id`
   - Contains: metric type, value, pass/fail status

**Data Flow:**
```
Enriched JSONL (data/processed/cleaning_docs.jsonl)
    ↓
ETL Script (loads into ClickHouse)
    ↓
ClickHouse Raw Tables
    (raw_documents, steps, tools, quality_metrics)
```

#### 2.2 dbt Transformations

**Purpose:** Transform raw data into analytical models (staging → dimensions → facts).

**Model Layers:**

1. **Sources** (`sources/`)
   - Define external data sources (ClickHouse tables)
   - `source_raw_documents`, `source_steps`, `source_tools`, `source_quality_metrics`

2. **Staging** (`staging/`)
   - Clean and normalize raw data
   - `stg_documents`, `stg_steps`, `stg_tools`, `stg_quality_metrics`

3. **Dimensions** (`dimensions/`)
   - Dimension tables for analytical queries
   - `dim_surface`, `dim_dirt`, `dim_method`, `dim_tool`, `dim_document`

4. **Facts** (`facts/`)
   - Fact tables for aggregations
   - `fct_cleaning_procedures` - Coverage analysis (surface × dirt × method)
   - `fct_tool_usage` - Tool usage patterns
   - `fct_step_sequences` - Step ordering analysis
   - `fct_quality_scores` - Quality trend analysis

**Data Flow:**
```
ClickHouse Raw Tables
    ↓
dbt Sources (define external tables)
    ↓
dbt Staging (clean & normalize)
    ↓
dbt Dimensions (create dimension tables)
    ↓
dbt Facts (create fact tables)
    ↓
Analytical Views (materialized in ClickHouse)
```

**Connection to Agent:**
- Agent tools query dbt models (via ClickHouse materialized views)
- Fast analytical queries for `fetch_methods`, `fetch_steps`, `fetch_tools`
- Pre-aggregated coverage matrices for `search_similar_scenarios`

### Phase 3: Workflow Planner Agent (LangChain)

#### 3.1 Agent Architecture

**Purpose:** Generate structured cleaning workflows from natural language queries.

**Components:**
- **LangChain Agent** - Orchestrates tool calls and LLM reasoning
- **LLM** - GPT-4, Claude, or local model for query parsing and workflow composition
- **Agent Tools** - LangChain tools that wrap ClickHouse queries

**Agent Tools (see `WORKFLOW_AGENT_DESIGN.md`):**

1. **`fetch_methods`**
   - Queries: `fct_cleaning_procedures` (via ClickHouse)
   - Returns: Available cleaning methods for surface × dirt combination

2. **`fetch_steps`**
   - Queries: `steps` table joined with `raw_documents` (via ClickHouse)
   - Returns: Ordered cleaning steps for a specific combination

3. **`fetch_tools`**
   - Queries: `fct_tool_usage` (via ClickHouse)
   - Returns: Recommended tools with usage counts and confidence

4. **`fetch_reference_context`**
   - Queries: `raw_documents` with joins to `steps` and `tools` (via ClickHouse)
   - Returns: Full document context for citation

5. **`search_similar_scenarios`**
   - Queries: Coverage matrices and similarity search (via ClickHouse)
   - Returns: Similar combinations when exact match unavailable

**Planning Strategy (4-phase):**

1. **Parse & Normalize** - Extract and normalize surface/dirt/method from query
2. **Fetch & Retrieve** - Call tools to get relevant procedures from warehouse
3. **Compose & Generate** - Use LLM to create structured workflow from retrieved data
4. **Validate & Refine** - Check completeness, constraints, quality

**Data Flow:**
```
User Query (natural language)
    ↓
Agent: Parse & Normalize
    ↓
Agent Tools → ClickHouse Queries
    ↓
Retrieved Procedures (steps, tools, documents)
    ↓
Agent: Compose & Generate (LLM)
    ↓
Structured Workflow (JSON)
```

**Connection to Warehouse:**
- Agent tools use ClickHouse client (`src/db/clickhouse_client.py`)
- Queries target dbt materialized views for performance
- All data is grounded in corpus (no hallucination)

### Phase 4: API Layer (FastAPI)

#### 4.1 FastAPI Server (`src/api/`)

**Purpose:** HTTP API for accessing workflow planning and corpus search.

**Endpoints (see `API_DESIGN.md` for full specs):**

1. **`POST /plan_workflow`**
   - Input: Natural language query + optional constraints
   - Calls: Workflow Planner Agent
   - Returns: Structured workflow plan

2. **`GET /search_procedures`**
   - Input: Filters (surface, dirt, method)
   - Queries: ClickHouse directly (or via agent tools)
   - Returns: Matching procedures from corpus

3. **`GET /stats/coverage`**
   - Input: Optional filters
   - Queries: `fct_cleaning_procedures` (via ClickHouse)
   - Returns: Coverage statistics and matrices

**Data Flow:**
```
HTTP Request
    ↓
FastAPI Router
    ↓
Endpoint Handler
    ↓
Workflow Agent (for /plan_workflow)
    OR
ClickHouse Query (for /search_procedures, /stats/coverage)
    ↓
HTTP Response (JSON)
```

**Connection to Agent:**
- `/plan_workflow` endpoint instantiates and calls Workflow Planner Agent
- Agent returns structured workflow, API formats as HTTP response
- Error handling and validation at API layer

## Data Flow Summary

### End-to-End Flow

```
1. Web URLs (seeds.txt)
   ↓
2. Scrapy Crawler
   → data/raw/seed_pages.jsonl
   ↓
3. Text Processor + Enrichment
   → data/processed/cleaning_docs.jsonl
   ↓
4. ETL to ClickHouse
   → raw_documents, steps, tools, quality_metrics tables
   ↓
5. dbt Transformations
   → staging → dimensions → facts
   ↓
6. Materialized Views (ClickHouse)
   → Fast analytical queries
   ↓
7. Agent Tools (LangChain)
   → Query warehouse for procedures
   ↓
8. Workflow Planner Agent
   → Generate structured workflows
   ↓
9. FastAPI Endpoints
   → Expose workflows via HTTP
   ↓
10. Clients (Robots/Agents)
    → Use structured workflows
```

### Query Flow (User Request)

```
User: "Remove red wine stain from wool carpet"
   ↓
FastAPI: POST /plan_workflow
   ↓
Agent: Parse query → surface="carpets_floors", dirt="stain"
   ↓
Agent Tool: fetch_methods(surface="carpets_floors", dirt="stain")
   → ClickHouse Query → Returns: ["spot_clean", "steam_clean"]
   ↓
Agent: Select method="spot_clean" (highest document count)
   ↓
Agent Tool: fetch_steps(surface, dirt, method="spot_clean")
   → ClickHouse Query → Returns: [25 steps from 5 documents]
   ↓
Agent Tool: fetch_tools(surface, dirt, method="spot_clean")
   → ClickHouse Query → Returns: ["vinegar", "paper_towels", ...]
   ↓
Agent: Compose workflow (LLM) using retrieved data
   ↓
Agent: Return structured workflow JSON
   ↓
FastAPI: Return HTTP 200 with workflow
```

## Component Dependencies

```
FastAPI
  └─→ Workflow Planner Agent (LangChain)
        └─→ Agent Tools
              └─→ ClickHouse Client (src/db/)
                    └─→ ClickHouse Database
                          └─→ dbt Models (materialized views)

FastAPI
  └─→ ClickHouse Client (for /search_procedures, /stats/coverage)
        └─→ ClickHouse Database

Pipeline Orchestrator
  └─→ Scrapy Crawler
  └─→ Text Processor
        └─→ Enrichment Pipeline
              └─→ Extractors (rule_based, ner, llm)
  └─→ ETL Script
        └─→ ClickHouse Database
```

## Technology Stack

- **Crawler:** Scrapy (Python)
- **Processing:** Python (trafilatura, spaCy, transformers)
- **Database:** ClickHouse (analytical DB)
- **Transformations:** dbt (data modeling)
- **Agent:** LangChain (Python) + LLM (GPT-4/Claude/local)
- **API:** FastAPI (Python)
- **Storage:** JSONL files (intermediate), ClickHouse (warehouse)

## Directory Structure

```
src/
├── crawlers/          # Scrapy spiders and pipelines
├── processors/        # Text extraction and quality filters
├── enrichment/        # Structured extraction (tools, steps)
├── quality/          # Quality filters (text, image, alignment)
├── evaluation/       # Dataset statistics and analysis
├── pipeline/         # Orchestrator for end-to-end pipeline
├── db/               # ClickHouse client and dbt integration
├── agents/           # Workflow Planner Agent (LangChain)
└── api/              # FastAPI server and endpoints

dbt/
├── models/
│   ├── sources/      # Source definitions
│   ├── staging/      # Staging models
│   ├── dimensions/   # Dimension models
│   └── facts/        # Fact models
└── dbt_project.yml

data/
├── raw/              # Raw crawled data (JSONL)
├── processed/       # Enriched data (JSONL)
└── evaluation/      # Statistics and visualizations
```

## Key Design Principles

1. **Data Grounding:** All agent outputs are grounded in corpus data (no hallucination)
2. **Analytical First:** Warehouse optimized for analytical queries, not transactional
3. **Modular Components:** Clear boundaries between crawler, processor, warehouse, agent, API
4. **Research-Grade:** Designed for research and portfolio, not commercial SaaS
5. **Extensible:** Easy to add new extraction methods, tools, or endpoints


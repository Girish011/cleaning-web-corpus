Product Overview
Product name (working): Cleaning Workflow Planner Platform
Type: Research-grade knowledge + planning platform for cleaning workflows
Primary users (initial focus):

AI/robotics engineers who need structured cleaning procedures for agents/robots.

AI engineers (Apollo-like roles) who want a realistic LLM agent + data infra reference project.

Core idea:
A domain-specific platform that:

Crawls and cleans the web for cleaning knowledge.

Normalizes it into a structured corpus (surface, dirt, method, tools, steps).

Stores it in an analytical warehouse (ClickHouse + dbt).

Exposes a workflow-planner agent (LangChain) and API (FastAPI) for planning cleaning procedures.

Problem Statement
Unstructured web content on cleaning is:

Redundant and inconsistent.

Hard for robots/agents to use directly.

Lacking a standardized schema for “surface × dirt × method × steps × tools.”

AI roles and robotics teams need:

A clean, structured, queryable dataset of cleaning procedures.

A reference workflow planner agent grounded in that data.

A production-like stack (data pipelines, warehouse, API, LLM agents) to study or build upon.

Goals & Non-Goals
Goals

Build a structured corpus of ≥50 high-quality cleaning documents with:

surface_type, dirt_type, cleaning_method, tools, steps.
​

Design and implement a data warehouse model using ClickHouse + dbt.

Design and implement a workflow planner agent that:

Takes natural-language cleaning scenarios.

Returns structured workflows suitable for robots/agents.

Expose a FastAPI service with endpoints for:

planning workflows

retrieving procedures

basic stats

Provide evaluation hooks and metrics for planning quality.

Non-Goals (for now)

Full commercial SaaS for hotels or janitorial businesses.

Complex user management, billing, or multi-tenant features.

Real robot integration (no ROS, no simulators inside this repo).

Target Users & Use Cases
User segments

AI/LLM engineers (job-oriented)

Need a portfolio project that demonstrates:

LLM agents

data warehousing

backend APIs

Robotics / research engineers (future)

Need a domain-specific workflow corpus and planner.

Primary use cases

Plan a cleaning workflow for a scenario

Input: “Red wine on wool carpet in a living room, no bleach.”

Output: normalized surface/dirt, method, steps, tools, safety notes.

Query procedures by surface/dirt/method

Input filters: surface_type=“carpet”, dirt_type=“stain”.

Output: candidate procedures from corpus.

Analyze corpus coverage and quality

Get stats and visualizations of coverage over surfaces/dirt/method combinations.
​

Core Features (MVP)
Corpus Expansion & Processing

≥50 documents in data/processed/cleaning_docs.jsonl.

Enrichment fields present: surface_type, dirt_type, cleaning_method, tools, steps, quality metrics.
​

Data Warehouse (ClickHouse + dbt)

Logical table design:

documents, steps, tools, quality_metrics.

dbt models:

staging models.

dims (dim_surface, dim_dirt, dim_method, dim_tool).

facts (fct_cleaning_procedures, fct_tool_usage).

Basic tests & docs (even if minimal).

Workflow Planner Agent

Agent design:

input/output schemas

tools that query ClickHouse

reasoning strategy (parse → fetch → compose).

Prompts with 2–3 few-shot examples.

FastAPI Service

/plan_workflow – plans a workflow based on user scenario.

/search_procedures – returns corpus procedures by filters.

/stats/coverage – returns high-level coverage metrics.

Evaluation & Research Hooks

Evaluation plan document.

A few defined metrics for:

step coverage vs corpus.

tool correctness.

Success Metrics
For MVP:

Corpus:

total_documents >= 50.
​

coverage_summary.total_combinations increased beyond current 5.
​

Data warehouse:

dbt project with at least:

4 dim models.

2 fact models.

Agent:

Can return a structured plan for at least 5 manually-tested scenarios.

API:

Local FastAPI server with working endpoints.

Documentation:

PRD, DATA_WAREHOUSE.md, WORKFLOW_AGENT_DESIGN.md, API_DESIGN.md.
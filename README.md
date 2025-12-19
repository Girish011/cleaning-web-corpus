# cleaning-web-corpus

Domain-specific web crawling and data ingestion pipeline for household dirt, dust, stains, and cleaning knowledge.  
The goal is to build a research-grade corpus and pipeline that can support LLM agents and cleaning robots with structured cleaning knowledge.

## Overview

- Multi-domain **web crawler** (Scrapy) targeting cleaning-related content (pillows, clothes, carpets, sofas).
- **Processing pipeline** to extract main article text (trafilatura), apply quality filters, and store structured JSONL.
- **Domain-aware tagging** (surface_type, dirt_type, cleaning_method) using heuristic rules.
- **Analysis tools** to inspect distributions and tag co-occurrences (e.g., dirt_type × cleaning_method).
- Extensible design for **multi-modal data** (image/video URLs, future robot sensor traces).

## Quickstart

1. Create and activate a virtual environment:

python3 -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate


2. Install dependencies:

pip install -r requirements.txt

3. Run the crawler (from repo root):

cd crawler_project
scrapy crawl seed_spider -O ../data/raw/seed_pages.jsonl
cd ..

4. Run the processing pipeline:

python pipeline/process_seed_pages.py

5. Run the analysis:

python analysis/describe_corpus.py

## Repository structure

cleaning-web-corpus/
crawler/ # Seed URLs and (later) search-guided seeds
crawler_project/ # Scrapy project (spiders, settings)
data/
raw/ # Raw crawl outputs (JSONL)
processed/ # Processed, tagged corpus (JSONL)
pipeline/ # HTML → text extraction, tagging, filters
analysis/ # Stats scripts and experiment reports
DATASET_CARD.md # Dataset card and intended uses
requirements.txt
README.md


## Dataset and pipeline

- See **DATASET_CARD.md** for a detailed description of:
  - Motivation and intended uses.
  - Schema and fields.
  - Known limitations and future extensions.

## Experiments

- **Experiment A – Seed targeting & coverage**:  
  Analyze how adding targeted seeds changes tag distributions and dirt_type × cleaning_method coverage.

- **Experiment B – Length-based quality filtering**:  
  Study how different minimum length thresholds affect corpus size and quality.

(Experiment reports live under `analysis/experiments/`.)

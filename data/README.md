# Data Directory

This directory contains crawled and processed data for the cleaning corpus pipeline.

## Structure

- `seeds.txt` - Seed URLs for crawling
- `raw/` - Raw crawled JSONL files (gitignored)
- `processed/` - Processed and filtered JSONL files (gitignored)
- `images/` - Downloaded images organized by domain/page_id (gitignored)

## Usage

The pipeline expects:
- `data/raw/seed_pages.jsonl` - Output from the crawler
- `data/processed/cleaning_docs.jsonl` - Output from the text processor

Images will be stored in `data/images/` when image downloading is implemented.

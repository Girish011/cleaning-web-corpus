"""
ETL script to load data from cleaning_docs.jsonl into ClickHouse tables.

This script reads processed documents from data/processed/cleaning_docs.jsonl,
transforms them to match ClickHouse table schemas, and performs batch inserts
into raw_documents, steps, tools, and quality_metrics tables.
"""

import sys
import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.clickhouse_client import ClickHouseClient
from src.db.schema import (
    create_raw_documents_table,
    create_steps_table,
    create_tools_table,
    create_quality_metrics_table,
)

logger = logging.getLogger(__name__)


def generate_document_id(url: str) -> str:
    """Generate document_id from URL hash."""
    return hashlib.sha256(url.encode()).hexdigest()


def generate_step_id(document_id: str, step_order: int) -> str:
    """Generate step_id from document_id and step_order."""
    return hashlib.sha256(f"{document_id}:{step_order}".encode()).hexdigest()


def generate_tool_id(document_id: str, tool_name: str, index: int) -> str:
    """Generate tool_id from document_id, tool_name, and index."""
    return hashlib.sha256(f"{document_id}:{tool_name}:{index}".encode()).hexdigest()


def generate_metric_id(document_id: str, metric_type: str, metric_name: str) -> str:
    """Generate metric_id from document_id, metric_type, and metric_name."""
    return hashlib.sha256(f"{document_id}:{metric_type}:{metric_name}".encode()).hexdigest()


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO format datetime string to datetime object."""
    try:
        # Handle both with and without microseconds
        if '.' in dt_str:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except Exception as e:
        logger.warning(f"Failed to parse datetime {dt_str}: {e}, using current time")
        return datetime.now(timezone.utc)


def transform_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform document to raw_documents table row."""
    document_id = generate_document_id(doc.get('url', ''))

    # Compute word and character counts
    main_text = doc.get('main_text', '')
    word_count = len(main_text.split()) if main_text else 0
    character_count = len(main_text) if main_text else 0

    # Get image and video counts
    image_count = len(doc.get('image_urls', []))
    video_count = len(doc.get('video_urls', []))

    # Parse timestamps
    fetched_at = parse_datetime(doc.get('fetched_at', datetime.now(timezone.utc).isoformat()))
    processed_at = parse_datetime(doc.get('processed_at', datetime.now(timezone.utc).isoformat()))

    # Get extraction metadata
    extraction_meta = doc.get('extraction_metadata', {})
    extraction_method = extraction_meta.get('extraction_method', 'rule_based')
    extraction_confidence = extraction_meta.get('confidence', {}).get('overall')
    if extraction_confidence is None:
        # Try to get average confidence
        confidences = extraction_meta.get('confidence', {})
        if isinstance(confidences, dict):
            values = [v for v in confidences.values() if isinstance(v, (int, float))]
            extraction_confidence = sum(values) / len(values) if values else None

    return {
        'document_id': document_id,
        'url': doc.get('url', ''),
        'title': doc.get('title', ''),
        'main_text': main_text,
        'raw_html': doc.get('raw_html'),  # Can be None
        'source': 'seed_spider',  # Default source
        'language': doc.get('language', 'en'),
        'http_status': doc.get('http_status', 200),
        'fetched_at': fetched_at,
        'processed_at': processed_at,
        'surface_type': doc.get('surface_type', ''),
        'dirt_type': doc.get('dirt_type', ''),
        'cleaning_method': doc.get('cleaning_method', ''),
        'extraction_method': extraction_method,
        'extraction_confidence': extraction_confidence,
        'image_count': image_count,
        'video_count': video_count,
        'word_count': word_count,
        'character_count': character_count,
    }


def transform_steps(doc: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
    """Transform steps_detailed to steps table rows."""
    steps = []
    steps_detailed = doc.get('steps_detailed', [])

    # Fallback to simple steps list if steps_detailed not available
    if not steps_detailed:
        simple_steps = doc.get('steps', [])
        steps_detailed = [
            {'step': step, 'order': idx + 1, 'confidence': 0.5}
            for idx, step in enumerate(simple_steps)
        ]

    extraction_meta = doc.get('extraction_metadata', {})
    extraction_method = extraction_meta.get('extraction_method', 'rule_based')
    created_at = parse_datetime(doc.get('processed_at', datetime.now(timezone.utc).isoformat()))

    for step_data in steps_detailed:
        step_order = step_data.get('order', step_data.get('step_order', 0))
        step_text = step_data.get('step', step_data.get('step_text', ''))
        confidence = step_data.get('confidence', 0.5)

        if not step_text or step_order == 0:
            continue

        step_id = generate_step_id(document_id, step_order)

        steps.append({
            'step_id': step_id,
            'document_id': document_id,
            'step_order': step_order,
            'step_text': step_text,
            'step_summary': None,  # Not extracted yet
            'confidence': float(confidence),
            'extraction_method': extraction_method,
            'created_at': created_at,
        })

    return steps


def transform_tools(doc: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
    """Transform tools_detailed to tools table rows."""
    tools = []
    tools_detailed = doc.get('tools_detailed', [])

    # Fallback to simple tools list if tools_detailed not available
    if not tools_detailed:
        simple_tools = doc.get('tools', [])
        tools_detailed = [
            {'name': tool, 'confidence': 0.5}
            for tool in simple_tools
        ]

    extraction_meta = doc.get('extraction_metadata', {})
    extraction_method = extraction_meta.get('extraction_method', 'rule_based')
    created_at = parse_datetime(doc.get('processed_at', datetime.now(timezone.utc).isoformat()))

    for idx, tool_data in enumerate(tools_detailed):
        tool_name = tool_data.get('name', tool_data.get('tool_name', ''))
        confidence = tool_data.get('confidence', 0.5)
        tool_category = tool_data.get('category', tool_data.get('tool_category'))

        if not tool_name:
            continue

        tool_id = generate_tool_id(document_id, tool_name, idx)

        tools.append({
            'tool_id': tool_id,
            'document_id': document_id,
            'tool_name': tool_name,
            'tool_category': tool_category,  # Can be None
            'confidence': float(confidence),
            'extraction_method': extraction_method,
            'mentioned_in_step_id': None,  # Not linked yet
            'created_at': created_at,
        })

    return tools


def transform_quality_metrics(doc: Dict[str, Any], document_id: str) -> List[Dict[str, Any]]:
    """Transform quality metrics to quality_metrics table rows."""
    metrics = []
    extraction_meta = doc.get('extraction_metadata', {})
    computed_at = parse_datetime(doc.get('processed_at', datetime.now(timezone.utc).isoformat()))

    # Extract confidence metrics
    confidences = extraction_meta.get('confidence', {})
    if isinstance(confidences, dict):
        for metric_name, value in confidences.items():
            if isinstance(value, (int, float)):
                metric_id = generate_metric_id(document_id, 'extraction_quality', metric_name)
                metrics.append({
                    'metric_id': metric_id,
                    'document_id': document_id,
                    'metric_type': 'extraction_quality',
                    'metric_name': metric_name,
                    'metric_value': float(value),
                    'metric_bool': None,
                    'threshold': None,
                    'passed': 1 if value >= 0.5 else 0,  # Default threshold
                    'metadata': None,
                    'computed_at': computed_at,
                })

    # Add word count as a quality metric
    main_text = doc.get('main_text', '')
    word_count = len(main_text.split()) if main_text else 0
    if word_count > 0:
        metric_id = generate_metric_id(document_id, 'text_quality', 'word_count')
        metrics.append({
            'metric_id': metric_id,
            'document_id': document_id,
            'metric_type': 'text_quality',
            'metric_name': 'word_count',
            'metric_value': float(word_count),
            'metric_bool': None,
            'threshold': None,
            'passed': 1,
            'metadata': None,
            'computed_at': computed_at,
        })

    return metrics


def load_documents(
    jsonl_path: Path,
    client: ClickHouseClient,
    batch_size: int = 100,
) -> Dict[str, int]:
    """
    Load documents from JSONL file into ClickHouse tables.
    
    Args:
        jsonl_path: Path to cleaning_docs.jsonl file
        client: ClickHouse client instance
        batch_size: Number of documents to process before batch insert
        
    Returns:
        Dictionary with counts of inserted rows per table
    """
    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    # Ensure tables exist
    logger.info("Ensuring tables exist...")
    create_raw_documents_table(client)
    create_steps_table(client)
    create_tools_table(client)
    create_quality_metrics_table(client)

    # Accumulators for batch inserts
    documents_batch = []
    steps_batch = []
    tools_batch = []
    metrics_batch = []

    counts = {
        'documents': 0,
        'steps': 0,
        'tools': 0,
        'metrics': 0,
    }

    logger.info(f"Reading documents from {jsonl_path}...")

    with jsonl_path.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                doc = json.loads(line)

                # Transform document
                document_id = generate_document_id(doc.get('url', ''))
                doc_row = transform_document(doc)
                documents_batch.append(doc_row)

                # Transform steps
                step_rows = transform_steps(doc, document_id)
                steps_batch.extend(step_rows)

                # Transform tools
                tool_rows = transform_tools(doc, document_id)
                tools_batch.extend(tool_rows)

                # Transform quality metrics
                metric_rows = transform_quality_metrics(doc, document_id)
                metrics_batch.extend(metric_rows)

                # Batch insert when batch_size reached
                if len(documents_batch) >= batch_size:
                    logger.info(f"Inserting batch of {len(documents_batch)} documents...")

                    # Insert documents
                    if documents_batch:
                        client.execute_insert('raw_documents', documents_batch)
                        counts['documents'] += len(documents_batch)
                        documents_batch = []

                    # Insert steps
                    if steps_batch:
                        client.execute_insert('steps', steps_batch)
                        counts['steps'] += len(steps_batch)
                        steps_batch = []

                    # Insert tools
                    if tools_batch:
                        client.execute_insert('tools', tools_batch)
                        counts['tools'] += len(tools_batch)
                        tools_batch = []

                    # Insert metrics
                    if metrics_batch:
                        client.execute_insert('quality_metrics', metrics_batch)
                        counts['metrics'] += len(metrics_batch)
                        metrics_batch = []

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing document on line {line_num}: {e}")
                continue

    # Insert remaining batches
    logger.info("Inserting final batch...")

    if documents_batch:
        client.execute_insert('raw_documents', documents_batch)
        counts['documents'] += len(documents_batch)

    if steps_batch:
        client.execute_insert('steps', steps_batch)
        counts['steps'] += len(steps_batch)

    if tools_batch:
        client.execute_insert('tools', tools_batch)
        counts['tools'] += len(tools_batch)

    if metrics_batch:
        client.execute_insert('quality_metrics', metrics_batch)
        counts['metrics'] += len(metrics_batch)

    return counts


def main():
    """CLI entry point."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Load cleaning documents from JSONL into ClickHouse"
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/processed/cleaning_docs.jsonl'),
        help='Path to input JSONL file (default: data/processed/cleaning_docs.jsonl)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for inserts (default: 100)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    try:
        # Connect to ClickHouse
        client = ClickHouseClient()
        client.connect()

        # Load documents
        counts = load_documents(args.input, client, batch_size=args.batch_size)

        # Print summary
        print("\n" + "="*60)
        print("Load Summary")
        print("="*60)
        print(f"Documents inserted: {counts['documents']}")
        print(f"Steps inserted: {counts['steps']}")
        print(f"Tools inserted: {counts['tools']}")
        print(f"Quality metrics inserted: {counts['metrics']}")
        print("="*60)

        client.disconnect()
        sys.exit(0)

    except Exception as e:
        logger.error(f"Failed to load documents: {e}", exc_info=True)
        print(f"✗ Failed to load documents: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


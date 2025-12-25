"""
ClickHouse table schema definitions and creation utilities.

This module defines the SQL DDL statements for creating ClickHouse tables
according to the schema specified in docs/DATA_WAREHOUSE.md.
"""

from typing import Optional
import logging

from src.db.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)


# ============================================================================
# Table Creation DDL Statements
# ============================================================================

RAW_DOCUMENTS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS raw_documents
(
    document_id String,
    url String,
    title String,
    main_text String,
    raw_html Nullable(String),
    source String,
    language String,
    http_status UInt16,
    fetched_at DateTime,
    processed_at DateTime,
    surface_type String,
    dirt_type String,
    cleaning_method String,
    extraction_method String,
    extraction_confidence Nullable(Float32),
    image_count UInt16,
    video_count UInt16,
    word_count UInt32,
    character_count UInt32,
    INDEX idx_surface_dirt_method (surface_type, dirt_type, cleaning_method) TYPE minmax GRANULARITY 4,
    INDEX idx_fetched_at fetched_at TYPE minmax GRANULARITY 4,
    INDEX idx_extraction_method extraction_method TYPE set(10) GRANULARITY 4
)
ENGINE = MergeTree()
PRIMARY KEY (document_id)
ORDER BY (document_id)
"""


STEPS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS steps
(
    step_id String,
    document_id String,
    step_order UInt16,
    step_text String,
    step_summary Nullable(String),
    confidence Float32,
    extraction_method String,
    created_at DateTime,
    INDEX idx_document_id document_id TYPE minmax GRANULARITY 4,
    INDEX idx_document_order (document_id, step_order) TYPE minmax GRANULARITY 4,
    INDEX idx_confidence confidence TYPE minmax GRANULARITY 4
)
ENGINE = MergeTree()
PRIMARY KEY (step_id)
ORDER BY (step_id)
"""


TOOLS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS tools
(
    tool_id String,
    document_id String,
    tool_name String,
    tool_category Nullable(String),
    confidence Float32,
    extraction_method String,
    mentioned_in_step_id Nullable(String),
    created_at DateTime,
    INDEX idx_document_id document_id TYPE minmax GRANULARITY 4,
    INDEX idx_tool_name tool_name TYPE set(100) GRANULARITY 4,
    INDEX idx_tool_category tool_category TYPE set(20) GRANULARITY 4,
    INDEX idx_mentioned_in_step mentioned_in_step_id TYPE minmax GRANULARITY 4
)
ENGINE = MergeTree()
PRIMARY KEY (tool_id)
ORDER BY (tool_id)
"""


QUALITY_METRICS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS quality_metrics
(
    metric_id String,
    document_id String,
    metric_type String,
    metric_name String,
    metric_value Nullable(Float32),
    metric_bool Nullable(UInt8),
    threshold Nullable(Float32),
    passed UInt8,
    metadata Nullable(String),
    computed_at DateTime,
    INDEX idx_document_id document_id TYPE minmax GRANULARITY 4,
    INDEX idx_metric_type_name (metric_type, metric_name) TYPE minmax GRANULARITY 4,
    INDEX idx_passed passed TYPE set(2) GRANULARITY 4
)
ENGINE = MergeTree()
PRIMARY KEY (metric_id)
ORDER BY (metric_id)
"""


def create_raw_documents_table(
    client: Optional[ClickHouseClient] = None,
    database: Optional[str] = None,
) -> None:
    """
    Create the raw_documents table in ClickHouse.
    
    Args:
        client: ClickHouse client instance. If None, creates a new client.
        database: Database name. If None, uses client's configured database.
        
    Raises:
        ConnectionError: If connection fails
        ClickHouseError: If table creation fails
    """
    if client is None:
        client = ClickHouseClient()
        should_disconnect = True
    else:
        should_disconnect = False

    try:
        # Ensure database exists
        if database:
            client.create_database(database)
        else:
            client.create_database()

        # Create table
        logger.info("Creating raw_documents table...")
        client.execute(RAW_DOCUMENTS_TABLE_DDL)
        logger.info("Successfully created raw_documents table")

        # Verify table exists
        table_name = "raw_documents"
        if client.table_exists(table_name, database):
            logger.info(f"Verified: {table_name} table exists")
        else:
            logger.warning(f"Warning: {table_name} table may not exist after creation")

    finally:
        if should_disconnect:
            client.disconnect()


def create_steps_table(
    client: Optional[ClickHouseClient] = None,
    database: Optional[str] = None,
) -> None:
    """
    Create the steps table in ClickHouse.
    
    Args:
        client: ClickHouse client instance. If None, creates a new client.
        database: Database name. If None, uses client's configured database.
        
    Raises:
        ConnectionError: If connection fails
        ClickHouseError: If table creation fails
    """
    if client is None:
        client = ClickHouseClient()
        should_disconnect = True
    else:
        should_disconnect = False

    try:
        # Ensure database exists
        if database:
            client.create_database(database)
        else:
            client.create_database()

        # Create table
        logger.info("Creating steps table...")
        client.execute(STEPS_TABLE_DDL)
        logger.info("Successfully created steps table")

        # Verify table exists
        table_name = "steps"
        if client.table_exists(table_name, database):
            logger.info(f"Verified: {table_name} table exists")
        else:
            logger.warning(f"Warning: {table_name} table may not exist after creation")

    finally:
        if should_disconnect:
            client.disconnect()


def create_tools_table(
    client: Optional[ClickHouseClient] = None,
    database: Optional[str] = None,
) -> None:
    """
    Create the tools table in ClickHouse.
    
    Args:
        client: ClickHouse client instance. If None, creates a new client.
        database: Database name. If None, uses client's configured database.
        
    Raises:
        ConnectionError: If connection fails
        ClickHouseError: If table creation fails
    """
    if client is None:
        client = ClickHouseClient()
        should_disconnect = True
    else:
        should_disconnect = False

    try:
        # Ensure database exists
        if database:
            client.create_database(database)
        else:
            client.create_database()

        # Create table
        logger.info("Creating tools table...")
        client.execute(TOOLS_TABLE_DDL)
        logger.info("Successfully created tools table")

        # Verify table exists
        table_name = "tools"
        if client.table_exists(table_name, database):
            logger.info(f"Verified: {table_name} table exists")
        else:
            logger.warning(f"Warning: {table_name} table may not exist after creation")

    finally:
        if should_disconnect:
            client.disconnect()


def create_quality_metrics_table(
    client: Optional[ClickHouseClient] = None,
    database: Optional[str] = None,
) -> None:
    """
    Create the quality_metrics table in ClickHouse.
    
    Args:
        client: ClickHouse client instance. If None, creates a new client.
        database: Database name. If None, uses client's configured database.
        
    Raises:
        ConnectionError: If connection fails
        ClickHouseError: If table creation fails
    """
    if client is None:
        client = ClickHouseClient()
        should_disconnect = True
    else:
        should_disconnect = False

    try:
        # Ensure database exists
        if database:
            client.create_database(database)
        else:
            client.create_database()

        # Create table
        logger.info("Creating quality_metrics table...")
        client.execute(QUALITY_METRICS_TABLE_DDL)
        logger.info("Successfully created quality_metrics table")

        # Verify table exists
        table_name = "quality_metrics"
        if client.table_exists(table_name, database):
            logger.info(f"Verified: {table_name} table exists")
        else:
            logger.warning(f"Warning: {table_name} table may not exist after creation")

    finally:
        if should_disconnect:
            client.disconnect()


if __name__ == "__main__":
    """CLI entry point for creating tables."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    try:
        create_raw_documents_table()
        print("✓ raw_documents table created successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to create raw_documents table: {e}")
        print(f"✗ Failed to create raw_documents table: {e}")
        sys.exit(1)


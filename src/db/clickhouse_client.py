"""
ClickHouse database client with connection pooling and error handling.

This module provides a high-level interface for interacting with ClickHouse,
including connection management, query execution, and error handling.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager

try:
    from clickhouse_driver import Client as ClickHouseDriverClient
    from clickhouse_driver.errors import Error as ClickHouseError
except ImportError:
    raise ImportError(
        "clickhouse-driver is required. Install it with: pip install clickhouse-driver"
    )

from src.config import get_config, ClickHouseConfig


logger = logging.getLogger(__name__)


class ClickHouseClient:
    """
    ClickHouse client with connection pooling and error handling.
    
    This client manages connections to ClickHouse and provides methods
    for executing queries, inserting data, and managing transactions.
    """

    def __init__(self, config: Optional[ClickHouseConfig] = None):
        """
        Initialize ClickHouse client.
        
        Args:
            config: ClickHouse configuration. If None, loads from default config.
        """
        if config is None:
            config = get_config().clickhouse

        self.config = config
        self._client: Optional[ClickHouseDriverClient] = None
        self._connection_params = self._build_connection_params()

    def _build_connection_params(self) -> Dict[str, Any]:
        """Build connection parameters from config."""
        # Check if compression dependencies are available
        compression = self.config.compression
        if compression:
            try:
                import lz4  # noqa: F401
                import clickhouse_cityhash  # noqa: F401
            except ImportError as e:
                logger.warning(
                    f"Compression dependencies not found ({e}). Compression disabled. "
                    "Install with: pip install lz4 clickhouse-cityhash"
                )
                compression = False

        params = {
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "user": self.config.user,
            "password": self.config.password or "",
            "connect_timeout": self.config.connect_timeout,
            "send_receive_timeout": self.config.send_receive_timeout,
            "compression": compression,
        }
        return params

    def connect(self) -> None:
        """Establish connection to ClickHouse."""
        if self._client is not None:
            logger.debug("ClickHouse client already connected")
            return

        try:
            logger.info(
                f"Connecting to ClickHouse at {self.config.host}:{self.config.port}"
            )
            self._client = ClickHouseDriverClient(**self._connection_params)
            # Test connection
            self._client.execute("SELECT 1")
            logger.info("Successfully connected to ClickHouse")
        except ClickHouseError as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            self._client = None
            raise ConnectionError(f"ClickHouse connection failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error connecting to ClickHouse: {e}")
            self._client = None
            raise ConnectionError(f"ClickHouse connection failed: {e}") from e

    def disconnect(self) -> None:
        """Close connection to ClickHouse."""
        if self._client is not None:
            try:
                self._client.disconnect()
                logger.info("Disconnected from ClickHouse")
            except Exception as e:
                logger.warning(f"Error disconnecting from ClickHouse: {e}")
            finally:
                self._client = None

    def _ensure_connected(self) -> None:
        """Ensure client is connected, connecting if necessary."""
        if self._client is None:
            self.connect()

    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query string
            params: Optional query parameters for parameterized queries
            settings: Optional query settings
            
        Returns:
            Query results (list of rows or single value depending on query)
            
        Raises:
            ConnectionError: If connection fails
            ClickHouseError: If query execution fails
        """
        self._ensure_connected()

        try:
            logger.debug(f"Executing query: {query[:100]}...")
            result = self._client.execute(query, params=params, settings=settings)
            logger.debug(
                f"Query executed successfully, returned {len(result) if isinstance(result, list) else 'non-list'} results")
            return result
        except ClickHouseError as e:
            logger.error(f"ClickHouse query error: {e}")
            logger.error(f"Query: {query}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            logger.error(f"Query: {query}")
            raise RuntimeError(f"Query execution failed: {e}") from e

    def execute_insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
    ) -> None:
        """
        Insert data into a table.
        
        Args:
            table: Table name
            data: List of dictionaries representing rows to insert
            columns: Optional list of column names (if None, inferred from data)
            
        Raises:
            ConnectionError: If connection fails
            ClickHouseError: If insert fails
        """
        if not data:
            logger.warning(f"No data to insert into {table}")
            return

        self._ensure_connected()

        # Infer columns from first row if not provided
        if columns is None:
            columns = list(data[0].keys())

        try:
            logger.info(f"Inserting {len(data)} rows into {table}")
            self._client.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES",
                data,
                types_check=True,
            )
            logger.info(f"Successfully inserted {len(data)} rows into {table}")
        except ClickHouseError as e:
            logger.error(f"ClickHouse insert error: {e}")
            logger.error(f"Table: {table}, Rows: {len(data)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting data: {e}")
            logger.error(f"Table: {table}, Rows: {len(data)}")
            raise RuntimeError(f"Insert failed: {e}") from e

    def execute_batch(
        self,
        table: str,
        data: List[List[Any]],
        columns: List[str],
    ) -> None:
        """
        Insert data in batch format (list of lists).
        
        Args:
            table: Table name
            data: List of lists representing rows to insert
            columns: List of column names
            
        Raises:
            ConnectionError: If connection fails
            ClickHouseError: If insert fails
        """
        if not data:
            logger.warning(f"No data to insert into {table}")
            return

        self._ensure_connected()

        try:
            logger.info(f"Inserting {len(data)} rows into {table} (batch format)")
            self._client.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES",
                data,
                types_check=True,
            )
            logger.info(f"Successfully inserted {len(data)} rows into {table}")
        except ClickHouseError as e:
            logger.error(f"ClickHouse batch insert error: {e}")
            logger.error(f"Table: {table}, Rows: {len(data)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in batch insert: {e}")
            logger.error(f"Table: {table}, Rows: {len(data)}")
            raise RuntimeError(f"Batch insert failed: {e}") from e

    def create_database(self, database_name: Optional[str] = None) -> None:
        """
        Create database if it doesn't exist.
        
        Args:
            database_name: Database name (defaults to config database)
            
        Raises:
            ConnectionError: If connection fails
            ClickHouseError: If database creation fails
        """
        if database_name is None:
            database_name = self.config.database

        self._ensure_connected()

        try:
            logger.info(f"Creating database {database_name} if not exists")
            self._client.execute(
                f"CREATE DATABASE IF NOT EXISTS {database_name}"
            )
            logger.info(f"Database {database_name} ready")
        except ClickHouseError as e:
            logger.error(f"Failed to create database {database_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating database: {e}")
            raise RuntimeError(f"Database creation failed: {e}") from e

    def table_exists(self, table_name: str, database: Optional[str] = None) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Table name
            database: Database name (defaults to config database)
            
        Returns:
            True if table exists, False otherwise
        """
        if database is None:
            database = self.config.database

        self._ensure_connected()

        try:
            result = self._client.execute(
                f"EXISTS TABLE {database}.{table_name}"
            )
            return bool(result[0][0] if result else False)
        except ClickHouseError as e:
            logger.warning(f"Error checking table existence: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking table existence: {e}")
            return False

    @contextmanager
    def transaction(self):
        """
        Context manager for transactions.
        
        Note: ClickHouse doesn't support traditional transactions,
        but this provides a consistent interface for future use.
        
        Usage:
            with client.transaction():
                client.execute("INSERT INTO ...")
                client.execute("UPDATE ...")
        """
        # ClickHouse doesn't support transactions in the traditional sense,
        # but we provide this interface for consistency
        logger.debug("Starting transaction context (ClickHouse doesn't support transactions)")
        try:
            yield self
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            raise
        finally:
            logger.debug("Transaction context ended")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()


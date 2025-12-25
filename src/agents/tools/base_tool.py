"""
Base tool interface for agent tools that query ClickHouse.

All agent tools should inherit from this base class to ensure consistent
error handling, connection management, and interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.db.clickhouse_client import ClickHouseClient

logger = logging.getLogger(__name__)


class BaseClickHouseTool(ABC):
    """
    Base class for agent tools that query ClickHouse.
    
    Provides common functionality:
    - ClickHouse client management
    - Error handling
    - Query execution
    - Result formatting
    """

    def __init__(self, client: Optional[ClickHouseClient] = None):
        """
        Initialize the tool with a ClickHouse client.
        
        Args:
            client: ClickHouse client instance. If None, creates a new client.
        """
        if client is None:
            self.client = ClickHouseClient()
        else:
            self.client = client

        self.client.connect()

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dictionary with tool results
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If query execution fails
        """
        pass

    def _execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a ClickHouse query with error handling.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Query results
            
        Raises:
            RuntimeError: If query execution fails
        """
        try:
            logger.debug(f"Executing query for {self.__class__.__name__}")
            result = self.client.execute(query, params=params)
            return result
        except Exception as e:
            logger.error(f"Query execution failed in {self.__class__.__name__}: {e}")
            raise RuntimeError(f"Tool execution failed: {e}") from e

    def _normalize_string(self, value: Optional[str]) -> Optional[str]:
        """
        Normalize string values (lowercase, trim) to match dbt staging normalization.
        
        Args:
            value: String value to normalize
            
        Returns:
            Normalized string or None
        """
        if value is None:
            return None
        return value.lower().strip()

    def _normalize_method(self, value: Optional[str]) -> Optional[str]:
        """
        Normalize cleaning method (lowercase, trim, replace spaces with underscores).
        
        Args:
            value: Method value to normalize
            
        Returns:
            Normalized method string or None
        """
        if value is None:
            return None
        normalized = value.lower().strip().replace(" ", "_")
        return normalized

    def _escape_sql_string(self, value: str) -> str:
        """
        Escape SQL string values to prevent injection.
        
        SECURITY NOTE: While this provides basic protection, parameterized queries
        would be more secure. Consider refactoring to use ClickHouse's parameterized
        query support: client.execute(query, params={'param_name': value})
        
        Current approach: Escapes single quotes by doubling them (SQL standard).
        This is safer than raw f-strings but parameterized queries are preferred.
        """
        """
        Escape single quotes in SQL string values.
        
        Args:
            value: String value to escape
            
        Returns:
            Escaped string safe for SQL queries
        """
        if value is None:
            return "NULL"
        # Escape single quotes by doubling them
        return value.replace("'", "''")

    def close(self):
        """Close the ClickHouse connection."""
        if self.client:
            self.client.disconnect()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


"""
Tool to fetch cleaning steps for a specific surface × dirt × method combination.

Queries steps table joined with raw_documents to retrieve ordered steps
with confidence scores and document references.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.tools.base_tool import BaseClickHouseTool

logger = logging.getLogger(__name__)


class FetchStepsTool(BaseClickHouseTool):
    """
    Tool to retrieve cleaning steps for a specific combination.
    
    Input:
        - surface_type: Normalized surface type
        - dirt_type: Normalized dirt type
        - cleaning_method: Normalized cleaning method
        - limit: Optional limit on number of steps to return (default: 10)
    
    Output:
        - steps: List of steps with step_order, step_text, document_id, confidence
        - total_steps: Total number of steps found
        - unique_documents: Number of unique documents
    """

    def execute(
        self,
        surface_type: str,
        dirt_type: str,
        cleaning_method: str,
        limit: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Fetch cleaning steps for the given combination.
        
        Args:
            surface_type: Normalized surface type
            dirt_type: Normalized dirt type
            cleaning_method: Normalized cleaning method
            limit: Maximum number of steps to return (default: 10)
            
        Returns:
            Dictionary with 'steps' list and metadata
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not surface_type or not dirt_type or not cleaning_method:
            raise ValueError("surface_type, dirt_type, and cleaning_method are required")

        if limit is None:
            limit = 10

        # Normalize inputs
        surface_type = self._normalize_string(surface_type)
        dirt_type = self._normalize_string(dirt_type)
        cleaning_method = self._normalize_method(cleaning_method)

        # Query steps joined with raw_documents
        # Use f-string formatting since clickhouse-driver doesn't support {param:Type} syntax
        query = f"""
        SELECT
            s.step_order,
            s.step_text,
            s.document_id,
            s.confidence,
            s.step_summary
        FROM cleaning_warehouse.steps s
        INNER JOIN cleaning_warehouse.raw_documents d
            ON s.document_id = d.document_id
        WHERE d.surface_type = '{self._escape_sql_string(surface_type)}'
          AND d.dirt_type = '{self._escape_sql_string(dirt_type)}'
          AND d.cleaning_method = '{self._escape_sql_string(cleaning_method)}'
        ORDER BY s.step_order ASC
        LIMIT {limit}
        """

        results = self._execute_query(query)

        # Get total count and unique documents
        count_query = f"""
        SELECT
            COUNT(*) as total_steps,
            COUNT(DISTINCT s.document_id) as unique_documents
        FROM cleaning_warehouse.steps s
        INNER JOIN cleaning_warehouse.raw_documents d
            ON s.document_id = d.document_id
        WHERE d.surface_type = '{self._escape_sql_string(surface_type)}'
          AND d.dirt_type = '{self._escape_sql_string(dirt_type)}'
          AND d.cleaning_method = '{self._escape_sql_string(cleaning_method)}'
        """

        count_results = self._execute_query(count_query)
        total_steps = count_results[0][0] if count_results else 0
        unique_documents = count_results[0][1] if count_results else 0

        # Format steps
        steps = []
        for row in results:
            steps.append({
                "step_order": row[0],
                "step_text": row[1],
                "document_id": row[2],
                "confidence": float(row[3]) if row[3] is not None else 0.0,
                "step_summary": row[4] if len(row) > 4 else None,
            })

        logger.info(
            f"Found {len(steps)} steps (of {total_steps} total) "
            f"from {unique_documents} documents for "
            f"{surface_type} × {dirt_type} × {cleaning_method}"
        )

        return {
            "steps": steps,
            "total_steps": total_steps,
            "unique_documents": unique_documents,
        }


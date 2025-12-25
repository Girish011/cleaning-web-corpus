"""
Tool to fetch available cleaning methods for a given surface × dirt combination.

Queries fct_cleaning_procedures to find methods with document counts,
average steps, confidence scores, and common tools.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.tools.base_tool import BaseClickHouseTool

logger = logging.getLogger(__name__)


class FetchMethodsTool(BaseClickHouseTool):
    """
    Tool to retrieve available cleaning methods for a surface × dirt combination.
    
    Input:
        - surface_type: Normalized surface type (e.g., "carpets_floors")
        - dirt_type: Normalized dirt type (e.g., "stain")
    
    Output:
        - methods: List of methods with document_count, avg_steps, avg_confidence, common_tools
    """

    def execute(
        self,
        surface_type: str,
        dirt_type: str,
    ) -> Dict[str, Any]:
        """
        Fetch available cleaning methods for the given combination.
        
        Args:
            surface_type: Normalized surface type
            dirt_type: Normalized dirt type
            
        Returns:
            Dictionary with 'methods' list containing method information
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not surface_type or not dirt_type:
            raise ValueError("surface_type and dirt_type are required")

        # Normalize inputs
        surface_type = self._normalize_string(surface_type)
        dirt_type = self._normalize_string(dirt_type)

        # Query fct_cleaning_procedures for methods matching this combination
        # Use f-string formatting since clickhouse-driver doesn't support {param:Type} syntax
        query = f"""
        SELECT
            cleaning_method,
            document_count,
            avg_step_count,
            avg_extraction_confidence,
            avg_quality_score
        FROM cleaning_warehouse.fct_cleaning_procedures
        WHERE surface_type = '{self._escape_sql_string(surface_type)}'
          AND dirt_type = '{self._escape_sql_string(dirt_type)}'
        ORDER BY document_count DESC, avg_extraction_confidence DESC
        """

        results = self._execute_query(query)

        # Get common tools for each method
        methods = []
        for row in results:
            method = row[0]
            doc_count = row[1]
            avg_steps = float(row[2]) if row[2] is not None else 0.0
            avg_confidence = float(row[3]) if row[3] is not None else 0.0
            avg_quality = float(row[4]) if row[4] is not None else 0.0

            # Get top 3 common tools for this method
            common_tools = self._get_common_tools(surface_type, dirt_type, method)

            methods.append({
                "cleaning_method": method,
                "document_count": doc_count,
                "avg_steps": round(avg_steps, 2),
                "avg_confidence": round(avg_confidence, 3),
                "avg_quality_score": round(avg_quality, 3),
                "common_tools": common_tools,
            })

        logger.info(
            f"Found {len(methods)} methods for {surface_type} × {dirt_type}"
        )

        return {"methods": methods}

    def _get_common_tools(
        self,
        surface_type: str,
        dirt_type: str,
        cleaning_method: str,
        limit: int = 3,
    ) -> List[str]:
        """
        Get top N common tools for a specific combination.
        
        Args:
            surface_type: Surface type
            dirt_type: Dirt type
            cleaning_method: Cleaning method
            limit: Maximum number of tools to return
            
        Returns:
            List of tool names
        """
        query = f"""
        SELECT
            t.tool_name,
            COUNT(*) as usage_count
        FROM cleaning_warehouse.tools t
        INNER JOIN cleaning_warehouse.raw_documents d
            ON t.document_id = d.document_id
        WHERE d.surface_type = '{self._escape_sql_string(surface_type)}'
          AND d.dirt_type = '{self._escape_sql_string(dirt_type)}'
          AND d.cleaning_method = '{self._escape_sql_string(cleaning_method)}'
          AND t.tool_name IS NOT NULL
          AND t.tool_name != ''
        GROUP BY t.tool_name
        ORDER BY usage_count DESC
        LIMIT {limit}
        """

        try:
            results = self._execute_query(query)
            return [row[0] for row in results]
        except Exception as e:
            logger.warning(f"Failed to fetch common tools: {e}")
            return []


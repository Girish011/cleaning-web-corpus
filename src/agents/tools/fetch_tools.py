"""
Tool to fetch recommended tools for a specific surface × dirt × method combination.

Queries tools table aggregated by tool_name to find most commonly used tools
with usage counts, confidence scores, categories, and step references.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.tools.base_tool import BaseClickHouseTool

logger = logging.getLogger(__name__)


class FetchToolsTool(BaseClickHouseTool):
    """
    Tool to retrieve recommended tools for a specific combination.
    
    Input:
        - surface_type: Normalized surface type
        - dirt_type: Normalized dirt type
        - cleaning_method: Normalized cleaning method
    
    Output:
        - tools: List of tools with tool_name, usage_count, avg_confidence, category, is_primary, mentioned_in_steps
        - total_tools: Total number of unique tools found
    """

    def execute(
        self,
        surface_type: str,
        dirt_type: str,
        cleaning_method: str,
    ) -> Dict[str, Any]:
        """
        Fetch recommended tools for the given combination.
        
        Args:
            surface_type: Normalized surface type
            dirt_type: Normalized dirt type
            cleaning_method: Normalized cleaning method
            
        Returns:
            Dictionary with 'tools' list and metadata
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not surface_type or not dirt_type or not cleaning_method:
            raise ValueError("surface_type, dirt_type, and cleaning_method are required")

        # Normalize inputs
        surface_type = self._normalize_string(surface_type)
        dirt_type = self._normalize_string(dirt_type)
        cleaning_method = self._normalize_method(cleaning_method)

        # Query tools aggregated by tool_name
        # Use f-string formatting since clickhouse-driver doesn't support {param:Type} syntax
        query = f"""
        SELECT
            t.tool_name,
            COUNT(*) as usage_count,
            AVG(t.confidence) as avg_confidence,
            MAX(t.tool_category) as category,
            COUNT(DISTINCT t.mentioned_in_step_id) as step_mentions
        FROM cleaning_warehouse.tools t
        INNER JOIN cleaning_warehouse.raw_documents d
            ON t.document_id = d.document_id
        WHERE d.surface_type = '{self._escape_sql_string(surface_type)}'
          AND d.dirt_type = '{self._escape_sql_string(dirt_type)}'
          AND d.cleaning_method = '{self._escape_sql_string(cleaning_method)}'
          AND t.tool_name IS NOT NULL
          AND t.tool_name != ''
        GROUP BY t.tool_name
        ORDER BY usage_count DESC, avg_confidence DESC
        """

        results = self._execute_query(query)

        # Get step IDs where each tool is mentioned
        tools = []
        total_usage = 0
        max_usage = 0

        for row in results:
            tool_name = row[0]
            usage_count = row[1]
            avg_confidence = float(row[2]) if row[2] is not None else 0.0
            category = row[3]
            step_mentions = row[4]

            total_usage += usage_count
            if usage_count > max_usage:
                max_usage = usage_count

            # Get step IDs where this tool is mentioned
            step_ids = self._get_step_ids_for_tool(
                surface_type, dirt_type, cleaning_method, tool_name
            )

            tools.append({
                "tool_name": tool_name,
                "usage_count": usage_count,
                "avg_confidence": round(avg_confidence, 3),
                "category": category,
                "is_primary": False,  # Will be set below based on usage
                "mentioned_in_steps": step_ids,
            })

        # Mark primary tools (top 50% by usage)
        if tools:
            # Sort by usage_count to determine primary tools
            sorted_tools = sorted(tools, key=lambda x: x["usage_count"], reverse=True)
            primary_threshold = sorted_tools[len(
                sorted_tools) // 2]["usage_count"] if len(sorted_tools) > 1 else max_usage

            for tool in tools:
                tool["is_primary"] = tool["usage_count"] >= primary_threshold

        logger.info(
            f"Found {len(tools)} unique tools for "
            f"{surface_type} × {dirt_type} × {cleaning_method}"
        )

        return {
            "tools": tools,
            "total_tools": len(tools),
        }

    def _get_step_ids_for_tool(
        self,
        surface_type: str,
        dirt_type: str,
        cleaning_method: str,
        tool_name: str,
        limit: int = 10,
    ) -> List[str]:
        """
        Get step IDs where a tool is mentioned.
        
        Args:
            surface_type: Surface type
            dirt_type: Dirt type
            cleaning_method: Cleaning method
            tool_name: Tool name
            limit: Maximum number of step IDs to return
            
        Returns:
            List of step IDs
        """
        query = f"""
        SELECT DISTINCT
            t.mentioned_in_step_id
        FROM cleaning_warehouse.tools t
        INNER JOIN cleaning_warehouse.raw_documents d
            ON t.document_id = d.document_id
        WHERE d.surface_type = '{self._escape_sql_string(surface_type)}'
          AND d.dirt_type = '{self._escape_sql_string(dirt_type)}'
          AND d.cleaning_method = '{self._escape_sql_string(cleaning_method)}'
          AND t.tool_name = '{self._escape_sql_string(tool_name)}'
          AND t.mentioned_in_step_id IS NOT NULL
          AND t.mentioned_in_step_id != ''
        LIMIT {limit}
        """

        try:
            results = self._execute_query(query)
            return [row[0] for row in results if row[0]]
        except Exception as e:
            logger.warning(f"Failed to fetch step IDs for tool {tool_name}: {e}")
            return []


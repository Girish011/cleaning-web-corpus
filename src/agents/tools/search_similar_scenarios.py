"""
Tool to search for similar cleaning scenarios when exact match is not available.

Queries fct_cleaning_procedures to find combinations with same dirt_type
or same surface_type, computing similarity scores based on shared dimensions.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.tools.base_tool import BaseClickHouseTool

logger = logging.getLogger(__name__)


class SearchSimilarScenariosTool(BaseClickHouseTool):
    """
    Tool to find similar cleaning scenarios when exact match is not available.
    
    Input:
        - surface_type: Normalized surface type
        - dirt_type: Normalized dirt type
        - fuzzy_match: Whether to use fuzzy matching (default: True)
        - limit: Maximum number of results to return (default: 10)
    
    Output:
        - similar_combinations: List of similar combinations with similarity_score
    """

    def execute(
        self,
        surface_type: str,
        dirt_type: str,
        fuzzy_match: bool = True,
        limit: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Search for similar scenarios matching the given combination.
        
        Args:
            surface_type: Normalized surface type
            dirt_type: Normalized dirt type
            fuzzy_match: Whether to use fuzzy matching (default: True)
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            Dictionary with 'similar_combinations' list containing similar scenarios
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not surface_type or not dirt_type:
            raise ValueError("surface_type and dirt_type are required")

        if limit is None:
            limit = 10

        # Normalize inputs
        surface_type = self._normalize_string(surface_type)
        dirt_type = self._normalize_string(dirt_type)

        if fuzzy_match:
            # Find combinations with same dirt_type or same surface_type
            # Compute similarity score: 1.0 for exact match, 0.5 for same dirt, 0.5 for same surface
            query = f"""
            SELECT
                surface_type,
                dirt_type,
                cleaning_method,
                document_count,
                avg_extraction_confidence,
                CASE
                    WHEN surface_type = '{self._escape_sql_string(surface_type)}' AND dirt_type = '{self._escape_sql_string(dirt_type)}' THEN 1.0
                    WHEN dirt_type = '{self._escape_sql_string(dirt_type)}' THEN 0.5
                    WHEN surface_type = '{self._escape_sql_string(surface_type)}' THEN 0.3
                    ELSE 0.1
                END as similarity_score
            FROM cleaning_warehouse.fct_cleaning_procedures
            WHERE (surface_type = '{self._escape_sql_string(surface_type)}' OR dirt_type = '{self._escape_sql_string(dirt_type)}')
            ORDER BY similarity_score DESC, document_count DESC, avg_extraction_confidence DESC
            LIMIT {limit}
            """
        else:
            # Only exact matches
            query = f"""
            SELECT
                surface_type,
                dirt_type,
                cleaning_method,
                document_count,
                avg_extraction_confidence,
                1.0 as similarity_score
            FROM cleaning_warehouse.fct_cleaning_procedures
            WHERE surface_type = '{self._escape_sql_string(surface_type)}'
              AND dirt_type = '{self._escape_sql_string(dirt_type)}'
            ORDER BY document_count DESC, avg_extraction_confidence DESC
            LIMIT {limit}
            """

        results = self._execute_query(query)

        similar_combinations = []
        for row in results:
            similar_combinations.append({
                "surface_type": row[0],
                "dirt_type": row[1],
                "cleaning_method": row[2],
                "document_count": row[3],
                "avg_extraction_confidence": float(row[4]) if row[4] is not None else 0.0,
                "similarity_score": float(row[5]),
            })

        logger.info(
            f"Found {len(similar_combinations)} similar scenarios for "
            f"{surface_type} × {dirt_type} (fuzzy_match={fuzzy_match})"
        )

        return {"similar_combinations": similar_combinations}


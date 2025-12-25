"""
Tool to fetch full document context for reference and citation.

Queries raw_documents with joins to steps and tools tables to retrieve
complete document information including URL, title, steps, and tools.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.tools.base_tool import BaseClickHouseTool

logger = logging.getLogger(__name__)


class FetchReferenceContextTool(BaseClickHouseTool):
    """
    Tool to retrieve full document context for reference.
    
    Input:
        - document_ids: List of document IDs to fetch
        - include_steps: Whether to include steps (default: True)
        - include_tools: Whether to include tools (default: True)
    
    Output:
        - documents: List of documents with full context including steps and tools
    """

    def execute(
        self,
        document_ids: List[str],
        include_steps: bool = True,
        include_tools: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch full document context for the given document IDs.
        
        Args:
            document_ids: List of document IDs to fetch
            include_steps: Whether to include steps in the response
            include_tools: Whether to include tools in the response
            
        Returns:
            Dictionary with 'documents' list containing full document context
            
        Raises:
            ValueError: If document_ids is empty
        """
        if not document_ids:
            raise ValueError("document_ids cannot be empty")

        # Query raw_documents for basic document info
        # Build query with proper parameterization for IN clause
        # ClickHouse doesn't support array parameters directly, so we use a workaround
        placeholders = ", ".join([f"'{doc_id}'" for doc_id in document_ids])

        query = f"""
        SELECT
            document_id,
            url,
            title,
            surface_type,
            dirt_type,
            cleaning_method,
            extraction_confidence,
            word_count,
            character_count,
            fetched_at,
            processed_at
        FROM cleaning_warehouse.raw_documents
        WHERE document_id IN ({placeholders})
        """

        # Note: Using string formatting for IN clause since ClickHouse doesn't support
        # array parameters directly. document_ids are already validated as strings.
        results = self._execute_query(query)

        documents = []
        for row in results:
            doc_id = row[0]

            document = {
                "document_id": doc_id,
                "url": row[1],
                "title": row[2],
                "surface_type": row[3],
                "dirt_type": row[4],
                "cleaning_method": row[5],
                "extraction_confidence": float(row[6]) if row[6] is not None else None,
                "word_count": row[7],
                "character_count": row[8],
                "fetched_at": row[9].isoformat() if row[9] else None,
                "processed_at": row[10].isoformat() if row[10] else None,
            }

            # Fetch steps if requested
            if include_steps:
                document["steps"] = self._get_steps_for_document(doc_id)
            else:
                document["steps"] = []

            # Fetch tools if requested
            if include_tools:
                document["tools"] = self._get_tools_for_document(doc_id)
            else:
                document["tools"] = []

            documents.append(document)

        logger.info(
            f"Fetched context for {len(documents)} documents "
            f"(steps: {include_steps}, tools: {include_tools})"
        )

        return {"documents": documents}

    def _get_steps_for_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get steps for a document, ordered by step_order.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of step dictionaries
        """
        query = f"""
        SELECT
            step_id,
            step_order,
            step_text,
            step_summary,
            confidence
        FROM cleaning_warehouse.steps
        WHERE document_id = '{self._escape_sql_string(document_id)}'
        ORDER BY step_order ASC
        """

        try:
            results = self._execute_query(query)
            return [
                {
                    "step_id": row[0],
                    "step_order": row[1],
                    "step_text": row[2],
                    "step_summary": row[3],
                    "confidence": float(row[4]) if row[4] is not None else 0.0,
                }
                for row in results
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch steps for document {document_id}: {e}")
            return []

    def _get_tools_for_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get tools for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of tool dictionaries
        """
        query = f"""
        SELECT DISTINCT
            tool_name,
            tool_category,
            AVG(confidence) as avg_confidence,
            mentioned_in_step_id
        FROM cleaning_warehouse.tools
        WHERE document_id = '{self._escape_sql_string(document_id)}'
          AND tool_name IS NOT NULL
          AND tool_name != ''
        GROUP BY tool_name, tool_category, mentioned_in_step_id
        ORDER BY tool_name
        """

        try:
            results = self._execute_query(query)
            return [
                {
                    "tool_name": row[0],
                    "tool_category": row[1],
                    "avg_confidence": float(row[2]) if row[2] is not None else 0.0,
                    "mentioned_in_step_id": row[3],
                }
                for row in results
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch tools for document {document_id}: {e}")
            return []


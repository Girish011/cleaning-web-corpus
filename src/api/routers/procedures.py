"""
Procedure search endpoint router.

Handles GET /search_procedures requests with validation and error handling.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse

from src.db.clickhouse_client import ClickHouseClient
from src.api.schemas.procedures import (
    SearchProceduresRequest,
    SearchProceduresResponse,
    Procedure,
    ProcedureStep,
    ProcedureTool,
)
from src.api.schemas.workflow import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _escape_sql_string(value: str) -> str:
    """
    Escape single quotes in SQL string values.
    
    SECURITY NOTE: While this provides basic protection, parameterized queries
    would be more secure. Consider refactoring to use ClickHouse's parameterized
    query support: client.execute(query, params={'param_name': value})
    
    Current approach: Escapes single quotes by doubling them (SQL standard).
    This is safer than raw f-strings but parameterized queries are preferred.
    """
    if value is None:
        return "NULL"
    return value.replace("'", "''")


def _normalize_string(value: Optional[str]) -> Optional[str]:
    """Normalize string values (lowercase, trim)."""
    if value is None:
        return None
    return value.lower().strip()


@router.get(
    "/search_procedures",
    response_model=SearchProceduresResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def search_procedures(
    surface_type: Optional[str] = Query(None, description="Filter by surface type"),
    dirt_type: Optional[str] = Query(None, description="Filter by dirt type"),
    cleaning_method: Optional[str] = Query(None, description="Filter by cleaning method"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum extraction confidence"),
    include_steps: bool = Query(True, description="Include steps in response"),
    include_tools: bool = Query(True, description="Include tools in response"),
) -> SearchProceduresResponse:
    """
    Search for cleaning procedures in the corpus by filters.
    
    Args:
        surface_type: Optional surface type filter
        dirt_type: Optional dirt type filter
        cleaning_method: Optional cleaning method filter
        limit: Maximum number of results (default: 20, max: 100)
        offset: Pagination offset (default: 0)
        min_confidence: Minimum extraction confidence (default: 0.0)
        include_steps: Include steps in response (default: true)
        include_tools: Include tools in response (default: true)
        
    Returns:
        SearchProceduresResponse with matching procedures
        
    Raises:
        HTTPException: With appropriate status code and error response
    """
    request_id = f"req-{uuid.uuid4().hex[:8]}"

    # Validate filter values
    valid_surface_types = {
        "carpets_floors", "clothes", "pillows_bedding", "upholstery",
        "hard_surfaces", "bathroom", "appliances", "outdoor"
    }
    valid_dirt_types = {
        "stain", "dust", "grease", "mold", "pet_hair", "odor", "water_stain", "ink"
    }
    valid_methods = {
        "vacuum", "hand_wash", "washing_machine", "spot_clean",
        "steam_clean", "dry_clean", "wipe", "scrub"
    }

    if surface_type and surface_type not in valid_surface_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid surface_type: '{surface_type}'. Valid values: {', '.join(sorted(valid_surface_types))}",
                "details": {
                    "parameter": "surface_type",
                    "value": surface_type,
                },
                "request_id": request_id,
            },
        )

    if dirt_type and dirt_type not in valid_dirt_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid dirt_type: '{dirt_type}'. Valid values: {', '.join(sorted(valid_dirt_types))}",
                "details": {
                    "parameter": "dirt_type",
                    "value": dirt_type,
                },
                "request_id": request_id,
            },
        )

    if cleaning_method and cleaning_method not in valid_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid cleaning_method: '{cleaning_method}'. Valid values: {', '.join(sorted(valid_methods))}",
                "details": {
                    "parameter": "cleaning_method",
                    "value": cleaning_method,
                },
                "request_id": request_id,
            },
        )

    # Normalize filter values
    surface_type = _normalize_string(surface_type) if surface_type else None
    dirt_type = _normalize_string(dirt_type) if dirt_type else None
    cleaning_method = _normalize_string(cleaning_method) if cleaning_method else None

    client = None
    try:
        # Initialize ClickHouse client
        client = ClickHouseClient()
        client.connect()

        # Build WHERE clause
        where_conditions = []
        if surface_type:
            where_conditions.append(f"d.surface_type = '{_escape_sql_string(surface_type)}'")
        if dirt_type:
            where_conditions.append(f"d.dirt_type = '{_escape_sql_string(dirt_type)}'")
        if cleaning_method:
            where_conditions.append(f"d.cleaning_method = '{_escape_sql_string(cleaning_method)}'")
        if min_confidence > 0.0:
            where_conditions.append(f"d.extraction_confidence >= {min_confidence}")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get total count
        count_query = f"""
        SELECT COUNT(DISTINCT d.document_id)
        FROM cleaning_warehouse.raw_documents d
        WHERE {where_clause}
        """

        count_result = client.execute(count_query)
        total = count_result[0][0] if count_result else 0

        # Get documents with pagination
        documents_query = f"""
        SELECT
            d.document_id,
            d.url,
            d.title,
            d.surface_type,
            d.dirt_type,
            d.cleaning_method,
            d.extraction_confidence,
            d.extraction_method,
            d.fetched_at,
            d.word_count
        FROM cleaning_warehouse.raw_documents d
        WHERE {where_clause}
        ORDER BY d.extraction_confidence DESC, d.fetched_at DESC
        LIMIT {limit} OFFSET {offset}
        """

        documents_result = client.execute(documents_query)

        # Build procedures list
        procedures = []
        document_ids = [row[0] for row in documents_result]

        if document_ids:
            # Fetch steps if requested
            steps_by_doc = {}
            if include_steps:
                steps_query = f"""
                SELECT
                    s.document_id,
                    s.step_order,
                    s.step_text,
                    s.confidence
                FROM cleaning_warehouse.steps s
                WHERE s.document_id IN ({','.join([f"'{_escape_sql_string(doc_id)}'" for doc_id in document_ids])})
                ORDER BY s.document_id, s.step_order ASC
                """
                steps_result = client.execute(steps_query)
                for row in steps_result:
                    doc_id = row[0]
                    if doc_id not in steps_by_doc:
                        steps_by_doc[doc_id] = []
                    steps_by_doc[doc_id].append({
                        "step_order": row[1],
                        "step_text": row[2],
                        "confidence": float(row[3]) if row[3] is not None else 0.0,
                    })

            # Fetch tools if requested
            tools_by_doc = {}
            if include_tools:
                tools_query = f"""
                SELECT
                    t.document_id,
                    t.tool_name,
                    t.tool_category,
                    t.confidence
                FROM cleaning_warehouse.tools t
                WHERE t.document_id IN ({','.join([f"'{_escape_sql_string(doc_id)}'" for doc_id in document_ids])})
                  AND t.tool_name IS NOT NULL
                  AND t.tool_name != ''
                ORDER BY t.document_id, t.confidence DESC
                """
                tools_result = client.execute(tools_query)
                for row in tools_result:
                    doc_id = row[0]
                    if doc_id not in tools_by_doc:
                        tools_by_doc[doc_id] = []
                    tools_by_doc[doc_id].append({
                        "tool_name": row[1],
                        "tool_category": row[2] if row[2] else None,
                        "confidence": float(row[3]) if row[3] is not None else 0.0,
                    })

            # Build procedure objects
            for row in documents_result:
                doc_id = row[0]
                url = row[1]
                title = row[2]
                surface = row[3]
                dirt = row[4]
                method = row[5]
                confidence = float(row[6]) if row[6] is not None else 0.0
                extraction_method = row[7]
                fetched_at = row[8].isoformat() if row[8] else ""
                word_count = row[9] if row[9] else 0

                # Get steps for this document
                steps = None
                if include_steps and doc_id in steps_by_doc:
                    steps = [
                        ProcedureStep(
                            step_order=s["step_order"],
                            step_text=s["step_text"],
                            confidence=s["confidence"],
                        )
                        for s in steps_by_doc[doc_id]
                    ]

                # Get tools for this document
                tools = None
                if include_tools and doc_id in tools_by_doc:
                    tools = [
                        ProcedureTool(
                            tool_name=t["tool_name"],
                            category=t["tool_category"],
                            confidence=t["confidence"],
                        )
                        for t in tools_by_doc[doc_id]
                    ]

                procedures.append(
                    Procedure(
                        document_id=doc_id,
                        url=url,
                        title=title,
                        surface_type=surface,
                        dirt_type=dirt,
                        cleaning_method=method,
                        extraction_confidence=confidence,
                        extraction_method=extraction_method,
                        steps=steps,
                        tools=tools,
                        fetched_at=fetched_at,
                        word_count=word_count,
                    )
                )

        return SearchProceduresResponse(
            total=total,
            limit=limit,
            offset=offset,
            procedures=procedures,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Handle database/service errors
        error_msg = str(e)
        logger.error(f"Database query failed in search_procedures: {e}", exc_info=True)

        if "connection" in error_msg.lower() or "unavailable" in error_msg.lower():
            # 503: Service unavailable
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "service_unavailable",
                    "message": "ClickHouse database is temporarily unavailable",
                    "retry_after": 30,
                    "request_id": request_id,
                },
            )
        else:
            # 500: Internal server error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "internal_error",
                    "message": "Database query failed",
                    "request_id": request_id,
                },
            )

    finally:
        # Clean up client connection
        if client:
            client.disconnect()


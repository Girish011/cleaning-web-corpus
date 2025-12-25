"""
Coverage statistics endpoint router.

Handles GET /stats/coverage requests with validation and error handling.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Set

from fastapi import APIRouter, HTTPException, status, Query

from src.db.clickhouse_client import ClickHouseClient
from src.api.schemas.stats import (
    CoverageStatsResponse,
    CoverageSummary,
    Distributions,
    CoverageMatrix,
    Gaps,
    LowCoverageCombination,
)
from src.api.schemas.workflow import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Canonical dimension values
CANONICAL_SURFACE_TYPES = {
    "carpets_floors", "clothes", "pillows_bedding", "upholstery",
    "hard_surfaces", "bathroom", "appliances", "outdoor"
}
CANONICAL_DIRT_TYPES = {
    "stain", "dust", "grease", "mold", "pet_hair", "odor", "water_stain", "ink"
}
CANONICAL_METHODS = {
    "vacuum", "hand_wash", "washing_machine", "spot_clean",
    "steam_clean", "dry_clean", "wipe", "scrub"
}


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
    "/stats/coverage",
    response_model=CoverageStatsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_coverage_stats(
    surface_type: Optional[str] = Query(None, description="Filter by surface type"),
    dirt_type: Optional[str] = Query(None, description="Filter by dirt type"),
    cleaning_method: Optional[str] = Query(None, description="Filter by cleaning method"),
    include_matrix: bool = Query(False, description="Include coverage matrix in response"),
    matrix_type: str = Query("full", description="Matrix type: surface_dirt, surface_method, dirt_method, full"),
) -> CoverageStatsResponse:
    """
    Get coverage statistics and matrices for the corpus.
    
    Args:
        surface_type: Optional surface type filter
        dirt_type: Optional dirt type filter
        cleaning_method: Optional cleaning method filter
        include_matrix: Include coverage matrix in response (default: false)
        matrix_type: Matrix type (default: "full")
        
    Returns:
        CoverageStatsResponse with coverage statistics
        
    Raises:
        HTTPException: With appropriate status code and error response
    """
    request_id = f"req-{uuid.uuid4().hex[:8]}"

    # Validate matrix_type
    valid_matrix_types = {"surface_dirt", "surface_method", "dirt_method", "full"}
    if matrix_type not in valid_matrix_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid matrix_type: '{matrix_type}'. Valid values: {', '.join(sorted(valid_matrix_types))}",
                "details": {
                    "parameter": "matrix_type",
                    "value": matrix_type,
                },
                "request_id": request_id,
            },
        )

    # Validate filter values
    if surface_type and surface_type not in CANONICAL_SURFACE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid surface_type: '{surface_type}'",
                "details": {"parameter": "surface_type", "value": surface_type},
                "request_id": request_id,
            },
        )

    if dirt_type and dirt_type not in CANONICAL_DIRT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid dirt_type: '{dirt_type}'",
                "details": {"parameter": "dirt_type", "value": dirt_type},
                "request_id": request_id,
            },
        )

    if cleaning_method and cleaning_method not in CANONICAL_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": f"Invalid cleaning_method: '{cleaning_method}'",
                "details": {"parameter": "cleaning_method", "value": cleaning_method},
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

        # Build WHERE clause for filters
        where_conditions = []
        if surface_type:
            where_conditions.append(f"surface_type = '{_escape_sql_string(surface_type)}'")
        if dirt_type:
            where_conditions.append(f"dirt_type = '{_escape_sql_string(dirt_type)}'")
        if cleaning_method:
            where_conditions.append(f"cleaning_method = '{_escape_sql_string(cleaning_method)}'")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Query fct_cleaning_procedures for summary statistics
        summary_query = f"""
        SELECT
            SUM(document_count) as total_documents,
            COUNT(*) as total_combinations,
            COUNT(DISTINCT surface_type) as surface_types_covered,
            COUNT(DISTINCT dirt_type) as dirt_types_covered,
            COUNT(DISTINCT cleaning_method) as methods_covered
        FROM cleaning_warehouse.fct_cleaning_procedures
        WHERE {where_clause}
        """

        summary_result = client.execute(summary_query)
        if summary_result and summary_result[0]:
            row = summary_result[0]
            total_documents = row[0] if row[0] else 0
            total_combinations = row[1] if row[1] else 0
            surface_types_covered = row[2] if row[2] else 0
            dirt_types_covered = row[3] if row[3] else 0
            methods_covered = row[4] if row[4] else 0
        else:
            total_documents = 0
            total_combinations = 0
            surface_types_covered = 0
            dirt_types_covered = 0
            methods_covered = 0

        # Calculate coverage percentage (512 = 8×8×8 possible combinations)
        total_possible_combinations = 512
        coverage_percentage = (total_combinations / total_possible_combinations * \
                               100.0) if total_possible_combinations > 0 else 0.0

        # Get distributions
        surface_dist_query = f"""
        SELECT
            surface_type,
            SUM(document_count) as doc_count
        FROM cleaning_warehouse.fct_cleaning_procedures
        WHERE {where_clause}
        GROUP BY surface_type
        ORDER BY doc_count DESC
        """
        surface_dist_result = client.execute(surface_dist_query)
        surface_distributions = {row[0]: row[1] for row in surface_dist_result} if surface_dist_result else {}

        dirt_dist_query = f"""
        SELECT
            dirt_type,
            SUM(document_count) as doc_count
        FROM cleaning_warehouse.fct_cleaning_procedures
        WHERE {where_clause}
        GROUP BY dirt_type
        ORDER BY doc_count DESC
        """
        dirt_dist_result = client.execute(dirt_dist_query)
        dirt_distributions = {row[0]: row[1] for row in dirt_dist_result} if dirt_dist_result else {}

        method_dist_query = f"""
        SELECT
            cleaning_method,
            SUM(document_count) as doc_count
        FROM cleaning_warehouse.fct_cleaning_procedures
        WHERE {where_clause}
        GROUP BY cleaning_method
        ORDER BY doc_count DESC
        """
        method_dist_result = client.execute(method_dist_query)
        method_distributions = {row[0]: row[1] for row in method_dist_result} if method_dist_result else {}

        # Build coverage matrix if requested
        coverage_matrix = None
        if include_matrix:
            matrix_data = {}

            if matrix_type in ("surface_dirt", "full"):
                # Surface × Dirt matrix
                surface_dirt_query = f"""
                SELECT
                    surface_type,
                    dirt_type,
                    SUM(document_count) as doc_count
                FROM cleaning_warehouse.fct_cleaning_procedures
                WHERE {where_clause}
                GROUP BY surface_type, dirt_type
                """
                surface_dirt_result = client.execute(surface_dirt_query)
                surface_dirt_matrix = {}
                for row in surface_dirt_result:
                    surf = row[0]
                    dirt = row[1]
                    count = row[2]
                    if surf not in surface_dirt_matrix:
                        surface_dirt_matrix[surf] = {}
                    surface_dirt_matrix[surf][dirt] = count
                matrix_data["surface_dirt"] = surface_dirt_matrix

            if matrix_type in ("surface_method", "full"):
                # Surface × Method matrix
                surface_method_query = f"""
                SELECT
                    surface_type,
                    cleaning_method,
                    SUM(document_count) as doc_count
                FROM cleaning_warehouse.fct_cleaning_procedures
                WHERE {where_clause}
                GROUP BY surface_type, cleaning_method
                """
                surface_method_result = client.execute(surface_method_query)
                surface_method_matrix = {}
                for row in surface_method_result:
                    surf = row[0]
                    method = row[1]
                    count = row[2]
                    if surf not in surface_method_matrix:
                        surface_method_matrix[surf] = {}
                    surface_method_matrix[surf][method] = count
                matrix_data["surface_method"] = surface_method_matrix

            if matrix_type in ("dirt_method", "full"):
                # Dirt × Method matrix
                dirt_method_query = f"""
                SELECT
                    dirt_type,
                    cleaning_method,
                    SUM(document_count) as doc_count
                FROM cleaning_warehouse.fct_cleaning_procedures
                WHERE {where_clause}
                GROUP BY dirt_type, cleaning_method
                """
                dirt_method_result = client.execute(dirt_method_query)
                dirt_method_matrix = {}
                for row in dirt_method_result:
                    dirt = row[0]
                    method = row[1]
                    count = row[2]
                    if dirt not in dirt_method_matrix:
                        dirt_method_matrix[dirt] = {}
                    dirt_method_matrix[dirt][method] = count
                matrix_data["dirt_method"] = dirt_method_matrix

            if matrix_type == "full":
                # Full 3D matrix: Surface × Dirt × Method
                full_query = f"""
                SELECT
                    surface_type,
                    dirt_type,
                    cleaning_method,
                    document_count
                FROM cleaning_warehouse.fct_cleaning_procedures
                WHERE {where_clause}
                ORDER BY surface_type, dirt_type, cleaning_method
                """
                full_result = client.execute(full_query)
                full_matrix = {}
                for row in full_result:
                    surf = row[0]
                    dirt = row[1]
                    method = row[2]
                    count = row[3]
                    if surf not in full_matrix:
                        full_matrix[surf] = {}
                    if dirt not in full_matrix[surf]:
                        full_matrix[surf][dirt] = {}
                    full_matrix[surf][dirt][method] = count
                matrix_data["full"] = full_matrix

            coverage_matrix = CoverageMatrix(
                type=matrix_type,
                matrix=matrix_data,
            )

        # Identify gaps
        # Missing surface types
        all_surface_types = set(CANONICAL_SURFACE_TYPES)
        covered_surface_types = set(surface_distributions.keys())
        missing_surface_types = sorted(list(all_surface_types - covered_surface_types))

        # Missing dirt types
        all_dirt_types = set(CANONICAL_DIRT_TYPES)
        covered_dirt_types = set(dirt_distributions.keys())
        missing_dirt_types = sorted(list(all_dirt_types - covered_dirt_types))

        # Missing methods
        all_methods = set(CANONICAL_METHODS)
        covered_methods = set(method_distributions.keys())
        missing_methods = sorted(list(all_methods - covered_methods))

        # Low coverage combinations (document_count <= 1)
        low_coverage_query = f"""
        SELECT
            surface_type,
            dirt_type,
            cleaning_method,
            document_count
        FROM cleaning_warehouse.fct_cleaning_procedures
        WHERE {where_clause}
          AND document_count <= 1
        ORDER BY document_count ASC, surface_type, dirt_type, cleaning_method
        LIMIT 50
        """
        low_coverage_result = client.execute(low_coverage_query)
        low_coverage_combinations = [
            LowCoverageCombination(
                surface_type=row[0],
                dirt_type=row[1],
                cleaning_method=row[2],
                document_count=row[3],
            )
            for row in low_coverage_result
        ] if low_coverage_result else []

        # Build response
        summary = CoverageSummary(
            total_documents=total_documents,
            total_combinations=total_combinations,
            total_possible_combinations=total_possible_combinations,
            coverage_percentage=round(coverage_percentage, 2),
            surface_types_covered=surface_types_covered,
            dirt_types_covered=dirt_types_covered,
            methods_covered=methods_covered,
        )

        distributions = Distributions(
            surface_types=surface_distributions,
            dirt_types=dirt_distributions,
            cleaning_methods=method_distributions,
        )

        gaps = Gaps(
            missing_surface_types=missing_surface_types,
            missing_dirt_types=missing_dirt_types,
            missing_methods=missing_methods,
            low_coverage_combinations=low_coverage_combinations,
        )

        return CoverageStatsResponse(
            summary=summary,
            distributions=distributions,
            coverage_matrix=coverage_matrix,
            gaps=gaps,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Handle database/service errors
        error_msg = str(e)
        logger.error(f"Database query failed in get_coverage_stats: {e}", exc_info=True)

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
                    "message": "Failed to compute coverage statistics",
                    "request_id": request_id,
                },
            )

    finally:
        # Clean up client connection
        if client:
            client.disconnect()


"""
Pydantic schemas for coverage statistics endpoint.

Matches API_DESIGN.md specifications exactly.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas (Query Parameters)
# ============================================================================

class CoverageStatsRequest(BaseModel):
    """Request schema for GET /stats/coverage (query parameters)."""
    surface_type: Optional[str] = Field(
        None,
        description="Filter by surface type",
        pattern="^(carpets_floors|clothes|pillows_bedding|upholstery|hard_surfaces|bathroom|appliances|outdoor)$"
    )
    dirt_type: Optional[str] = Field(
        None,
        description="Filter by dirt type",
        pattern="^(stain|dust|grease|mold|pet_hair|odor|water_stain|ink)$"
    )
    cleaning_method: Optional[str] = Field(
        None,
        description="Filter by cleaning method",
        pattern="^(vacuum|hand_wash|washing_machine|spot_clean|steam_clean|dry_clean|wipe|scrub)$"
    )
    include_matrix: Optional[bool] = Field(False, description="Include coverage matrix in response")
    matrix_type: Optional[str] = Field(
        "full",
        description="Matrix type",
        pattern="^(surface_dirt|surface_method|dirt_method|full)$"
    )


# ============================================================================
# Response Schemas
# ============================================================================

class CoverageSummary(BaseModel):
    """Coverage summary statistics."""
    total_documents: int
    total_combinations: int
    total_possible_combinations: int = Field(default=512, description="512 for 8×8×8")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0)
    surface_types_covered: int = Field(..., description="Out of 8")
    dirt_types_covered: int = Field(..., description="Out of 8")
    methods_covered: int = Field(..., description="Out of 8")


class Distributions(BaseModel):
    """Distribution of documents across dimensions."""
    surface_types: Dict[str, int]
    dirt_types: Dict[str, int]
    cleaning_methods: Dict[str, int]


class CoverageMatrix(BaseModel):
    """Coverage matrix structure."""
    type: str
    matrix: Dict[str, Dict]  # Flexible structure for different matrix types


class LowCoverageCombination(BaseModel):
    """Low coverage combination information."""
    surface_type: str
    dirt_type: str
    cleaning_method: str
    document_count: int


class Gaps(BaseModel):
    """Coverage gaps information."""
    missing_surface_types: List[str]
    missing_dirt_types: List[str]
    missing_methods: List[str]
    low_coverage_combinations: List[LowCoverageCombination]


class CoverageStatsResponse(BaseModel):
    """Response schema for GET /stats/coverage."""
    summary: CoverageSummary
    distributions: Distributions
    coverage_matrix: Optional[CoverageMatrix] = None
    gaps: Gaps


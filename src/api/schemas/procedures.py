"""
Pydantic schemas for procedure search endpoint.

Matches API_DESIGN.md specifications exactly.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas (Query Parameters)
# ============================================================================

class SearchProceduresRequest(BaseModel):
    """Request schema for GET /search_procedures (query parameters)."""
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
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: Optional[int] = Field(0, ge=0, description="Pagination offset")
    min_confidence: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Minimum extraction confidence")
    include_steps: Optional[bool] = Field(True, description="Include steps in response")
    include_tools: Optional[bool] = Field(True, description="Include tools in response")


# ============================================================================
# Response Schemas
# ============================================================================

class ProcedureStep(BaseModel):
    """Step in a procedure."""
    step_order: int
    step_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ProcedureTool(BaseModel):
    """Tool in a procedure."""
    tool_name: str
    category: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class Procedure(BaseModel):
    """Cleaning procedure document."""
    document_id: str
    url: str
    title: str
    surface_type: str
    dirt_type: str
    cleaning_method: str
    extraction_confidence: float = Field(..., ge=0.0, le=1.0)
    extraction_method: str
    steps: Optional[List[ProcedureStep]] = None
    tools: Optional[List[ProcedureTool]] = None
    fetched_at: str  # ISO 8601 datetime
    word_count: int


class SearchProceduresResponse(BaseModel):
    """Response schema for GET /search_procedures."""
    total: int
    limit: int
    offset: int
    procedures: List[Procedure]


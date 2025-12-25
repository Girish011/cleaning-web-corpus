"""
Pydantic schemas for workflow planning endpoint.

Matches API_DESIGN.md specifications exactly.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


# ============================================================================
# Request Schemas
# ============================================================================

class Constraints(BaseModel):
    """User constraints for workflow planning."""
    no_bleach: Optional[bool] = None
    no_harsh_chemicals: Optional[bool] = None
    preferred_method: Optional[str] = None
    gentle_only: Optional[bool] = None


class Context(BaseModel):
    """Additional context for workflow planning."""
    location: Optional[str] = None
    material: Optional[str] = None
    urgency: Optional[str] = Field(None, pattern="^(low|normal|high)$")


class PlanWorkflowRequest(BaseModel):
    """Request schema for POST /plan_workflow."""
    query: str = Field(..., description="Natural language description of cleaning scenario")
    surface_type: Optional[str] = Field(
        None,
        description="Pre-normalized surface type",
        pattern="^(carpets_floors|clothes|pillows_bedding|upholstery|hard_surfaces|bathroom|appliances|outdoor)$"
    )
    dirt_type: Optional[str] = Field(
        None,
        description="Pre-normalized dirt type",
        pattern="^(stain|dust|grease|mold|pet_hair|odor|water_stain|ink)$"
    )
    cleaning_method: Optional[str] = Field(
        None,
        description="Pre-normalized cleaning method",
        pattern="^(vacuum|hand_wash|washing_machine|spot_clean|steam_clean|dry_clean|wipe|scrub)$"
    )
    constraints: Optional[Constraints] = None
    context: Optional[Context] = None


# ============================================================================
# Response Schemas
# ============================================================================

class Scenario(BaseModel):
    """Normalized scenario information."""
    surface_type: str
    dirt_type: str
    cleaning_method: str
    normalized_query: str


class Step(BaseModel):
    """Workflow step."""
    step_number: int
    action: str
    description: str
    tools: List[str]
    duration_seconds: int
    order: int


class RequiredTool(BaseModel):
    """Required tool for workflow."""
    tool_name: str
    category: Optional[str] = None
    quantity: str
    is_required: bool
    alternative: Optional[str] = None


class Workflow(BaseModel):
    """Structured workflow."""
    estimated_duration_minutes: int
    difficulty: str = Field(..., pattern="^(easy|moderate|hard)$")
    steps: List[Step]
    required_tools: List[RequiredTool]
    safety_notes: List[str]
    tips: List[str]


class SourceDocument(BaseModel):
    """Source document reference."""
    document_id: str
    url: str
    title: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    extraction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class CorpusCoverage(BaseModel):
    """Corpus coverage information."""
    matching_documents: int
    total_combinations: int
    coverage_score: float = Field(..., ge=0.0, le=1.0)


class MethodCandidate(BaseModel):
    """Method candidate with score."""
    method: str
    score: float


class MethodSelection(BaseModel):
    """Method selection information."""
    chosen_method: str
    candidates: List[MethodCandidate]
    selection_reason: str


class Metadata(BaseModel):
    """Workflow generation metadata."""
    generated_at: str  # ISO 8601 datetime
    agent_version: str
    extraction_method: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    corpus_coverage: CorpusCoverage
    constraints_applied: Optional[List[str]] = None
    method_selection: Optional[MethodSelection] = None


class PlanWorkflowResponse(BaseModel):
    """Response schema for POST /plan_workflow."""
    workflow_id: str
    scenario: Scenario
    workflow: Workflow
    source_documents: List[SourceDocument]
    metadata: Metadata


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail information."""
    field: Optional[str] = None
    issue: Optional[str] = None
    parameter: Optional[str] = None
    value: Optional[str] = None
    max: Optional[int] = None


class Suggestion(BaseModel):
    """Suggestion for similar scenarios."""
    surface_type: Optional[str] = None
    dirt_type: Optional[str] = None
    cleaning_method: Optional[str] = None
    similarity_score: Optional[float] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: Optional[ErrorDetail] = None
    suggestions: Optional[List[Suggestion]] = None
    available_methods: Optional[List[str]] = None
    request_id: Optional[str] = None
    retry_after: Optional[int] = None


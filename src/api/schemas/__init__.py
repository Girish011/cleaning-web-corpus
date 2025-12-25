"""
Pydantic schemas for API request/response validation.

Schemas match the API design in docs/API_DESIGN.md.
"""

from src.api.schemas.workflow import (
    PlanWorkflowRequest,
    PlanWorkflowResponse,
    ErrorResponse,
    Constraints,
    Context,
    Scenario,
    Step,
    RequiredTool,
    Workflow,
    SourceDocument,
    Metadata,
    CorpusCoverage,
    MethodSelection,
)
from src.api.schemas.procedures import (
    SearchProceduresRequest,
    SearchProceduresResponse,
    Procedure,
    ProcedureStep,
    ProcedureTool,
)
from src.api.schemas.stats import (
    CoverageStatsRequest,
    CoverageStatsResponse,
    CoverageSummary,
    Distributions,
    CoverageMatrix,
    Gaps,
    LowCoverageCombination,
)

__all__ = [
    # Workflow schemas
    "PlanWorkflowRequest",
    "PlanWorkflowResponse",
    "ErrorResponse",
    "Constraints",
    "Context",
    "Scenario",
    "Step",
    "RequiredTool",
    "Workflow",
    "SourceDocument",
    "Metadata",
    "CorpusCoverage",
    "MethodSelection",
    # Procedure schemas
    "SearchProceduresRequest",
    "SearchProceduresResponse",
    "Procedure",
    "ProcedureStep",
    "ProcedureTool",
    # Stats schemas
    "CoverageStatsRequest",
    "CoverageStatsResponse",
    "CoverageSummary",
    "Distributions",
    "CoverageMatrix",
    "Gaps",
    "LowCoverageCombination",
]


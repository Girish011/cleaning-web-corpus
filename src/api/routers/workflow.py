"""
Workflow planning endpoint router.

Handles POST /plan_workflow requests with validation and error handling.
"""

import logging
import uuid
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from src.agents.workflow_planner import WorkflowPlannerAgent
from src.api.schemas.workflow import (
    PlanWorkflowRequest,
    PlanWorkflowResponse,
    ErrorResponse,
    Suggestion,
    ErrorDetail,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/plan_workflow",
    response_model=PlanWorkflowResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request body or missing required fields"},
        404: {"model": ErrorResponse, "description": "No matching procedures found in corpus"},
        422: {"model": ErrorResponse, "description": "Constraint conflict"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def plan_workflow(request: PlanWorkflowRequest) -> PlanWorkflowResponse:
    """
    Plan a structured cleaning workflow from a natural language query.
    
    Args:
        request: PlanWorkflowRequest with query and optional parameters
        
    Returns:
        PlanWorkflowResponse with structured workflow
        
    Raises:
        HTTPException: With appropriate status code and error response
    """
    request_id = f"req-{uuid.uuid4().hex[:8]}"

    try:
        # Initialize agent
        agent = WorkflowPlannerAgent()

        try:
            # Convert constraints to dict
            constraints = {}
            if request.constraints:
                if request.constraints.no_bleach:
                    constraints["no_bleach"] = True
                if request.constraints.no_harsh_chemicals:
                    constraints["no_harsh_chemicals"] = True
                if request.constraints.preferred_method:
                    constraints["preferred_method"] = request.constraints.preferred_method
                if request.constraints.gentle_only:
                    constraints["gentle_only"] = True

            # Convert context to dict
            context = {}
            if request.context:
                if request.context.location:
                    context["location"] = request.context.location
                if request.context.material:
                    context["material"] = request.context.material
                if request.context.urgency:
                    context["urgency"] = request.context.urgency

            # Call agent to plan workflow
            result = agent.plan_workflow(
                query=request.query,
                surface_type=request.surface_type,
                dirt_type=request.dirt_type,
                cleaning_method=request.cleaning_method,
                constraints=constraints if constraints else None,
                context=context if context else None,
            )

            # Convert agent result to response schema
            response = _convert_to_response(result, constraints)

            return response

        except ValueError as e:
            # Handle no match found, insufficient steps, or invalid input
            error_msg = str(e)

            if (
                "No matching" in error_msg
                or "Could not extract" in error_msg
                or "Insufficient steps" in error_msg
            ):
                # 404: No match found or insufficient steps
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "no_match_found",
                        "message": error_msg,
                        "suggestions": _get_suggestions(request),
                        "request_id": request_id,
                    },
                )
            else:
                # 400: Validation error
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "validation_error",
                        "message": error_msg,
                        "details": {"field": "query", "issue": "invalid"},
                        "request_id": request_id,
                    },
                )

        except RuntimeError as e:
            # Handle database/service errors
            error_msg = str(e)

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
                logger.error(f"Workflow planning failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "internal_error",
                        "message": f"Workflow planning failed: {error_msg}",
                        "request_id": request_id,
                    },
                )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error in plan_workflow: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "internal_error",
                    "message": "Workflow planning failed due to unexpected error",
                    "request_id": request_id,
                },
            )

        finally:
            # Clean up agent resources
            agent.close()

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Catch-all for errors before agent initialization
        logger.error(f"Error initializing agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Failed to initialize workflow planner agent",
                "request_id": request_id,
            },
        )


def _convert_to_response(
    agent_result: Dict[str, Any], constraints: Dict[str, Any]
) -> PlanWorkflowResponse:
    """
    Convert agent result dictionary to PlanWorkflowResponse schema.
    
    Args:
        agent_result: Dictionary from WorkflowPlannerAgent.plan_workflow()
        constraints: User constraints dictionary
        
    Returns:
        PlanWorkflowResponse instance
    """
    from src.api.schemas.workflow import (
        Scenario,
        Workflow,
        Step,
        RequiredTool,
        SourceDocument,
        Metadata,
        CorpusCoverage,
        MethodSelection,
    )

    # Build constraints_applied list
    constraints_applied = []
    if constraints.get("no_bleach"):
        constraints_applied.append("no_bleach")
    if constraints.get("no_harsh_chemicals"):
        constraints_applied.append("no_harsh_chemicals")
    if constraints.get("gentle_only"):
        constraints_applied.append("gentle_only")
    if constraints.get("preferred_method"):
        constraints_applied.append("preferred_method")

    # Build method_selection if available
    method_selection = None
    if "metadata" in agent_result and "method_selection" in agent_result["metadata"]:
        from src.api.schemas.workflow import MethodCandidate
        ms_data = agent_result["metadata"]["method_selection"]
        candidates = [
            MethodCandidate(method=c["method"], score=c["score"])
            for c in ms_data.get("candidates", [])
        ]
        method_selection = MethodSelection(
            chosen_method=ms_data.get("chosen_method", ""),
            candidates=candidates,
            selection_reason=ms_data.get("selection_reason", ""),
        )

    # Convert workflow steps
    workflow_data = agent_result["workflow"]
    steps = [
        Step(
            step_number=s["step_number"],
            action=s["action"],
            description=s["description"],
            tools=s["tools"],
            duration_seconds=s["duration_seconds"],
            order=s["order"],
        )
        for s in workflow_data["steps"]
    ]

    # Convert required tools
    required_tools = [
        RequiredTool(
            tool_name=t["tool_name"],
            category=t.get("category"),
            quantity=t["quantity"],
            is_required=t["is_required"],
            alternative=t.get("alternative"),
        )
        for t in workflow_data["required_tools"]
    ]

    # Convert source documents (deduplicate by document_id as defensive measure)
    seen_doc_ids = set()
    source_documents = []
    for d in agent_result["source_documents"]:
        doc_id = d.get("document_id")
        if doc_id and doc_id not in seen_doc_ids:
            seen_doc_ids.add(doc_id)
            source_documents.append(
                SourceDocument(
                    document_id=doc_id,
                    url=d["url"],
                    title=d["title"],
                    relevance_score=d.get("relevance_score", 0.9),
                    extraction_confidence=d.get("extraction_confidence"),
                )
            )

    # Build metadata
    metadata_data = agent_result["metadata"]
    corpus_coverage = CorpusCoverage(
        matching_documents=metadata_data["corpus_coverage"]["matching_documents"],
        total_combinations=metadata_data["corpus_coverage"]["total_combinations"],
        coverage_score=metadata_data["corpus_coverage"]["coverage_score"],
    )

    metadata = Metadata(
        generated_at=metadata_data["generated_at"],
        agent_version=metadata_data["agent_version"],
        extraction_method=metadata_data["extraction_method"],
        confidence=metadata_data["confidence"],
        corpus_coverage=corpus_coverage,
        constraints_applied=constraints_applied if constraints_applied else None,
        method_selection=method_selection,
    )

    # Build workflow
    workflow = Workflow(
        estimated_duration_minutes=workflow_data["estimated_duration_minutes"],
        difficulty=workflow_data["difficulty"],
        steps=steps,
        required_tools=required_tools,
        safety_notes=workflow_data["safety_notes"],
        tips=workflow_data["tips"],
    )

    # Build scenario
    scenario_data = agent_result["scenario"]
    scenario = Scenario(
        surface_type=scenario_data["surface_type"],
        dirt_type=scenario_data["dirt_type"],
        cleaning_method=scenario_data["cleaning_method"],
        normalized_query=scenario_data["normalized_query"],
    )

    return PlanWorkflowResponse(
        workflow_id=agent_result["workflow_id"],
        scenario=scenario,
        workflow=workflow,
        source_documents=source_documents,
        metadata=metadata,
    )


def _get_suggestions(request: PlanWorkflowRequest) -> list[Suggestion]:
    """
    Get suggestions for similar scenarios when no match found.
    
    Args:
        request: Original request
        
    Returns:
        List of suggestion dictionaries
    """
    # Try to find similar scenarios using search_similar_scenarios tool
    try:
        from src.agents.tools import SearchSimilarScenariosTool

        tool = SearchSimilarScenariosTool()
        try:
            if request.surface_type and request.dirt_type:
                result = tool.execute(
                    surface_type=request.surface_type,
                    dirt_type=request.dirt_type,
                    fuzzy_match=True,
                    limit=3,
                )
                similar = result.get("similar_combinations", [])
                return [
                    Suggestion(
                        surface_type=s["surface_type"],
                        dirt_type=s["dirt_type"],
                        cleaning_method=s["cleaning_method"],
                        similarity_score=s["similarity_score"],
                    )
                    for s in similar
                ]
        finally:
            tool.close()
    except Exception as e:
        logger.warning(f"Failed to get suggestions: {e}")

    return []

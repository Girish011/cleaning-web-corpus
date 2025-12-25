"""
Workflow Planner Agent for generating structured cleaning workflows.

Implements the 4-phase planning strategy:
1. Parse & Normalize - Extract and normalize entities from query
2. Fetch & Retrieve - Query data warehouse using tools
3. Compose & Generate - Build structured workflow
4. Validate & Refine - Check completeness and constraints
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from src.agents.composition import WorkflowComposer
from src.agents.normalization import Normalizer, get_normalizer
from src.agents.tools import (
    FetchMethodsTool,
    FetchStepsTool,
    FetchToolsTool,
    FetchReferenceContextTool,
    SearchSimilarScenariosTool,
)
from src.config import get_config

logger = logging.getLogger(__name__)


class WorkflowPlannerAgent:
    """
    Workflow Planner Agent that generates structured cleaning workflows.
    
    Follows the 4-phase planning strategy from WORKFLOW_AGENT_DESIGN.md:
    1. Parse & Normalize: Extract entities and normalize to canonical values
    2. Fetch & Retrieve: Query data warehouse using agent tools
    3. Compose & Generate: Build structured workflow with steps, tools, safety notes
    4. Validate & Refine: Check completeness, constraints, and quality
    """

    def __init__(
        self,
        normalizer: Optional[Normalizer] = None,
        composer: Optional[WorkflowComposer] = None,
        enable_llm_enrichment: bool = False,
    ):
        """
        Initialize the workflow planner agent.
        
        Args:
            normalizer: Optional normalizer instance (creates default if None)
            composer: Optional workflow composer instance (creates default if None)
            enable_llm_enrichment: Whether to use LLM for step enrichment
        """
        self.normalizer = normalizer or get_normalizer()
        self.composer = composer or WorkflowComposer(
            enable_llm_enrichment=enable_llm_enrichment
        )

        # Load config for workflow settings
        config = get_config()
        self.min_steps = config.workflow.min_steps
        self.allow_fewer_steps_if_limited_data = config.workflow.allow_fewer_steps_if_limited_data

        # Initialize tools
        self.fetch_methods = FetchMethodsTool()
        self.fetch_steps = FetchStepsTool()
        self.fetch_tools = FetchToolsTool()
        self.fetch_reference_context = FetchReferenceContextTool()
        self.search_similar_scenarios = SearchSimilarScenariosTool()

    def plan_workflow(
        self,
        query: str,
        surface_type: Optional[str] = None,
        dirt_type: Optional[str] = None,
        cleaning_method: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured workflow plan from user query.
        
        Args:
            query: Natural language query describing cleaning scenario
            surface_type: Optional pre-normalized surface type
            dirt_type: Optional pre-normalized dirt type
            cleaning_method: Optional pre-normalized cleaning method
            constraints: Optional user constraints (no_bleach, no_harsh_chemicals, etc.)
            context: Optional additional context (location, material, urgency)
            
        Returns:
            Structured workflow dictionary matching WORKFLOW_AGENT_DESIGN.md output schema
            
        Raises:
            ValueError: If query is invalid or no matching procedures found
        """
        if not query:
            raise ValueError("Query cannot be empty")

        constraints = constraints or {}
        context = context or {}

        # Phase 1: Parse & Normalize
        logger.info("Phase 1: Parse & Normalize")
        normalized = self._parse_and_normalize(
            query, surface_type, dirt_type, cleaning_method
        )

        if not normalized["surface_type"] or not normalized["dirt_type"]:
            raise ValueError(
                "Could not extract surface_type and dirt_type from query. "
                "Please provide more specific information."
            )

        # Phase 2: Fetch & Retrieve
        logger.info("Phase 2: Fetch & Retrieve")
        retrieved = self._fetch_and_retrieve(
            normalized, constraints, context
        )

        if not retrieved["methods"]:
            # Try similar scenarios
            logger.info("No exact match found, searching similar scenarios")
            similar = self._try_similar_scenarios(normalized)
            if similar:
                # Use first similar scenario
                normalized["surface_type"] = similar[0]["surface_type"]
                normalized["dirt_type"] = similar[0]["dirt_type"]
                normalized["cleaning_method"] = similar[0]["cleaning_method"]
                retrieved = self._fetch_and_retrieve(normalized, constraints, context)
            else:
                raise ValueError(
                    "No matching cleaning procedures found. "
                    "Please try a different query or check the corpus coverage."
                )

        # Phase 3: Compose & Generate
        logger.info("Phase 3: Compose & Generate")
        workflow = self._compose_and_generate(
            normalized, retrieved, constraints, context
        )

        # Phase 4: Validate & Refine
        logger.info("Phase 4: Validate & Refine")
        validated = self._validate_and_refine(
            workflow, normalized, retrieved, constraints
        )

        # Build final output
        return self._build_output(validated, normalized, retrieved)

    def _parse_and_normalize(
        self,
        query: str,
        surface_type: Optional[str],
        dirt_type: Optional[str],
        cleaning_method: Optional[str],
    ) -> Dict[str, Any]:
        """
        Phase 1: Parse and normalize entities from query.
        
        Args:
            query: Natural language query
            surface_type: Optional pre-normalized surface type
            dirt_type: Optional pre-normalized dirt type
            cleaning_method: Optional pre-normalized cleaning method
            
        Returns:
            Dictionary with normalized surface_type, dirt_type, cleaning_method
        """
        # Use pre-normalized values if provided
        if surface_type:
            surface = self.normalizer.normalize_surface(surface_type)
            if not surface:
                surface = surface_type  # Use as-is if normalization fails
        else:
            # Extract from query
            surface, _, _ = self.normalizer.extract_and_normalize(query)

        if dirt_type:
            dirt = self.normalizer.normalize_dirt(dirt_type)
            if not dirt:
                dirt = dirt_type  # Use as-is if normalization fails
        else:
            # Extract from query
            _, dirt, _ = self.normalizer.extract_and_normalize(query)

        if cleaning_method:
            method = self.normalizer.normalize_method(cleaning_method)
            if not method:
                method = cleaning_method  # Use as-is if normalization fails
        else:
            # Extract from query
            _, _, method = self.normalizer.extract_and_normalize(query)

        # Validate normalized values
        if surface and not self.normalizer.is_valid_surface(surface):
            logger.warning(f"Invalid surface type: {surface}")
            surface = None

        if dirt and not self.normalizer.is_valid_dirt(dirt):
            logger.warning(f"Invalid dirt type: {dirt}")
            dirt = None

        if method and not self.normalizer.is_valid_method(method):
            logger.warning(f"Invalid method: {method}")
            method = None

        # Detect wool nuance
        is_wool = self.normalizer.detect_wool_nuance(query)

        return {
            "surface_type": surface,
            "dirt_type": dirt,
            "cleaning_method": method,
            "normalized_query": query,  # Can be enhanced with LLM
            "is_wool": is_wool,  # Internal flag for wool material detection
        }

    def _fetch_and_retrieve(
        self,
        normalized: Dict[str, Any],
        constraints: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Phase 2: Fetch and retrieve data from warehouse.
        
        Args:
            normalized: Normalized scenario (surface, dirt, method)
            constraints: User constraints
            context: Additional context
            
        Returns:
            Dictionary with methods, steps, tools, and reference documents
        """
        surface = normalized["surface_type"]
        dirt = normalized["dirt_type"]
        method = normalized.get("cleaning_method")

        # Fetch available methods
        methods_result = self.fetch_methods.execute(
            surface_type=surface, dirt_type=dirt
        )
        methods = methods_result.get("methods", [])

        if not methods:
            return {
                "methods": [],
                "steps": [],
                "tools": [],
                "reference_documents": [],
            }

        # Select method (pass normalized query, dirt_type, and is_wool for relevance scoring)
        method_selection_result = self._select_method(
            methods, method, constraints, normalized.get("normalized_query", ""),
            normalized.get("dirt_type"), normalized.get("is_wool", False)
        )
        selected_method = method_selection_result["chosen_method"]
        method_selection_metadata = method_selection_result["metadata"]

        if not selected_method:
            selected_method = methods[0]["cleaning_method"]

        # Fetch steps
        steps_result = self.fetch_steps.execute(
            surface_type=surface,
            dirt_type=dirt,
            cleaning_method=selected_method,
            limit=20,
        )
        steps = steps_result.get("steps", [])

        # Fetch tools
        tools_result = self.fetch_tools.execute(
            surface_type=surface,
            dirt_type=dirt,
            cleaning_method=selected_method,
        )
        tools = tools_result.get("tools", [])

        # Get reference documents (top 5 by document_id frequency)
        document_ids = list(
            set(step.get("document_id") for step in steps[:20])
        )[:5]

        reference_docs = []
        if document_ids:
            ref_result = self.fetch_reference_context.execute(
                document_ids=document_ids,
                include_steps=True,
                include_tools=True,
            )
            reference_docs = ref_result.get("documents", [])

        return {
            "methods": methods,
            "selected_method": selected_method,
            "method_selection_metadata": method_selection_metadata,
            "steps": steps,
            "tools": tools,
            "reference_documents": reference_docs,
        }

    def _select_method(
        self,
        methods: List[Dict[str, Any]],
        user_method: Optional[str],
        constraints: Dict[str, Any],
        normalized_query: str = "",
        dirt_type: Optional[str] = None,
        is_wool: bool = False,
    ) -> Dict[str, Any]:
        """
        Select best cleaning method from available options, prioritizing relevance over document count.
        For stain scenarios, forces stain-focused methods (spot_clean) and treats vacuum as secondary.
        For wool+stain scenarios without stain-focused methods, synthesizes spot_clean.
        
        Args:
            methods: List of available methods
            user_method: Optional user-specified method
            constraints: User constraints
            normalized_query: Original query text for keyword analysis
            dirt_type: Normalized dirt type for context-aware selection
            is_wool: Whether the surface is wool material
            
        Returns:
            Dictionary with 'chosen_method' and 'metadata' containing method_selection info
        """
        query_lower = normalized_query.lower() if normalized_query else ""
        is_stain_scenario = (
            dirt_type and dirt_type.lower() == "stain"
        ) or any(
            keyword in query_lower
            for keyword in ["stain", "spill", "wine", "coffee", "ink", "mark", "blot"]
        )

        # If user specified method, use it if available
        if user_method:
            for method in methods:
                if method["cleaning_method"] == user_method:
                    candidates = [
                        {
                            "method": m["cleaning_method"],
                            "score": 1.0 if m["cleaning_method"] == user_method else 0.0,
                        }
                        for m in methods
                    ]
                    return {
                        "chosen_method": user_method,
                        "metadata": {
                            "chosen_method": user_method,
                            "candidates": candidates,
                            "selection_reason": f"User specified method: {user_method}",
                        },
                    }

        # For stain scenarios, force stain-focused methods and deprioritize vacuum
        # Special case: wool+stain without stain-focused methods -> synthesize spot_clean
        if is_stain_scenario:
            # Filter to stain-focused methods first
            stain_focused_methods = ["spot_clean", "scrub", "wipe", "hand_wash"]
            available_stain_methods = [
                m for m in methods if m["cleaning_method"] in stain_focused_methods
            ]

            # If we have stain-focused methods, use them
            if available_stain_methods:
                methods_to_score = available_stain_methods
                # Mark vacuum as secondary (lower priority)
                vacuum_penalty = True
            else:
                # No stain-focused methods available
                # Special case: wool+stain+gentle constraints -> synthesize spot_clean
                if is_wool and (constraints.get("gentle_only") or constraints.get("no_harsh_chemicals")):
                    # Synthesize spot_clean for wool+stain scenarios
                    # Include corpus methods as lower-scored candidates
                    corpus_candidates = [
                        {
                            "method": m["cleaning_method"],
                            "score": max(0.0, self._calculate_method_relevance(
                                m["cleaning_method"], normalized_query, dirt_type
                            ) * 0.3),  # Lower score for corpus methods
                        }
                        for m in methods
                    ]

                    # Add synthesized spot_clean as top candidate
                    candidates = [
                        {
                            "method": "spot_clean",
                            "score": 1.0,  # Highest score for synthesized method
                        }
                    ] + corpus_candidates

                    selection_reason = (
                        "Wool material detected with stain scenario. "
                        "No stain-focused methods available in corpus, but wool + stain + gentle constraints "
                        "require a gentle spot cleaning approach. Synthesized spot_clean method as primary; "
                        "corpus methods (vacuum, etc.) are secondary options."
                    )

                    logger.info(
                        f"Synthesized spot_clean for wool+stain scenario "
                        f"(wool={is_wool}, stain={is_stain_scenario}, gentle={constraints.get('gentle_only')})"
                    )

                    return {
                        "chosen_method": "spot_clean",
                        "metadata": {
                            "chosen_method": "spot_clean",
                            "candidates": candidates,
                            "selection_reason": selection_reason,
                        },
                    }
                else:
                    # No stain-focused methods available, use all methods but still penalize vacuum
                    methods_to_score = methods
                    vacuum_penalty = True
        else:
            methods_to_score = methods
            vacuum_penalty = False

        # Apply constraints
        if constraints.get("no_harsh_chemicals") or constraints.get("gentle_only"):
            # Prefer gentle methods
            gentle_methods = ["spot_clean", "wipe", "vacuum", "hand_wash"]
            gentle_available = [
                m for m in methods_to_score if m["cleaning_method"] in gentle_methods
            ]
            if gentle_available:
                methods_to_score = gentle_available

        # Score methods based on relevance and document count
        scored_methods = []
        for method in methods_to_score:
            method_name = method["cleaning_method"]
            relevance_score = self._calculate_method_relevance(
                method_name, normalized_query, dirt_type
            )
            document_count = method.get("document_count", 0)
            avg_confidence = method.get("avg_confidence", 0.0)

            # Penalize vacuum for stain scenarios
            if vacuum_penalty and method_name == "vacuum":
                relevance_score = max(0.0, relevance_score - 0.5)

            # Combined score: relevance first (weighted 2x), then document count, then confidence
            # Normalize document count to 0-1 range (assuming max ~50 documents)
            normalized_doc_count = min(document_count / 50.0, 1.0)

            combined_score = (
                relevance_score * 2.0 +  # Prioritize relevance (2x weight)
                normalized_doc_count * 0.5 +  # Document count (0.5x weight)
                avg_confidence * 0.5  # Confidence (0.5x weight)
            )

            scored_methods.append({
                "method": method_name,
                "relevance_score": relevance_score,
                "document_count": document_count,
                "avg_confidence": avg_confidence,
                "combined_score": combined_score,
            })

        # Sort by combined score (descending)
        scored_methods.sort(key=lambda m: m["combined_score"], reverse=True)

        # Build candidates list with all scored methods
        candidates = [
            {
                "method": m["method"],
                "score": m["combined_score"],
            }
            for m in scored_methods
        ]

        if scored_methods:
            best_method = scored_methods[0]
            chosen_method = best_method["method"]

            # Build selection reason
            if is_stain_scenario:
                if chosen_method == "spot_clean":
                    selection_reason = (
                        "Stain scenario detected: stain keywords matched spot_clean method. "
                        "Spot cleaning is the primary method for stain removal; vacuum is secondary."
                    )
                elif chosen_method in ["scrub", "wipe", "hand_wash"]:
                    selection_reason = (
                        f"Stain scenario detected: {chosen_method} selected as stain-focused method. "
                        "Vacuum treated as secondary for stain removal."
                    )
                else:
                    selection_reason = (
                        f"Stain scenario detected: {chosen_method} selected (stain-focused methods not available). "
                        "Vacuum would be secondary if available."
                    )
            else:
                selection_reason = (
                    f"Selected {chosen_method} based on relevance score ({best_method['relevance_score']:.2f}), "
                    f"document count ({best_method['document_count']}), and confidence ({best_method['avg_confidence']:.2f})."
                )

            if constraints.get("gentle_only") or constraints.get("no_harsh_chemicals"):
                selection_reason += " Constraints require gentle method."

            logger.info(
                f"Selected method '{chosen_method}' "
                f"(relevance: {best_method['relevance_score']:.2f}, "
                f"doc_count: {best_method['document_count']}, "
                f"combined_score: {best_method['combined_score']:.2f})"
            )

            return {
                "chosen_method": chosen_method,
                "metadata": {
                    "chosen_method": chosen_method,
                    "candidates": candidates,
                    "selection_reason": selection_reason,
                },
            }

        # Fallback: select method with highest document count
        best_method = max(
            methods,
            key=lambda m: (
                m.get("document_count", 0),
                m.get("avg_confidence", 0.0),
            ),
        )
        chosen_method = best_method["cleaning_method"]
        candidates = [
            {
                "method": m["cleaning_method"],
                "score": m.get("document_count", 0) / 50.0,  # Normalized doc count as score
            }
            for m in methods
        ]

        return {
            "chosen_method": chosen_method,
            "metadata": {
                "chosen_method": chosen_method,
                "candidates": candidates,
                "selection_reason": f"Fallback: selected {chosen_method} based on highest document count.",
            },
        }

    def _calculate_method_relevance(
        self,
        method_name: str,
        normalized_query: str,
        dirt_type: Optional[str],
    ) -> float:
        """
        Calculate relevance score for a cleaning method based on query context.
        
        Uses keyword-based method hints to match methods to query intent.
        
        Args:
            method_name: Cleaning method name
            normalized_query: Original query text
            dirt_type: Normalized dirt type
            
        Returns:
            Relevance score (0.0-1.0)
        """
        query_lower = normalized_query.lower() if normalized_query else ""
        method_lower = method_name.lower()

        # Keyword-based method hints
        method_hints = {
            "spot_clean": [
                "stain", "spot", "spill", "remove stain", "treat stain",
                "wine", "coffee", "ink", "mark", "blot",
            ],
            "steam_clean": [
                "deep clean", "deep cleaning", "steam", "sanitize",
                "disinfect", "thorough", "deep",
            ],
            "vacuum": [
                "maintenance", "regular", "routine", "dust", "pet hair",
                "debris", "vacuum", "suck", "pick up",
            ],
            "hand_wash": [
                "hand wash", "handwash", "manual", "by hand", "gentle",
                "delicate", "careful",
            ],
            "washing_machine": [
                "machine", "washer", "laundry", "bulk", "load",
            ],
            "dry_clean": [
                "dry clean", "dryclean", "professional", "delicate fabric",
            ],
            "wipe": [
                "wipe", "clean surface", "quick", "surface clean",
            ],
            "scrub": [
                "scrub", "tough", "stubborn", "hard", "difficult",
            ],
        }

        # Base relevance score
        relevance = 0.0

        # Check method-specific keywords in query
        if method_lower in method_hints:
            hints = method_hints[method_lower]
            for hint in hints:
                if hint in query_lower:
                    relevance += 0.3  # Strong match
                    break

        # Dirt-type specific method preferences
        if dirt_type:
            dirt_lower = dirt_type.lower()

            # Stain removal should prefer spot_clean
            if dirt_lower == "stain" and method_lower == "spot_clean":
                relevance += 0.5
            elif dirt_lower == "stain" and method_lower == "vacuum":
                relevance -= 0.3  # Penalize vacuum for stains

            # Dust should prefer vacuum
            if dirt_lower == "dust" and method_lower == "vacuum":
                relevance += 0.4
            elif dirt_lower == "dust" and method_lower == "spot_clean":
                relevance -= 0.2  # Penalize spot_clean for dust

            # Pet hair should prefer vacuum
            if dirt_lower == "pet_hair" and method_lower == "vacuum":
                relevance += 0.4

            # Grease should prefer scrub or steam_clean
            if dirt_lower == "grease" and method_lower in ["scrub", "steam_clean"]:
                relevance += 0.3

            # Mold should prefer scrub or steam_clean
            if dirt_lower == "mold" and method_lower in ["scrub", "steam_clean"]:
                relevance += 0.3

        # Query context analysis
        # "deep clean" → prefer steam_clean
        if "deep clean" in query_lower or "deep cleaning" in query_lower:
            if method_lower == "steam_clean":
                relevance += 0.4
            elif method_lower == "vacuum":
                relevance -= 0.2

        # "maintenance" → prefer vacuum
        if "maintenance" in query_lower or "routine" in query_lower:
            if method_lower == "vacuum":
                relevance += 0.3
            elif method_lower == "spot_clean":
                relevance -= 0.2

        # "stain" in query → prefer spot_clean
        if "stain" in query_lower:
            if method_lower == "spot_clean":
                relevance += 0.5
            elif method_lower == "vacuum":
                relevance -= 0.3

        # "remove" or "treat" → prefer spot_clean or scrub
        if "remove" in query_lower or "treat" in query_lower:
            if method_lower in ["spot_clean", "scrub"]:
                relevance += 0.2

        # Normalize to 0.0-1.0 range
        return min(1.0, max(0.0, relevance))

    def _try_similar_scenarios(
        self, normalized: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Try to find similar scenarios when exact match not found.
        
        Args:
            normalized: Normalized scenario
            
        Returns:
            List of similar scenario dictionaries
        """
        try:
            result = self.search_similar_scenarios.execute(
                surface_type=normalized["surface_type"],
                dirt_type=normalized["dirt_type"],
                fuzzy_match=True,
                limit=5,
            )
            return result.get("similar_combinations", [])
        except Exception as e:
            logger.warning(f"Error searching similar scenarios: {e}")
            return []

    def _find_additional_steps(
        self,
        normalized: Dict[str, Any],
        retrieved: Dict[str, Any],
        current_step_count: int,
    ) -> List[Dict[str, Any]]:
        """
        Find additional steps from similar scenarios when workflow has insufficient steps.
        
        Args:
            normalized: Normalized scenario
            retrieved: Retrieved data
            current_step_count: Current number of steps in workflow
            
        Returns:
            List of additional step dictionaries
        """
        steps_needed = self.min_steps - current_step_count
        if steps_needed <= 0:
            return []

        additional_steps = []

        try:
            # Search for similar scenarios
            similar_result = self.search_similar_scenarios.execute(
                surface_type=normalized["surface_type"],
                dirt_type=normalized["dirt_type"],
                fuzzy_match=True,
                limit=3,  # Try top 3 similar scenarios
            )
            similar_combinations = similar_result.get("similar_combinations", [])

            # Try to fetch steps from similar scenarios
            for combo in similar_combinations:
                if len(additional_steps) >= steps_needed:
                    break

                try:
                    similar_steps_result = self.fetch_steps.execute(
                        surface_type=combo.get("surface_type"),
                        dirt_type=combo.get("dirt_type"),
                        cleaning_method=combo.get("cleaning_method"),
                        limit=steps_needed,
                    )
                    similar_steps = similar_steps_result.get("steps", [])

                    # Add steps that aren't already in the workflow
                    existing_step_texts = {
                        s.get("step_text", "").lower()
                        for s in retrieved.get("steps", [])
                    }

                    for step in similar_steps:
                        if len(additional_steps) >= steps_needed:
                            break
                        step_text = step.get("step_text", "").lower()
                        if step_text not in existing_step_texts:
                            additional_steps.append(step)
                            existing_step_texts.add(step_text)

                except Exception as e:
                    logger.warning(
                        f"Error fetching steps from similar scenario {combo}: {e}"
                    )
                    continue

        except Exception as e:
            logger.warning(f"Error searching for additional steps: {e}")

        logger.info(
            f"Found {len(additional_steps)} additional steps from similar scenarios "
            f"(needed {steps_needed})"
        )

        return additional_steps

    def _compose_and_generate(
        self,
        normalized: Dict[str, Any],
        retrieved: Dict[str, Any],
        constraints: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Phase 3: Compose and generate structured workflow.
        
        Args:
            normalized: Normalized scenario
            retrieved: Retrieved data from warehouse
            constraints: User constraints
            context: Additional context
            
        Returns:
            Workflow dictionary
        """
        scenario = {
            "surface_type": normalized["surface_type"],
            "dirt_type": normalized["dirt_type"],
            "cleaning_method": retrieved["selected_method"],
            "normalized_query": normalized["normalized_query"],
        }

        workflow = self.composer.compose_workflow(
            steps=retrieved["steps"],
            tools=retrieved["tools"],
            reference_documents=retrieved["reference_documents"],
            scenario=scenario,
            constraints=constraints,
        )

        return workflow

    def _validate_and_refine(
        self,
        workflow: Dict[str, Any],
        normalized: Dict[str, Any],
        retrieved: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Phase 4: Validate and refine workflow.
        
        Args:
            workflow: Generated workflow
            normalized: Normalized scenario
            retrieved: Retrieved data
            constraints: User constraints
            
        Returns:
            Validated and refined workflow
            
        Raises:
            ValueError: If workflow has fewer than 3 steps and cannot find additional steps
        """
        steps = workflow.get("steps", [])

        # Determine effective minimum step count
        effective_min_steps = self.min_steps
        if self.allow_fewer_steps_if_limited_data and len(steps) >= 2:
            # If we have at least 2 steps and limited data mode is enabled,
            # allow 2 steps as minimum (but still try to find more)
            effective_min_steps = max(2, self.min_steps - 1)

        # Enforce minimum step count
        if len(steps) < effective_min_steps:
            logger.warning(
                f"Workflow has only {len(steps)} steps, minimum {effective_min_steps} required. "
                "Attempting to find additional steps from similar scenarios..."
            )

            # Try to find additional steps from similar scenarios
            additional_steps = self._find_additional_steps(
                normalized, retrieved, len(steps)
            )

            if additional_steps:
                # Combine original steps with additional steps
                original_steps = retrieved.get("steps", [])
                combined_steps = original_steps.copy()

                # Add additional steps (avoid duplicates)
                existing_step_texts = {
                    s.get("step_text", "").lower() for s in combined_steps
                }
                for step in additional_steps:
                    step_text = step.get("step_text", "").lower()
                    # Only add if not duplicate
                    if step_text not in existing_step_texts:
                        combined_steps.append(step)
                        existing_step_texts.add(step_text)

                # Re-compose workflow with combined steps
                if len(combined_steps) >= effective_min_steps:
                    logger.info(
                        f"Found {len(additional_steps)} additional steps. "
                        f"Total steps now: {len(combined_steps)}"
                    )
                    # Re-compose workflow with updated steps
                    scenario = {
                        "surface_type": normalized["surface_type"],
                        "dirt_type": normalized["dirt_type"],
                        "cleaning_method": retrieved["selected_method"],
                        "normalized_query": normalized["normalized_query"],
                    }
                    workflow = self.composer.compose_workflow(
                        steps=combined_steps,
                        tools=retrieved["tools"],
                        reference_documents=retrieved["reference_documents"],
                        scenario=scenario,
                        constraints=constraints,
                    )
                    # Update steps after re-composition
                    steps = workflow.get("steps", [])

            # Use absolute minimum of 2 if allow_fewer_steps_if_limited_data is enabled
            absolute_min = 2 if self.allow_fewer_steps_if_limited_data else self.min_steps

            # If still insufficient steps, raise error
            if len(steps) < absolute_min:
                raise ValueError(
                    f"Insufficient steps found for this combination. "
                    f"Found {len(steps)} steps, minimum {absolute_min} required. "
                    "Please try a different query or check corpus coverage. "
                    "You may need to load more data into ClickHouse."
                )

        # Validate tools
        required_tools = workflow.get("required_tools", [])
        tool_names = {tool["tool_name"] for tool in required_tools}

        for step in steps:
            step_tools = step.get("tools", [])
            for tool in step_tools:
                if tool not in tool_names:
                    logger.warning(f"Tool '{tool}' mentioned in step but not in required_tools")

        # Check constraints
        if constraints.get("no_bleach"):
            for tool in required_tools:
                if "bleach" in tool["tool_name"].lower():
                    logger.warning("Bleach found in tools but user specified no_bleach")
                    # Remove bleach from tools
                    required_tools = [
                        t for t in required_tools if "bleach" not in t["tool_name"].lower()
                    ]
                    workflow["required_tools"] = required_tools

        # Quality check
        if len(retrieved["reference_documents"]) < 2:
            logger.warning("Workflow based on limited data (fewer than 2 documents)")

        return workflow

    def _build_output(
        self,
        workflow: Dict[str, Any],
        normalized: Dict[str, Any],
        retrieved: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build final output dictionary matching WORKFLOW_AGENT_DESIGN.md schema.
        
        Args:
            workflow: Validated workflow
            normalized: Normalized scenario
            retrieved: Retrieved data
            
        Returns:
            Complete output dictionary
        """
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"

        scenario = {
            "surface_type": normalized["surface_type"],
            "dirt_type": normalized["dirt_type"],
            "cleaning_method": retrieved["selected_method"],
            "normalized_query": normalized["normalized_query"],
        }

        # Format source documents (deduplicate by document_id)
        source_documents = []
        seen_document_ids: Set[str] = set()

        for doc in retrieved["reference_documents"]:
            document_id = doc.get("document_id")

            # Skip if we've already added this document
            if not document_id or document_id in seen_document_ids:
                continue

            # Mark as seen and add to list
            seen_document_ids.add(document_id)
            source_documents.append({
                "document_id": document_id,
                "url": doc.get("url"),
                "title": doc.get("title"),
                "relevance_score": 0.9,  # Can be calculated based on match quality
                "extraction_confidence": doc.get("extraction_confidence"),
            })

        # Build metadata
        metadata = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "agent_version": "1.0",
            "extraction_method": "agent",
            "confidence": workflow.get("metadata", {}).get("confidence", 0.7),
            "corpus_coverage": {
                "matching_documents": len(retrieved["reference_documents"]),
                "total_combinations": 1,
                "coverage_score": 1.0 if retrieved["reference_documents"] else 0.0,
            },
        }

        # Add method_selection metadata if available
        if "method_selection_metadata" in retrieved:
            metadata["method_selection"] = retrieved["method_selection_metadata"]

        return {
            "workflow_id": workflow_id,
            "scenario": scenario,
            "workflow": workflow,
            "source_documents": source_documents,
            "metadata": metadata,
        }

    def close(self):
        """Close all tool connections."""
        self.fetch_methods.close()
        self.fetch_steps.close()
        self.fetch_tools.close()
        self.fetch_reference_context.close()
        self.search_similar_scenarios.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


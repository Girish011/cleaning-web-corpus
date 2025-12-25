"""
Workflow composition logic for generating structured cleaning workflows.

Takes retrieved steps, tools, and reference documents, deduplicates and orders
steps logically, enriches descriptions with LLM, adds safety notes, and returns
structured workflows matching the output schema.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class WorkflowComposer:
    """
    Composes structured workflows from retrieved steps, tools, and documents.
    
    Responsibilities:
    - Deduplicate similar steps
    - Order steps logically (prep → apply → wait → clean → dry)
    - Enrich step descriptions with LLM
    - Aggregate tools with quantities and categories
    - Extract safety notes from source documents
    - Generate workflow metadata (duration, difficulty, confidence)
    """

    def __init__(
        self,
        enable_llm_enrichment: bool = False,
        llm_extractor=None,
    ):
        """
        Initialize the workflow composer.
        
        Args:
            enable_llm_enrichment: Whether to use LLM for step enrichment
            llm_extractor: Optional LLM extractor instance for enrichment
        """
        self.enable_llm_enrichment = enable_llm_enrichment
        self.llm_extractor = llm_extractor

    def compose_workflow(
        self,
        steps: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        reference_documents: List[Dict[str, Any]],
        scenario: Dict[str, str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compose a structured workflow from retrieved data.
        
        Args:
            steps: List of step dictionaries from fetch_steps
            tools: List of tool dictionaries from fetch_tools
            reference_documents: List of document dictionaries from fetch_reference_context
            scenario: Dictionary with surface_type, dirt_type, cleaning_method, normalized_query
            constraints: Optional user constraints (no_bleach, no_harsh_chemicals, etc.)
            
        Returns:
            Structured workflow dictionary matching WORKFLOW_AGENT_DESIGN.md output schema
        """
        # Filter out low-quality/informational steps
        quality_filtered_steps = self._filter_quality_steps(steps)

        # Filter steps by relevance to query intent
        relevance_filtered_steps = self._filter_by_relevance(
            quality_filtered_steps, scenario
        )

        # Deduplicate steps
        deduplicated_steps = self._deduplicate_steps(relevance_filtered_steps)

        # Order steps logically
        ordered_steps = self._order_steps(deduplicated_steps)

        # Enrich step descriptions (if LLM enabled)
        if self.enable_llm_enrichment and self.llm_extractor:
            enriched_steps = self._enrich_steps(ordered_steps, scenario)
        else:
            enriched_steps = self._format_steps(ordered_steps)

        # Aggregate tools
        required_tools = self._aggregate_tools(tools, enriched_steps)

        # Extract safety notes
        safety_notes = self._extract_safety_notes(reference_documents, constraints)

        # Extract tips
        tips = self._extract_tips(reference_documents)

        # Calculate metadata
        metadata = self._calculate_metadata(
            enriched_steps, reference_documents, scenario
        )

        # Build workflow
        workflow = {
            "estimated_duration_minutes": metadata["duration_minutes"],
            "difficulty": metadata["difficulty"],
            "steps": enriched_steps,
            "required_tools": required_tools,
            "safety_notes": safety_notes,
            "tips": tips,
        }

        return workflow

    def _deduplicate_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate or very similar steps.
        
        Args:
            steps: List of step dictionaries
            
        Returns:
            Deduplicated list of steps
        """
        if not steps:
            return []

        unique_steps = []
        seen_texts: Set[str] = set()

        for step in steps:
            step_text = step.get("step_text", "").lower().strip()

            # Skip exact duplicates
            if step_text in seen_texts:
                continue

            # Check for similar steps (simple word overlap)
            is_duplicate = False
            step_words = set(step_text.split())

            for seen_text in seen_texts:
                seen_words = set(seen_text.split())
                if len(step_words) > 0 and len(seen_words) > 0:
                    overlap = len(step_words & seen_words) / max(
                        len(step_words), len(seen_words)
                    )
                    # If >70% word overlap, consider duplicate
                    if overlap > 0.7:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_steps.append(step)
                seen_texts.add(step_text)

        return unique_steps

    def _filter_quality_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out informational/non-actionable steps.
        
        Rejects steps that:
        1. Don't contain action verbs (blot, apply, rinse, vacuum, etc.)
        2. Are too long (>200 words)
        3. Contain only informational content (benefits, descriptions without actions)
        4. Have low confidence scores (<0.5)
        
        Args:
            steps: List of step dictionaries
            
        Returns:
            Filtered list of actionable steps
        """
        if not steps:
            return []

        # Action verbs that indicate actionable cleaning steps
        action_verbs = [
            "blot", "apply", "rinse", "vacuum", "wipe", "scrub", "clean",
            "remove", "treat", "spray", "pour", "mix", "combine", "dilute",
            "soak", "scrub", "brush", "sweep", "mop", "wash", "dry",
            "towel", "dab", "pat", "rub", "polish", "sanitize", "disinfect",
            "prepare", "test", "cover", "spread", "let", "allow", "wait",
            "sit", "rest", "soak", "rinse", "flush", "drain", "empty",
        ]

        # Informational keywords that indicate non-actionable content
        informational_keywords = [
            "health benefits", "benefits", "prolongs", "extends", "improves",
            "helps", "can trap", "may contain", "is important", "is essential",
            "provides", "offers", "ensures", "maintains", "preserves",
            "description", "information", "about", "regarding", "concerning",
        ]

        filtered_steps = []

        for step in steps:
            step_text = step.get("step_text", "").strip()
            confidence = step.get("confidence", 0.0)

            # Skip if step text is empty
            if not step_text:
                continue

            # Filter 1: Reject steps with low confidence (<0.5)
            if confidence < 0.5:
                logger.debug(f"Rejecting step due to low confidence ({confidence}): {step_text[:50]}...")
                continue

            # Filter 2: Reject steps that are too long (>200 words)
            word_count = len(step_text.split())
            if word_count > 200:
                logger.debug(f"Rejecting step due to excessive length ({word_count} words): {step_text[:50]}...")
                continue

            step_lower = step_text.lower()

            # Filter 3: Reject steps that don't contain action verbs
            has_action_verb = any(
                verb in step_lower for verb in action_verbs
            )

            if not has_action_verb:
                logger.debug(f"Rejecting step due to missing action verb: {step_text[:50]}...")
                continue

            # Filter 4: Reject steps that contain only informational content
            # Check if step starts with informational keywords or is primarily informational
            starts_with_info = any(
                step_lower.startswith(keyword) or step_lower.startswith(f"{keyword} ")
                for keyword in informational_keywords
            )

            # Count informational keywords vs action verbs
            info_count = sum(1 for keyword in informational_keywords if keyword in step_lower)
            action_count = sum(1 for verb in action_verbs if verb in step_lower)

            # If step starts with informational keyword and has more info keywords than actions, reject
            if starts_with_info and info_count > action_count:
                logger.debug(f"Rejecting step due to informational content: {step_text[:50]}...")
                continue

            # Additional check: Reject if step is primarily descriptive (no imperative structure)
            # Check if step starts with a verb (imperative) or with informational phrases
            first_words = step_lower.split()[:3]
            starts_with_verb = any(
                first_words[0] == verb or (len(first_words) > 1 and first_words[1] == verb)
                for verb in action_verbs
            )

            # If step doesn't start with action verb and has high info keyword count, reject
            if not starts_with_verb and info_count >= 2:
                logger.debug(f"Rejecting step due to descriptive/informational structure: {step_text[:50]}...")
                continue

            # Step passed all filters
            filtered_steps.append(step)

        logger.info(
            f"Filtered {len(steps)} steps to {len(filtered_steps)} actionable steps "
            f"({len(steps) - len(filtered_steps)} informational/non-actionable steps removed)"
        )

        return filtered_steps

    def _filter_by_relevance(
        self, steps: List[Dict[str, Any]], scenario: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Filter and rank steps by relevance to query intent.
        
        For stain removal queries, prioritize steps containing stain-related keywords
        (blot, remove, treat, clean, rinse) and penalize general maintenance steps.
        
        Args:
            steps: List of step dictionaries
            scenario: Dictionary with surface_type, dirt_type, cleaning_method, normalized_query
            
        Returns:
            Filtered and ranked list of steps (sorted by relevance score, descending)
        """
        if not steps:
            return []

        normalized_query = scenario.get("normalized_query", "").lower()
        dirt_type = scenario.get("dirt_type", "").lower()

        # Score each step by relevance
        scored_steps = []
        for step in steps:
            step_text = step.get("step_text", "").lower()
            relevance_score = self._calculate_step_relevance(
                step_text, normalized_query, dirt_type
            )

            # Store relevance score with step
            step_with_score = step.copy()
            step_with_score["relevance_score"] = relevance_score
            scored_steps.append(step_with_score)

        # Sort by relevance score (descending)
        scored_steps.sort(key=lambda s: s.get("relevance_score", 0.0), reverse=True)

        # Filter out steps with very low relevance (<0.2) if we have enough steps
        if len(scored_steps) > 5:
            filtered = [
                s for s in scored_steps
                if s.get("relevance_score", 0.0) >= 0.2
            ]
            if filtered:  # Only filter if we still have steps
                scored_steps = filtered

        # Remove relevance_score before returning (clean up)
        for step in scored_steps:
            step.pop("relevance_score", None)

        logger.info(
            f"Filtered {len(steps)} steps to {len(scored_steps)} relevant steps "
            f"for query: '{normalized_query[:50]}...'"
        )

        return scored_steps

    def _calculate_step_relevance(
        self, step_text: str, normalized_query: str, dirt_type: str
    ) -> float:
        """
        Calculate relevance score for a step based on query intent.
        
        Args:
            step_text: Step text (lowercase)
            normalized_query: Original query text (lowercase)
            dirt_type: Normalized dirt type (lowercase)
            
        Returns:
            Relevance score (0.0-1.0)
        """
        relevance = 0.5  # Base relevance score

        # Dirt-type specific keyword matching
        if dirt_type == "stain":
            # Stain removal keywords (prioritize)
            stain_keywords = [
                "blot", "remove", "treat", "clean", "rinse", "stain",
                "spill", "spot", "mark", "wine", "coffee", "ink",
                "apply", "solution", "vinegar", "baking soda",
            ]
            stain_count = sum(1 for keyword in stain_keywords if keyword in step_text)
            if stain_count > 0:
                relevance += min(0.4, stain_count * 0.1)  # Up to 0.4 boost

            # General maintenance keywords (penalize)
            maintenance_keywords = [
                "health benefits", "prolongs", "extends", "maintenance",
                "regular", "routine", "vacuum", "general", "overall",
            ]
            maintenance_count = sum(
                1 for keyword in maintenance_keywords if keyword in step_text
            )
            if maintenance_count > 0:
                relevance -= min(0.3, maintenance_count * 0.1)  # Up to 0.3 penalty

        elif dirt_type == "dust":
            # Dust removal keywords
            dust_keywords = ["vacuum", "dust", "remove", "wipe", "clean", "sweep"]
            dust_count = sum(1 for keyword in dust_keywords if keyword in step_text)
            if dust_count > 0:
                relevance += min(0.3, dust_count * 0.1)

        elif dirt_type == "pet_hair":
            # Pet hair removal keywords
            pet_hair_keywords = [
                "pet hair", "hair", "vacuum", "lint", "roller", "remove"
            ]
            pet_hair_count = sum(
                1 for keyword in pet_hair_keywords if keyword in step_text
            )
            if pet_hair_count > 0:
                relevance += min(0.3, pet_hair_count * 0.1)

        elif dirt_type == "grease":
            # Grease removal keywords
            grease_keywords = [
                "grease", "degrease", "scrub", "tough", "stubborn", "remove"
            ]
            grease_count = sum(1 for keyword in grease_keywords if keyword in step_text)
            if grease_count > 0:
                relevance += min(0.3, grease_count * 0.1)

        elif dirt_type == "mold":
            # Mold removal keywords
            mold_keywords = [
                "mold", "mildew", "scrub", "disinfect", "sanitize", "remove"
            ]
            mold_count = sum(1 for keyword in mold_keywords if keyword in step_text)
            if mold_count > 0:
                relevance += min(0.3, mold_count * 0.1)

        # Query keyword matching (boost steps that match query keywords)
        if normalized_query:
            query_words = set(normalized_query.split())
            step_words = set(step_text.split())

            # Count matching words (excluding common stop words)
            stop_words = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
                "for", "of", "with", "from", "by", "is", "are", "was", "were",
            }
            query_words = query_words - stop_words
            step_words = step_words - stop_words

            if query_words:
                matching_words = query_words & step_words
                match_ratio = len(matching_words) / len(query_words)
                relevance += min(0.3, match_ratio * 0.3)  # Up to 0.3 boost

        # Penalize informational/maintenance content
        informational_phrases = [
            "health benefits", "prolongs", "extends", "improves",
            "is important", "is essential", "helps", "can trap",
        ]
        info_count = sum(
            1 for phrase in informational_phrases if phrase in step_text
        )
        if info_count > 0:
            relevance -= min(0.4, info_count * 0.15)  # Up to 0.4 penalty

        # Normalize to 0.0-1.0 range
        return min(1.0, max(0.0, relevance))

    def _order_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Order steps logically: prep → apply → wait → clean → dry.
        
        Args:
            steps: List of step dictionaries
            
        Returns:
            Ordered list of steps
        """
        if not steps:
            return []

        # Categorize steps by action type
        prep_steps = []
        apply_steps = []
        wait_steps = []
        clean_steps = []
        dry_steps = []
        other_steps = []

        for step in steps:
            step_text = step.get("step_text", "").lower()
            step_order = step.get("step_order", 999)

            # Categorize based on keywords
            if any(
                word in step_text
                for word in ["prepare", "mix", "combine", "dilute", "test"]
            ):
                prep_steps.append((step_order, step))
            elif any(
                word in step_text
                for word in ["apply", "spray", "pour", "spread", "cover"]
            ):
                apply_steps.append((step_order, step))
            elif any(
                word in step_text
                for word in ["wait", "let", "allow", "sit", "soak", "rest"]
            ):
                wait_steps.append((step_order, step))
            elif any(
                word in step_text
                for word in ["rinse", "wipe", "scrub", "blot", "vacuum", "clean"]
            ):
                clean_steps.append((step_order, step))
            elif any(
                word in step_text for word in ["dry", "towel", "air dry", "blot dry"]
            ):
                dry_steps.append((step_order, step))
            else:
                other_steps.append((step_order, step))

        # Sort each category by original step_order
        prep_steps.sort(key=lambda x: x[0])
        apply_steps.sort(key=lambda x: x[0])
        wait_steps.sort(key=lambda x: x[0])
        clean_steps.sort(key=lambda x: x[0])
        dry_steps.sort(key=lambda x: x[0])
        other_steps.sort(key=lambda x: x[0])

        # Combine in logical order
        ordered = []
        for _, step in prep_steps + apply_steps + wait_steps + clean_steps + dry_steps:
            ordered.append(step)

        # Add other steps at the end
        for _, step in other_steps:
            ordered.append(step)

        # If no categorization worked, use original order
        if not ordered:
            ordered = sorted(steps, key=lambda s: s.get("step_order", 999))

        return ordered

    def _format_steps(
        self, steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format steps into output schema format.
        
        Args:
            steps: List of step dictionaries
            
        Returns:
            Formatted list of step dictionaries
        """
        formatted = []
        for idx, step in enumerate(steps, 1):
            step_text = step.get("step_text", "")
            step_summary = step.get("step_summary")

            # Extract action (first few words or summary)
            if step_summary:
                action = step_summary
            else:
                # Use first 3-5 words as action
                words = step_text.split()[:5]
                action = " ".join(words)
                if len(step_text.split()) > 5:
                    action += "..."

            # Estimate duration (simple heuristic)
            duration = self._estimate_step_duration(step_text)

            # Extract tools mentioned in step
            tools_in_step = self._extract_tools_from_step(step_text)

            formatted.append({
                "step_number": idx,
                "action": action,
                "description": step_text,
                "tools": tools_in_step,
                "duration_seconds": duration,
                "order": idx,
            })

        return formatted

    def _enrich_steps(
        self, steps: List[Dict[str, Any]], scenario: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Enrich step descriptions using LLM.
        
        Args:
            steps: List of step dictionaries
            scenario: Scenario context (surface, dirt, method)
            
        Returns:
            Enriched list of step dictionaries
        """
        # For now, use formatted steps (LLM enrichment can be added later)
        # This is a placeholder for future LLM integration
        return self._format_steps(steps)

    def _aggregate_tools(
        self, tools: List[Dict[str, Any]], steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate tools from tool list and steps.
        
        Args:
            tools: List of tool dictionaries from fetch_tools
            steps: List of formatted step dictionaries
            
        Returns:
            List of aggregated tool dictionaries
        """
        # Build tool map from tools list
        tool_map: Dict[str, Dict[str, Any]] = {}

        for tool in tools:
            tool_name = tool.get("tool_name", "")
            if tool_name:
                tool_map[tool_name] = {
                    "tool_name": tool_name,
                    "category": tool.get("category"),
                    "quantity": self._estimate_quantity(tool_name),
                    "is_required": tool.get("is_primary", True),
                }

        # Add tools mentioned in steps
        for step in steps:
            for tool_name in step.get("tools", []):
                if tool_name not in tool_map:
                    tool_map[tool_name] = {
                        "tool_name": tool_name,
                        "category": None,
                        "quantity": self._estimate_quantity(tool_name),
                        "is_required": True,
                    }

        return list(tool_map.values())

    def _extract_safety_notes(
        self,
        reference_documents: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Extract safety notes from reference documents.
        
        Args:
            reference_documents: List of document dictionaries
            constraints: Optional user constraints
            
        Returns:
            List of safety note strings
        """
        safety_notes = []
        safety_keywords = [
            "warning",
            "caution",
            "danger",
            "safety",
            "ventilate",
            "gloves",
            "test",
            "damage",
            "toxic",
            "harmful",
        ]

        # Extract from document text
        for doc in reference_documents:
            # Check steps for safety notes
            for step in doc.get("steps", []):
                step_text = step.get("step_text", "").lower()
                if any(keyword in step_text for keyword in safety_keywords):
                    # Extract safety-relevant sentences
                    sentences = step_text.split(".")
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if any(keyword in sentence for keyword in safety_keywords):
                            if sentence and len(sentence) > 20:
                                safety_notes.append(sentence.capitalize())

        # Add constraint-based safety notes
        if constraints:
            if constraints.get("no_bleach"):
                safety_notes.append(
                    "Do not use bleach or bleach-containing products"
                )
            if constraints.get("no_harsh_chemicals"):
                safety_notes.append(
                    "Use only gentle, non-harsh cleaning solutions"
                )
            if constraints.get("gentle_only"):
                safety_notes.append("Use gentle methods only to avoid damage")

        # Deduplicate
        return list(dict.fromkeys(safety_notes))[:10]  # Limit to 10

    def _extract_tips(self, reference_documents: List[Dict[str, Any]]) -> List[str]:
        """
        Extract helpful tips from reference documents.
        
        Args:
            reference_documents: List of document dictionaries
            
        Returns:
            List of tip strings
        """
        tips = []
        tip_keywords = ["tip", "hint", "recommend", "suggest", "best", "better"]

        # Extract from document text
        for doc in reference_documents:
            for step in doc.get("steps", []):
                step_text = step.get("step_text", "").lower()
                if any(keyword in step_text for keyword in tip_keywords):
                    sentences = step_text.split(".")
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if any(keyword in sentence for keyword in tip_keywords):
                            if sentence and len(sentence) > 20:
                                tips.append(sentence.capitalize())

        # Deduplicate
        return list(dict.fromkeys(tips))[:5]  # Limit to 5

    def _calculate_metadata(
        self,
        steps: List[Dict[str, Any]],
        reference_documents: List[Dict[str, Any]],
        scenario: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Calculate workflow metadata (duration, difficulty, confidence).
        
        Args:
            steps: List of formatted step dictionaries
            reference_documents: List of document dictionaries
            scenario: Scenario context
            
        Returns:
            Metadata dictionary
        """
        # Calculate total duration
        total_seconds = sum(step.get("duration_seconds", 0) for step in steps)
        duration_minutes = round(total_seconds / 60)

        # Estimate difficulty based on number of steps and complexity
        num_steps = len(steps)
        if num_steps <= 3:
            difficulty = "easy"
        elif num_steps <= 6:
            difficulty = "moderate"
        else:
            difficulty = "hard"

        # Calculate average confidence from reference documents
        confidences = [
            doc.get("extraction_confidence", 0.0)
            for doc in reference_documents
            if doc.get("extraction_confidence")
        ]
        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.7
        )

        return {
            "duration_minutes": duration_minutes,
            "difficulty": difficulty,
            "confidence": round(avg_confidence, 3),
        }

    def _estimate_step_duration(self, step_text: str) -> int:
        """
        Estimate step duration in seconds based on step text.
        
        Args:
            step_text: Step description text
            
        Returns:
            Estimated duration in seconds
        """
        step_lower = step_text.lower()

        # Look for explicit time mentions
        import re

        # Pattern: "X minutes", "X mins", "X seconds", etc.
        time_patterns = [
            (r"(\d+)\s*(?:minute|min|m)\s*s?", 60),
            (r"(\d+)\s*(?:second|sec|s)\s*", 1),
            (r"(\d+)\s*(?:hour|hr|h)\s*", 3600),
        ]

        for pattern, multiplier in time_patterns:
            match = re.search(pattern, step_lower)
            if match:
                return int(match.group(1)) * multiplier

        # Heuristic based on action type
        if any(word in step_lower for word in ["wait", "let", "sit", "soak"]):
            return 600  # 10 minutes default
        elif any(word in step_lower for word in ["rinse", "wipe", "blot"]):
            return 180  # 3 minutes
        elif any(word in step_lower for word in ["scrub", "clean"]):
            return 300  # 5 minutes
        elif any(word in step_lower for word in ["prepare", "mix"]):
            return 120  # 2 minutes
        else:
            return 60  # 1 minute default

    def _extract_tools_from_step(self, step_text: str) -> List[str]:
        """
        Extract tool names mentioned in step text.
        
        Args:
            step_text: Step description text
            
        Returns:
            List of tool names
        """
        # Simple keyword matching (can be enhanced with NER)
        tools = []
        tool_keywords = [
            "paper towel",
            "towel",
            "spray bottle",
            "vinegar",
            "water",
            "brush",
            "sponge",
            "vacuum",
            "cloth",
            "gloves",
        ]

        step_lower = step_text.lower()
        for keyword in tool_keywords:
            if keyword in step_lower:
                tools.append(keyword.replace(" ", "_"))

        return tools

    def _estimate_quantity(self, tool_name: str) -> str:
        """
        Estimate quantity for a tool.
        
        Args:
            tool_name: Tool name
            
        Returns:
            Estimated quantity string
        """
        tool_lower = tool_name.lower()

        # Heuristics for common tools
        if "towel" in tool_lower or "cloth" in tool_lower:
            return "several"
        elif "bottle" in tool_lower or "spray" in tool_lower:
            return "1"
        elif "vinegar" in tool_lower or "water" in tool_lower:
            return "1 cup"
        elif "gloves" in tool_lower:
            return "1 pair"
        else:
            return "1"


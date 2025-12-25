"""
Action extraction module for Phase 2.1.

Converts text cleaning steps into structured robot actions with:
- Action types (apply, scrub, vacuum, wait, etc.)
- Force/pressure specifications
- Temporal information (duration, wait times)
- Tool requirements
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Action type keywords
ACTION_TYPE_KEYWORDS = {
    "apply": ["apply", "spray", "spread", "pour", "add", "dose"],
    "scrub": ["scrub", "brush", "rub", "scour", "clean", "wipe", "polish"],
    "vacuum": ["vacuum", "suck", "extract", "remove debris"],
    "rinse": ["rinse", "wash", "flush", "soak", "drench"],
    "dry": ["dry", "air dry", "blot", "pat dry", "towel dry"],
    "wait": ["wait", "let sit", "allow", "leave", "rest", "stand", "soak for"],
    "pick": ["pick up", "pick", "grab", "grasp", "take", "lift"],  # CHANGE: Added pick action
    "place": ["place", "put", "set down", "position", "set"],  # CHANGE: Added place action
    "remove": ["remove", "take out", "extract"],
    "move": ["move", "relocate", "transfer"],
    "check": ["check", "inspect", "examine", "verify", "test"],
}

# Force/pressure indicators
FORCE_KEYWORDS = {
    "gentle": ["gentle", "lightly", "softly", "carefully", "delicately", "gently"],
    "moderate": ["moderate", "firmly", "thoroughly", "well"],
    "firm": ["firm", "hard", "vigorously", "forcefully", "strongly", "aggressively"],
    "light": ["light", "soft", "minimal", "slight"],
}

# Duration/time patterns
TIME_PATTERNS = [
    re.compile(r'(\d+)\s*(?:minute|min|m)\s*(?:s)?', re.IGNORECASE),
    re.compile(r'(\d+)\s*(?:second|sec|s)\s*(?:s)?', re.IGNORECASE),
    re.compile(r'(\d+)\s*(?:hour|hr|h)\s*(?:s)?', re.IGNORECASE),
    re.compile(r'for\s+(\d+)\s*(?:minute|min|m)', re.IGNORECASE),
    re.compile(r'(\d+)\s*-\s*(\d+)\s*(?:minute|min|m)', re.IGNORECASE),  # Range
]

# Tool keywords (mapping to robot-compatible tool names)
TOOL_MAPPING = {
    "brush": ["brush", "scrub brush", "cleaning brush", "stiff brush"],
    "sponge": ["sponge", "cleaning sponge"],
    "cloth": ["cloth", "rag", "towel", "paper towel", "cleaning cloth"],
    "vacuum": ["vacuum", "vacuum cleaner", "hoover"],
    "spray_bottle": ["spray bottle", "sprayer", "bottle"],
    "scraper": ["scraper", "putty knife", "razor"],
    "mop": ["mop", "mop head"],
    "detergent": ["detergent", "soap", "cleaning solution", "cleaner"],
}


class ActionExtractor:
    """
    Extracts structured robot actions from text cleaning steps.
    
    Converts natural language steps like:
    "Apply cleaning solution and scrub gently for 2 minutes"
    
    Into structured actions:
    {
        "action_type": "scrub",
        "tool": "brush",
        "force": 5.0,
        "duration": 120,
        "pattern": "circular"
    }
    """

    def __init__(
        self,
        default_force: float = 5.0,
        default_duration: int = 30,
        min_confidence: float = 0.3,
    ):
        """
        Initialize the action extractor.
        
        Args:
            default_force: Default force value (0-10 scale) if not specified
            default_duration: Default duration in seconds if not specified
            min_confidence: Minimum confidence threshold for action extraction
        """
        self.default_force = default_force
        self.default_duration = default_duration
        self.min_confidence = min_confidence

    def extract_action(self, step_text: str, step_order: int = 1) -> Optional[Dict]:
        """
        Extract structured action from a single step text.
        
        Args:
            step_text: Text description of the cleaning step
            step_order: Order/sequence number of the step
            
        Returns:
            Dictionary with structured action information, or None if extraction fails
        """
        if not step_text or len(step_text.strip()) < 5:
            return None

        step_lower = step_text.lower().strip()

        # Extract action type
        action_type, action_confidence = self._extract_action_type(step_lower)

        # Extract tool
        tool = self._extract_tool(step_lower)

        # Extract force/pressure
        force = self._extract_force(step_lower)

        # Extract duration
        duration = self._extract_duration(step_lower)

        # Extract motion pattern
        pattern = self._extract_pattern(step_lower)

        # Calculate overall confidence
        confidence = self._calculate_confidence(
            action_confidence, tool, force, duration, step_text
        )

        if confidence < self.min_confidence:
            logger.debug(f"Low confidence ({confidence:.2f}) for step: {step_text[:50]}...")
            return None

        action = {
            "action_type": action_type,
            "tool": tool,
            "force": force,
            "duration": duration,
            "pattern": pattern,
            "order": step_order,
            "original_text": step_text,
            "confidence": round(confidence, 3),
        }

        return action

    def extract_actions(self, steps: List[str]) -> List[Dict]:
        """
        Extract actions from a list of step texts.
        
        Args:
            steps: List of step text strings
            
        Returns:
            List of structured action dictionaries
        """
        actions = []

        for idx, step in enumerate(steps, start=1):
            action = self.extract_action(step, step_order=idx)
            if action:
                actions.append(action)
            else:
                logger.debug(f"Failed to extract action from step {idx}: {step[:50]}...")

        logger.info(f"Extracted {len(actions)}/{len(steps)} actions from steps")
        return actions

    def _extract_action_type(self, text: str) -> Tuple[str, float]:
        """
        Extract action type from text.
        
        Args:
            text: Lowercase step text
            
        Returns:
            Tuple of (action_type, confidence)
        """
        best_action = "apply"  # Default
        best_confidence = 0.3
        best_matches = 0

        # Check for "wait" first (has priority, often contains other action words)
        if any(keyword in text for keyword in ACTION_TYPE_KEYWORDS["wait"]):
            return "wait", 0.8

        for action_type, keywords in ACTION_TYPE_KEYWORDS.items():
            if action_type == "wait":  # Already checked
                continue
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > 0:
                confidence = min(0.9, 0.4 + (matches * 0.15))
                if matches > best_matches or (matches == best_matches and confidence > best_confidence):
                    best_action = action_type
                    best_confidence = confidence
                    best_matches = matches

        return best_action, best_confidence

    def _extract_tool(self, text: str) -> Optional[str]:
        """
        Extract tool requirement from text.
        
        Args:
            text: Lowercase step text
            
        Returns:
            Tool name or None
        """
        # Check for explicit tool mentions
        for tool, keywords in TOOL_MAPPING.items():
            for keyword in keywords:
                if keyword in text:
                    return tool

        # Infer tool from action type
        if "scrub" in text or "brush" in text:
            return "brush"
        elif "vacuum" in text:
            return "vacuum"
        elif "spray" in text or "apply" in text:
            return "spray_bottle"
        elif "rinse" in text or "wash" in text:
            return "cloth"

        return None

    def _extract_force(self, text: str) -> float:
        """
        Extract force/pressure specification from text.
        
        Args:
            text: Lowercase step text
            
        Returns:
            Force value (0-10 scale, where 5.0 is moderate/default)
        """
        # Check for force keywords
        for force_level, keywords in FORCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    if force_level == "gentle" or force_level == "light":
                        return 3.0
                    elif force_level == "moderate":
                        return 5.0
                    elif force_level == "firm":
                        return 7.5

        # Default moderate force
        return self.default_force

    def _extract_duration(self, text: str) -> int:
        """
        Extract duration from text.
        
        Args:
            text: Lowercase step text
            
        Returns:
            Duration in seconds
        """
        # Try each time pattern
        for pattern in TIME_PATTERNS:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    # Single value
                    value = int(groups[0])
                    # Determine unit from pattern
                    if 'hour' in pattern.pattern or 'hr' in pattern.pattern or 'h' in pattern.pattern:
                        return value * 3600
                    elif 'minute' in pattern.pattern or 'min' in pattern.pattern or 'm' in pattern.pattern:
                        return value * 60
                    else:
                        return value  # seconds
                elif len(groups) == 2:
                    # Range - take average
                    min_val = int(groups[0])
                    max_val = int(groups[1])
                    avg = (min_val + max_val) // 2
                    return avg * 60  # Assume minutes

        # Check for "immediately" or "right away" (0 duration)
        if any(word in text for word in ["immediately", "right away", "right now", "instantly"]):
            return 0

        # Default duration
        return self.default_duration

    def _extract_pattern(self, text: str) -> Optional[str]:
        """
        Extract motion pattern from text.
        
        Args:
            text: Lowercase step text
            
        Returns:
            Motion pattern name or None
        """
        if "circular" in text or "circle" in text or "round" in text:
            return "circular"
        elif "back and forth" in text or "backward and forward" in text or "side to side" in text:
            return "back_and_forth"
        elif "up and down" in text or "vertical" in text:
            return "vertical"
        elif "horizontal" in text or "left to right" in text:
            return "horizontal"
        elif "gentle" in text or "light" in text:
            return "gentle"

        return None

    def _calculate_confidence(
        self,
        action_confidence: float,
        tool: Optional[str],
        force: float,
        duration: int,
        original_text: str,
    ) -> float:
        """
        Calculate overall confidence for extracted action.
        
        Args:
            action_confidence: Confidence from action type extraction
            tool: Extracted tool (None if not found)
            force: Extracted force value
            duration: Extracted duration
            original_text: Original step text
            
        Returns:
            Overall confidence score (0.0-1.0)
        """
        confidence = action_confidence

        # Boost if tool was found
        if tool:
            confidence += 0.1

        # Boost if duration was explicitly found (not default)
        if duration != self.default_duration:
            confidence += 0.1

        # Boost if force was explicitly specified (not default)
        if force != self.default_force:
            confidence += 0.05

        # Penalize very short steps (likely incomplete), but less for wait/check actions
        if len(original_text) < 15:
            if action_confidence < 0.5:  # Only penalize if action confidence is already low
                confidence -= 0.2
            else:
                confidence -= 0.1  # Less penalty for high-confidence short actions

        return min(1.0, max(0.0, confidence))


def extract_actions_from_document(document: Dict) -> List[Dict]:
    """
    Extract robot actions from a processed document.
    
    Args:
        document: Document dictionary with 'steps' field
        
    Returns:
        List of structured action dictionaries
    """
    extractor = ActionExtractor()

    steps = document.get("steps", [])
    if not steps:
        logger.debug(f"No steps found in document: {document.get('url', 'unknown')}")
        return []

    # Handle both string list and dict list formats
    step_texts = []
    for step in steps:
        if isinstance(step, str):
            step_texts.append(step)
        elif isinstance(step, dict):
            step_texts.append(step.get("step", ""))

    actions = extractor.extract_actions(step_texts)

    # Add document context to each action
    for action in actions:
        action["document_url"] = document.get("url", "")
        action["surface_type"] = document.get("surface_type", "unknown")
        action["dirt_type"] = document.get("dirt_type", "unknown")
        action["cleaning_method"] = document.get("cleaning_method", "unknown")

    return actions


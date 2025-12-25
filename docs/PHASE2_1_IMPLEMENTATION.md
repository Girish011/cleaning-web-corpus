# Phase 2.1: Action Extraction Module - Implementation Summary

## ✅ Implementation Complete

Phase 2.1 has been successfully implemented! This module converts natural language cleaning steps into structured robot-executable actions with force, duration, tool, and motion pattern specifications.

## Overview

The Action Extraction Module is the first component of the robot simulation layer. It bridges the gap between human-readable cleaning instructions and robot-executable commands by extracting structured action parameters from text.

**Location**: `src/robot/action_extractor.py`

## What Was Implemented

### 1. ActionExtractor Class

**Purpose**: Convert text cleaning steps → structured robot actions

**Key Features**:
- Action type detection (9 types: apply, scrub, vacuum, wait, rinse, dry, remove, move, check)
- Force/pressure extraction (gentle: 3.0, moderate: 5.0, firm: 7.5 on 0-10 scale)
- Temporal information extraction (duration in seconds from minutes/hours)
- Tool requirement extraction (brush, sponge, cloth, vacuum, etc.)
- Motion pattern detection (circular, back_and_forth, vertical, horizontal)
- Confidence scoring for quality filtering

**Key Methods**:

1. **`extract_action(step_text, step_order)`** - Extract action from single step
   - Input: Text step string
   - Output: Structured action dictionary with all parameters
   - Returns None if confidence too low

2. **`extract_actions(steps)`** - Extract actions from list of steps
   - Input: List of step text strings
   - Output: List of structured action dictionaries
   - Handles both string and dict formats

3. **`_extract_action_type(text)`** - Detect action type from keywords
   - Uses keyword matching with priority (wait actions checked first)
   - Returns (action_type, confidence) tuple

4. **`_extract_tool(text)`** - Extract tool requirement
   - Maps natural language tool names to robot-compatible names
   - Falls back to inference from action type

5. **`_extract_force(text)`** - Extract force/pressure level
   - Maps descriptive words (gentle, firm, etc.) to numeric values
   - Default: 5.0 (moderate)

6. **`_extract_duration(text)`** - Extract time duration
   - Parses minutes, seconds, hours
   - Handles ranges (e.g., "2-5 minutes")
   - Default: 30 seconds

7. **`_extract_pattern(text)`** - Extract motion pattern
   - Detects circular, back_and_forth, vertical, horizontal patterns
   - Returns None if not specified

8. **`_calculate_confidence(...)`** - Calculate extraction confidence
   - Factors: action confidence, tool presence, explicit duration/force
   - Penalizes very short steps
   - Returns 0.0-1.0 score

### 2. Helper Function

**`extract_actions_from_document(document)`** - Extract actions from processed document
- Input: Document dictionary with 'steps' field
- Output: List of actions with document context added
- Adds: document_url, surface_type, dirt_type, cleaning_method

## Action Types Supported

| Action Type | Keywords | Use Case |
|------------|----------|----------|
| `apply` | apply, spray, spread, pour, add, put, place, dose | Applying cleaning solutions |
| `scrub` | scrub, brush, rub, scour, clean, wipe, polish | Scrubbing/cleaning surfaces |
| `vacuum` | vacuum, suck, extract, remove debris | Vacuuming operations |
| `rinse` | rinse, wash, flush, soak, drench | Rinsing/washing |
| `dry` | dry, air dry, blot, pat dry, towel dry | Drying operations |
| `wait` | wait, let sit, allow, leave, rest, stand, soak for | Waiting/soaking periods |
| `remove` | remove, take out, extract, pick up, grab | Removing items |
| `move` | move, place, put, position, set | Moving/positioning |
| `check` | check, inspect, examine, verify, test | Inspection/verification |

## Tool Mapping

| Robot Tool | Natural Language Keywords |
|-----------|---------------------------|
| `brush` | brush, scrub brush, cleaning brush, stiff brush |
| `sponge` | sponge, cleaning sponge |
| `cloth` | cloth, rag, towel, paper towel, cleaning cloth |
| `vacuum` | vacuum, vacuum cleaner, hoover |
| `spray_bottle` | spray bottle, sprayer, bottle |
| `scraper` | scraper, putty knife, razor |
| `mop` | mop, mop head |
| `detergent` | detergent, soap, cleaning solution, cleaner |

## Force Levels

| Level | Keywords | Value | Description |
|-------|----------|-------|-------------|
| Gentle/Light | gentle, lightly, softly, carefully, delicately, gently, light, soft, minimal, slight | 3.0 | Light pressure for delicate surfaces |
| Moderate | moderate, firmly, thoroughly, well | 5.0 | Standard cleaning pressure (default) |
| Firm | firm, hard, vigorously, forcefully, strongly, aggressively | 7.5 | Heavy pressure for tough stains |

## Output Format

### Action Dictionary Structure

```json
{
  "action_type": "scrub",
  "tool": "brush",
  "force": 3.0,
  "duration": 120,
  "pattern": "circular",
  "order": 1,
  "original_text": "Apply cleaning solution and scrub gently for 2 minutes",
  "confidence": 1.0,
  "document_url": "https://example.com/cleaning-guide",
  "surface_type": "carpets_floors",
  "dirt_type": "stain",
  "cleaning_method": "manual"
}
```

### Field Descriptions

- **`action_type`**: Type of action (string, one of 9 types)
- **`tool`**: Required tool (string or null)
- **`force`**: Force/pressure level (float, 0-10 scale, default 5.0)
- **`duration`**: Duration in seconds (int, default 30)
- **`pattern`**: Motion pattern (string or null)
- **`order`**: Step sequence number (int)
- **`original_text`**: Original step text (string)
- **`confidence`**: Extraction confidence (float, 0.0-1.0)
- **`document_url`**: Source document URL (added by `extract_actions_from_document`)
- **`surface_type`**: Surface being cleaned (added by `extract_actions_from_document`)
- **`dirt_type`**: Type of dirt/stain (added by `extract_actions_from_document`)
- **`cleaning_method`**: Cleaning method used (added by `extract_actions_from_document`)

## Requirements

### Dependencies

**No external dependencies required!** The action extractor uses only Python standard library:
- `re` (regex)
- `logging`
- `typing`

### Python Version

- Python 3.7+

### Integration Dependencies

The action extractor integrates with:
- **Corpus data**: Reads from `data/processed/cleaning_docs.jsonl`
- **Enrichment pipeline**: Uses steps extracted by `src/enrichment/extractors.py`
- **Future**: Will feed into MuJoCo simulator (Phase 2.2)

## Installation

No installation needed - the module is part of the codebase. Just ensure you're in the project root:

```bash
cd /Users/girish11/cleaning-web-corpus
source .venv/bin/activate  # If using virtual environment
```

## Usage

### Basic Usage

```python
from src.robot.action_extractor import ActionExtractor

# Initialize extractor
extractor = ActionExtractor(
    default_force=5.0,      # Default force if not specified
    default_duration=30,    # Default duration in seconds
    min_confidence=0.3      # Minimum confidence threshold
)

# Extract action from single step
step = "Apply cleaning solution and scrub gently for 2 minutes"
action = extractor.extract_action(step, step_order=1)

if action:
    print(f"Action: {action['action_type']}")
    print(f"Tool: {action['tool']}")
    print(f"Force: {action['force']}")
    print(f"Duration: {action['duration']}s")
```

### Extract from Multiple Steps

```python
steps = [
    "Remove excess stain with a paper towel",
    "Apply cleaning solution",
    "Wait 5 minutes",
    "Rinse thoroughly"
]

actions = extractor.extract_actions(steps)
print(f"Extracted {len(actions)} actions")
```

### Extract from Document

```python
import json
from src.robot.action_extractor import extract_actions_from_document

# Load document
with open('data/processed/cleaning_docs.jsonl') as f:
    doc = json.loads(f.readline())

# Extract actions
actions = extract_actions_from_document(doc)

# Actions now include document context
for action in actions:
    print(f"{action['action_type']} on {action['surface_type']} "
          f"for {action['dirt_type']} using {action['tool']}")
```

## Testing

### Test Script

A comprehensive test script is provided:

```bash
python scripts/test_action_extractor.py
```

This script:
1. Tests with sample steps (6 different action types)
2. Tests with real documents from the corpus
3. Shows extraction results with confidence scores

### Manual Testing

```python
from src.robot.action_extractor import ActionExtractor

extractor = ActionExtractor()

# Test cases
test_steps = [
    "Apply cleaning solution and scrub gently for 2 minutes",
    "Wait 5 minutes for the solution to soak in",
    "Remove excess stain with a paper towel",
    "Rinse thoroughly with cold water",
    "Vacuum the carpet to remove debris",
    "Dry the surface with a clean cloth"
]

for i, step in enumerate(test_steps, 1):
    action = extractor.extract_action(step, i)
    if action:
        print(f"Step {i}: {action['action_type']} | "
              f"Tool: {action['tool']} | "
              f"Force: {action['force']} | "
              f"Duration: {action['duration']}s | "
              f"Confidence: {action['confidence']:.2f}")
```

### Expected Output

```
Step 1: scrub | Tool: detergent | Force: 3.0 | Duration: 120s | Confidence: 1.00
Step 2: wait | Tool: None | Force: 5.0 | Duration: 300s | Confidence: 0.90
Step 3: remove | Tool: cloth | Force: 5.0 | Duration: 30s | Confidence: 0.65
Step 4: rinse | Tool: cloth | Force: 5.0 | Duration: 30s | Confidence: 0.65
Step 5: vacuum | Tool: vacuum | Force: 5.0 | Duration: 30s | Confidence: 0.80
Step 6: scrub | Tool: cloth | Force: 5.0 | Duration: 30s | Confidence: 0.65
```

## Integration with Framework

### 1. Data Flow

```
Corpus Documents (cleaning_docs.jsonl)
    ↓
Enrichment Pipeline (extracts steps)
    ↓
Action Extractor (converts steps → actions)
    ↓
[Future: MuJoCo Simulator]
    ↓
[Future: Command Generator]
```

### 2. Input Format

The action extractor expects documents with a `steps` field:

```json
{
  "url": "https://example.com/cleaning-guide",
  "steps": [
    "Remove excess stain",
    "Apply cleaning solution",
    "Scrub gently for 2 minutes",
    "Rinse thoroughly"
  ],
  "surface_type": "carpets_floors",
  "dirt_type": "stain",
  "cleaning_method": "manual"
}
```

Or with detailed step format:

```json
{
  "steps": [
    {
      "step": "Remove excess stain",
      "order": 1,
      "confidence": 0.8
    }
  ]
}
```

### 3. Integration Points

**Current Integration**:
- Reads from processed corpus (`data/processed/cleaning_docs.jsonl`)
- Uses steps extracted by enrichment pipeline
- Standalone module (no dependencies on other robot components)

**Future Integration** (Phase 2.2+):
- Will feed actions to MuJoCo simulator
- Actions will be validated in simulation
- Trajectories will be generated for robot execution

### 4. Pipeline Integration

To integrate action extraction into the pipeline:

```python
# In processing pipeline (future enhancement)
from src.robot.action_extractor import extract_actions_from_document

# After enrichment
document = enrichment_pipeline.enrich(document)

# Extract robot actions
actions = extract_actions_from_document(document)
document["robot_actions"] = actions
```

## Configuration

### ActionExtractor Parameters

```python
extractor = ActionExtractor(
    default_force=5.0,        # Default force (0-10 scale)
    default_duration=30,      # Default duration in seconds
    min_confidence=0.3        # Minimum confidence to accept action
)
```

### Customization

You can customize keyword lists in `action_extractor.py`:

- **ACTION_TYPE_KEYWORDS**: Add new action types
- **FORCE_KEYWORDS**: Add force level descriptors
- **TOOL_MAPPING**: Add tool name mappings
- **TIME_PATTERNS**: Add time parsing patterns

## Examples

### Example 1: Simple Step

**Input**:
```
"Apply cleaning solution and scrub gently for 2 minutes"
```

**Output**:
```json
{
  "action_type": "scrub",
  "tool": "detergent",
  "force": 3.0,
  "duration": 120,
  "pattern": null,
  "order": 1,
  "confidence": 1.0
}
```

### Example 2: Wait Action

**Input**:
```
"Wait 5 minutes for the solution to soak in"
```

**Output**:
```json
{
  "action_type": "wait",
  "tool": null,
  "force": 5.0,
  "duration": 300,
  "pattern": null,
  "order": 2,
  "confidence": 0.90
}
```

### Example 3: Complex Step

**Input**:
```
"Remove excess stain with a paper towel, then apply cleaning solution"
```

**Output**:
```json
{
  "action_type": "remove",
  "tool": "cloth",
  "force": 5.0,
  "duration": 30,
  "pattern": null,
  "order": 1,
  "confidence": 0.65
}
```

*Note: Currently extracts single action per step. Multi-action steps are handled as single primary action.*

## Limitations

1. **Single Action Per Step**: Each step extracts one primary action. Steps with multiple actions (e.g., "remove and apply") extract the first detected action.

2. **Language**: Currently optimized for English. Other languages may have lower accuracy.

3. **Context**: Limited context awareness. Doesn't consider previous steps or document-level context for disambiguation.

4. **Tool Inference**: Tool extraction relies on keyword matching. May miss tools mentioned indirectly.

5. **Pattern Detection**: Motion patterns are only detected if explicitly mentioned (circular, back and forth, etc.).

## Future Enhancements

1. **Multi-Action Steps**: Split steps with multiple actions into separate action objects
2. **LLM Integration**: Use LLM for better context understanding and disambiguation
3. **Learning from Examples**: Train on labeled examples to improve extraction accuracy
4. **Multi-language Support**: Add support for other languages
5. **Context Awareness**: Use previous steps and document context for better extraction

## Troubleshooting

### Low Confidence Scores

If actions have low confidence (< 0.3):
- Check if step text is too short (< 15 characters)
- Verify action keywords are present
- Consider lowering `min_confidence` threshold

### Missing Tools

If tools are not detected:
- Check if tool is mentioned in step text
- Add tool keywords to `TOOL_MAPPING` dictionary
- Tool may be inferred from action type

### Incorrect Action Types

If wrong action type is detected:
- Check keyword priority (wait actions checked first)
- Verify step text contains expected keywords
- Consider adding custom keywords to `ACTION_TYPE_KEYWORDS`

### Duration Not Extracted

If duration is default (30s) instead of extracted:
- Check if time is mentioned in standard format (e.g., "2 minutes")
- Verify time pattern matches `TIME_PATTERNS`
- Add custom time patterns if needed

## Related Files

- **Implementation**: `src/robot/action_extractor.py`
- **Package Init**: `src/robot/__init__.py`
- **Test Script**: `scripts/test_action_extractor.py`
- **Enrichment (steps source)**: `src/enrichment/extractors.py`
- **Corpus Data**: `data/processed/cleaning_docs.jsonl`

## Next Steps

**Phase 2.2**: MuJoCo Simulation Module
- Load robot models (Franka Panda, UR5, etc.)
- Simulate cleaning actions
- Validate motions (force, pressure, contact)
- Generate trajectories

**Phase 2.3**: Command Generator
- Convert actions → robot-executable commands
- Generate control sequences
- Output in robot-specific formats

## Summary

The Action Extraction Module successfully converts natural language cleaning steps into structured robot actions. It provides:

✅ 9 action types  
✅ Force/pressure extraction  
✅ Duration parsing  
✅ Tool detection  
✅ Motion pattern recognition  
✅ Confidence scoring  
✅ Document context integration  

The module is ready to feed structured actions into the MuJoCo simulator (Phase 2.2) for physics-based validation and trajectory generation.


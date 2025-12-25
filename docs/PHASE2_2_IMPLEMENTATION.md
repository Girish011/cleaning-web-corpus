# Phase 2.2: MuJoCo Simulation Module - Implementation Summary

## ✅ Implementation Complete

Phase 2.2 has been successfully implemented! This module provides physics-based simulation of cleaning robot actions using MuJoCo, validating motions, forces, and contacts, and generating trajectories.

## Overview

The MuJoCo Simulation Module is the second component of the robot simulation layer. It takes structured actions from the Action Extractor and simulates them in a physics engine to validate feasibility, check force/pressure requirements, detect contacts, and generate executable trajectories.

**Location**: `src/robot/mujoco_simulator.py`

## What Was Implemented

### 1. MuJoCoSimulator Class

**Purpose**: Simulate cleaning actions in MuJoCo physics engine

**Key Features**:
- Robot model loading (Franka Panda, UR5, simple_arm)
- Action simulation (all 9 action types)
- Force/pressure validation
- Contact detection
- Trajectory generation
- Motion validation (smoothness, feasibility)

**Key Methods**:

1. **`__init__(robot_model, model_path, timestep, enable_viewer)`** - Initialize simulator
   - Loads robot model from XML file
   - Creates minimal model if file not found
   - Sets up simulation environment

2. **`simulate_action(action, target_position, surface_normal)`** - Simulate single action
   - Input: Action dictionary from ActionExtractor
   - Output: Simulation results with trajectory, forces, contacts, validation
   - Validates force levels, contact, motion smoothness

3. **`_generate_trajectory(...)`** - Generate joint space trajectory
   - Supports multiple motion patterns (circular, back_and_forth, linear)
   - Handles wait actions (static)
   - Generates smooth motion paths

4. **`_get_contact_force()`** - Get current contact force
   - Returns total contact force magnitude in Newtons
   - Detects contacts between robot and environment

5. **`_validate_simulation(...)`** - Validate simulation results
   - Checks force levels match desired values
   - Validates contact presence/absence
   - Checks motion smoothness
   - Returns validation report with issues

6. **`generate_trajectory_file(actions, output_path, format)`** - Save trajectories
   - Generates trajectory files from multiple actions
   - Supports JSON and NumPy formats
   - Includes forces and contact data

7. **`is_available()`** - Check MuJoCo availability
   - Returns True if MuJoCo is installed
   - Graceful fallback if not available

### 2. Helper Function

**`simulate_actions_from_document(document, robot_model, output_dir)`** - Simulate document actions
- Extracts actions from document (if not present)
- Simulates all actions in sequence
- Saves trajectory files
- Returns comprehensive results

### 3. Robot Model Support

**Supported Models**:
- **Franka Panda**: 7-DOF manipulator with gripper
- **UR5**: 6-DOF industrial manipulator
- **Simple Arm**: 3-DOF test arm (default, auto-created if model files missing)

**Model Configuration**:
- Model paths configurable
- Auto-creates minimal model if file not found
- Supports custom model XML files

### 4. Action Type Motion Parameters

Each action type has predefined motion parameters:

| Action Type | Velocity (m/s) | Acceleration (m/s²) | Contact Force (N) | Motion Type |
|-------------|----------------|---------------------|-------------------|-------------|
| `apply` | 0.1 | 0.5 | 5.0 | linear |
| `scrub` | 0.15 | 1.0 | 10.0 | pattern |
| `vacuum` | 0.2 | 0.8 | 2.0 | linear |
| `rinse` | 0.12 | 0.6 | 1.0 | sweep |
| `dry` | 0.08 | 0.4 | 3.0 | pat |
| `wait` | 0.0 | 0.0 | 0.0 | static |
| `remove` | 0.15 | 0.7 | 0.0 | linear |
| `move` | 0.1 | 0.5 | 0.0 | linear |
| `check` | 0.05 | 0.3 | 0.0 | inspect |

## Requirements

### Dependencies

**Required**:
- `mujoco>=3.0.0` - MuJoCo physics engine
- `numpy>=1.24.0` - Numerical operations (already in requirements)

**Optional**:
- `mujoco.viewer` - For visualization (optional, may require additional setup)

### Installation

```bash
pip install mujoco
```

Or for legacy support:
```bash
pip install mujoco-py  # Legacy Python bindings
```

### Python Version

- Python 3.7+

### System Requirements

- **Linux/macOS**: MuJoCo works out of the box
- **Windows**: May require additional setup
- **GPU**: Optional, for faster simulation

## Usage

### Basic Usage

```python
from src.robot.mujoco_simulator import MuJoCoSimulator
from src.robot.action_extractor import ActionExtractor

# Initialize simulator
simulator = MuJoCoSimulator(robot_model="simple_arm")

# Extract action
extractor = ActionExtractor()
action = extractor.extract_action("Scrub gently for 2 minutes", step_order=1)

# Simulate action
result = simulator.simulate_action(action)

# Check results
if result["success"]:
    print(f"Trajectory points: {len(result['trajectory'])}")
    print(f"Max force: {max(result['forces']):.2f}N")
    print(f"Contacts: {len(result['contacts'])}")
    print(f"Validation: {result['validation']['summary']}")
else:
    print(f"Issues: {result['validation']['issues']}")

simulator.close()
```

### Simulate Multiple Actions

```python
actions = [
    {"action_type": "apply", "force": 5.0, "duration": 30, ...},
    {"action_type": "scrub", "force": 3.0, "duration": 120, ...},
    {"action_type": "wait", "force": 5.0, "duration": 300, ...},
]

simulator = MuJoCoSimulator(robot_model="simple_arm")

# Generate trajectory file
output_path = pathlib.Path("data/robot/trajectories.json")
simulator.generate_trajectory_file(actions, output_path, format="json")

simulator.close()
```

### Simulate from Document

```python
import json
from src.robot.mujoco_simulator import simulate_actions_from_document

# Load document
with open('data/processed/cleaning_docs.jsonl') as f:
    doc = json.loads(f.readline())

# Simulate all actions
result = simulate_actions_from_document(
    doc,
    robot_model="simple_arm",
    output_dir=pathlib.Path("data/robot/trajectories")
)

print(f"Simulated: {result['num_successful']}/{result['num_actions']} actions")
```

## Output Format

### Simulation Result Structure

```json
{
  "success": true,
  "trajectory": [
    [0.1, 0.2, 0.3, ...],  // Joint positions at timestep 0
    [0.11, 0.21, 0.31, ...],  // Joint positions at timestep 1
    ...
  ],
  "forces": [0.0, 0.5, 10.2, 8.5, ...],  // Contact forces over time
  "contacts": [
    {
      "time": 0.5,
      "force": 10.2,
      "position": [0.3, 0.0, 0.2]
    },
    ...
  ],
  "validation": {
    "valid": true,
    "force_valid": true,
    "contact_valid": true,
    "motion_valid": true,
    "summary": "Valid",
    "issues": [],
    "max_force": 10.2,
    "desired_force": 10.0,
    "contact_count": 5
  },
  "action_type": "scrub",
  "duration": 120,
  "simulated_duration": 120.0
}
```

## Integration with Framework

### 1. Data Flow

```
Action Extractor (Phase 2.1)
    ↓
Structured Actions
    ↓
MuJoCo Simulator (Phase 2.2)
    ↓
Validated Trajectories
    ↓
[Future: Command Generator (Phase 2.3)]
```

### 2. Input Format

The simulator expects action dictionaries from ActionExtractor:

```json
{
  "action_type": "scrub",
  "tool": "brush",
  "force": 3.0,
  "duration": 120,
  "pattern": "circular",
  "order": 1,
  "confidence": 1.0
}
```

### 3. Integration Points

**Current Integration**:
- Reads actions from ActionExtractor
- Standalone module (optional dependency)
- Gracefully handles missing MuJoCo

**Future Integration** (Phase 2.3):
- Trajectories will feed into Command Generator
- Commands will be converted to robot-specific formats
- Ready for real robot execution

### 4. Pipeline Integration

To integrate simulation into the pipeline:

```python
# In processing pipeline (future enhancement)
from src.robot.action_extractor import extract_actions_from_document
from src.robot.mujoco_simulator import simulate_actions_from_document

# After enrichment
document = enrichment_pipeline.enrich(document)

# Extract and simulate actions
actions = extract_actions_from_document(document)
simulation_result = simulate_actions_from_document(
    document,
    robot_model="franka_panda",
    output_dir=pathlib.Path("data/robot/trajectories")
)

document["robot_actions"] = actions
document["simulation_results"] = simulation_result
```

## Configuration

### MuJoCoSimulator Parameters

```python
simulator = MuJoCoSimulator(
    robot_model="simple_arm",      # Robot model name
    model_path=None,                # Optional custom model path
    timestep=0.002,                 # Simulation timestep (seconds)
    enable_viewer=False,            # Enable visual viewer
)
```

### Robot Models

Configured in `ROBOT_MODELS` dictionary:
- Model paths (relative to project root)
- DOF (degrees of freedom)
- Gripper availability
- Description

### Motion Parameters

Customize `ACTION_MOTION_PARAMS` for each action type:
- Velocity (m/s)
- Acceleration (m/s²)
- Contact force (N)
- Motion type (linear, pattern, sweep, etc.)

## Testing

### Test Script

A comprehensive test script is provided:

```bash
python scripts/test_mujoco_simulator.py
```

This script:
1. Tests MuJoCo availability
2. Tests individual action simulation
3. Tests document-level simulation
4. Shows validation results

### Manual Testing

```python
from src.robot.mujoco_simulator import MuJoCoSimulator
from src.robot.action_extractor import ActionExtractor

# Check availability
if not MuJoCoSimulator.is_available():
    print("MuJoCo not installed")
    print("Install with: pip install mujoco")
else:
    # Initialize
    sim = MuJoCoSimulator(robot_model="simple_arm")
    
    # Test action
    extractor = ActionExtractor()
    action = extractor.extract_action("Scrub gently for 2 minutes", 1)
    
    # Simulate
    result = sim.simulate_action(action)
    
    print(f"Success: {result['success']}")
    print(f"Validation: {result['validation']['summary']}")
    
    sim.close()
```

## Limitations

1. **Model Files**: Robot model XML files need to be provided separately. The simulator creates a minimal test model if files are missing.

2. **Inverse Kinematics**: Current implementation uses simplified trajectory generation. Full IK solver integration would improve accuracy.

3. **Contact Modeling**: Contact detection is basic. More sophisticated contact models would improve force validation.

4. **Tool Modeling**: Tools (brush, sponge, etc.) are not explicitly modeled. Contact forces are approximated.

5. **Surface Modeling**: Surfaces are not explicitly modeled. Contact validation uses simplified assumptions.

6. **Real-time**: Simulation runs faster than real-time but may be slow for long-duration actions.

## Future Enhancements

1. **Full IK Solver**: Integrate proper inverse kinematics for accurate end-effector positioning
2. **Tool Models**: Add explicit tool models (brush, sponge, etc.) to simulation
3. **Surface Models**: Model cleaning surfaces (carpet, floor, etc.) with proper physics
4. **Advanced Contact**: Implement more sophisticated contact models
5. **Visualization**: Add real-time visualization of simulation
6. **Optimization**: Optimize trajectory generation for efficiency
7. **Multi-robot**: Support multiple robots working together
8. **Sensor Simulation**: Add sensor feedback (force, vision, etc.)

## Troubleshooting

### MuJoCo Not Found

**Error**: `ModuleNotFoundError: No module named 'mujoco'`

**Solution**:
```bash
pip install mujoco
```

### Model File Not Found

**Error**: `Model file not found: models/franka_panda.xml`

**Solution**:
- The simulator will auto-create a minimal test model
- Or provide custom model path:
  ```python
  simulator = MuJoCoSimulator(
      robot_model="franka_panda",
      model_path=pathlib.Path("path/to/model.xml")
  )
  ```

### Simulation Too Slow

**Solutions**:
- Reduce simulation timestep (less accurate but faster)
- Reduce trajectory resolution
- Use simpler robot model
- Enable GPU acceleration (if available)

### Force Validation Fails

**Possible Causes**:
- Force scale mismatch (action force 0-10 vs Newtons)
- Contact not detected properly
- Motion parameters need adjustment

**Solutions**:
- Adjust force scaling in `_validate_simulation()`
- Check contact detection thresholds
- Tune motion parameters in `ACTION_MOTION_PARAMS`

## Related Files

- **Implementation**: `src/robot/mujoco_simulator.py`
- **Package Init**: `src/robot/__init__.py`
- **Test Script**: `scripts/test_mujoco_simulator.py`
- **Action Extractor**: `src/robot/action_extractor.py`
- **Requirements**: `requirements.txt` (mujoco>=3.0.0)

## Next Steps

**Phase 2.3**: Command Generator
- Convert validated trajectories → robot-executable commands
- Generate control sequences
- Output in robot-specific formats (ROS, MoveIt, etc.)
- Support multiple robot platforms

## Summary

The MuJoCo Simulation Module successfully simulates cleaning robot actions in a physics engine. It provides:

✅ Robot model loading (Franka Panda, UR5, simple_arm)  
✅ Action simulation (all 9 action types)  
✅ Force/pressure validation  
✅ Contact detection  
✅ Trajectory generation  
✅ Motion validation  
✅ Graceful fallback when MuJoCo not available  

The module is ready to feed validated trajectories into the Command Generator (Phase 2.3) for robot execution.


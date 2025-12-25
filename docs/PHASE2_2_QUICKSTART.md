# Phase 2.2: MuJoCo Simulator - Quick Start Guide

## Installation

```bash
# Activate virtual environment
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows

# Install MuJoCo
pip install mujoco
```

## Quick Test

```bash
# Test 1: Check if MuJoCo is available
python3 -c "from src.robot.mujoco_simulator import MuJoCoSimulator; print('Available:', MuJoCoSimulator.is_available())"

# Test 2: Run full test suite
python scripts/test_mujoco_simulator.py

# Test 3: Quick simulation test
python3 -c "
from src.robot.action_extractor import ActionExtractor
from src.robot.mujoco_simulator import MuJoCoSimulator

extractor = ActionExtractor()
action = extractor.extract_action('Scrub gently for 2 minutes', 1)

sim = MuJoCoSimulator(robot_model='simple_arm')
result = sim.simulate_action(action)
print(f'Success: {result[\"success\"]}')
print(f'Max force: {max(result[\"forces\"]):.2f}N')
sim.close()
"
```

## Test with Real Document

```bash
python3 -c "
import json
from src.robot.mujoco_simulator import simulate_actions_from_document

with open('data/processed/cleaning_docs.jsonl') as f:
    doc = json.loads(f.readline())

result = simulate_actions_from_document(doc, robot_model='simple_arm')
print(f'Simulated: {result[\"num_successful\"]}/{result[\"num_actions\"]} actions')
"
```

## View Live Simulation

### On Linux/Windows

```bash
# Run interactive viewer (opens GUI window)
python scripts/view_robot_simulation.py
```

### On macOS

**Important**: On macOS, the viewer requires `mjpython` instead of regular `python`.

**Option 1: Use the helper script (recommended)**
```bash
# Automatically detects and uses mjpython if available
python scripts/run_viewer_with_mjpython.py
```

**Option 2: Use mjpython directly**
```bash
# First, check if mjpython is available
python scripts/check_mjpython_setup.py

# If found, run with mjpython
mjpython scripts/view_robot_simulation.py
```

**Option 3: Run without viewer (simulation still works)**
```bash
# Simulation runs successfully, but no visual window
python scripts/view_robot_simulation.py
```

**Setup mjpython:**
- `mjpython` is included with MuJoCo installation
- If not found, reinstall: `pip install --upgrade mujoco`
- See [MUJOCO_VIEWER_SETUP.md](MUJOCO_VIEWER_SETUP.md) for detailed setup instructions

The viewer will:
- Open a MuJoCo viewer window (on macOS with mjpython, or Linux/Windows with regular python)
- Show robot motion in real-time
- Simulate multiple actions sequentially
- Display force and contact information

## Troubleshooting

**MuJoCo not found?**
```bash
pip install mujoco
```

**Import error?**
- Make sure you're in the project root
- Activate virtual environment
- Check Python version (3.7+)

**Model file not found?**
- Simulator auto-creates minimal test model
- No action needed

**Viewer doesn't work on macOS?**
```bash
# Check your setup
python scripts/check_mjpython_setup.py

# Use the helper script
python scripts/run_viewer_with_mjpython.py

# Or see detailed instructions
cat docs/MUJOCO_VIEWER_SETUP.md
```

**Error: "launch_passive requires mjpython on macOS"?**
- This is expected on macOS - use `mjpython` instead of `python`
- The helper script handles this automatically
- Simulation works fine without viewer (just no visual window)

## Expected Output

```
MuJoCo available: True
Model DOF: 3
Simulation: SUCCESS
  Trajectory points: 15000
  Max force: 10.2N
  Contacts: 5
  Validation: Valid
```


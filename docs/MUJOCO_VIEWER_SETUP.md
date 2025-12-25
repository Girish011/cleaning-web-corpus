# MuJoCo Viewer Setup for macOS

## Problem

On macOS, the MuJoCo viewer requires running Python scripts with `mjpython` instead of regular `python`. This is because macOS's Cocoa framework requires GUI operations to run on the main thread, which `mjpython` handles automatically.

## Error Message

If you see this error:
```
Could not initialize viewer: `launch_passive` requires that the Python script be run under `mjpython` on macOS
```

This means you need to use `mjpython` to run the viewer script.

## Solution 1: Use the Helper Script (Easiest)

We've created a helper script that automatically detects and uses `mjpython`:

```bash
python scripts/run_viewer_with_mjpython.py
```

This script will:
- Automatically find `mjpython` if it's installed
- Run the viewer with `mjpython` if found
- Provide helpful setup instructions if not found

## Solution 2: Install/Verify mjpython

The `mjpython` executable is included with the MuJoCo package. To ensure it's available:

1. **Reinstall MuJoCo** (to ensure mjpython is included):
   ```bash
   pip install --upgrade mujoco
   ```

2. **Find mjpython location**:
   ```bash
   python3 -c "import mujoco; import os; print(os.path.dirname(mujoco.__file__))"
   ```
   
   Then look for `mjpython` in the `bin/` directory nearby.

3. **Add to PATH** (optional, for convenience):
   
   Add to your `~/.zshrc`:
   ```bash
   # Find the mujoco installation directory
   MUJOCO_DIR=$(python3 -c "import mujoco; import os; print(os.path.dirname(os.path.dirname(mujoco.__file__)))")
   export PATH="$PATH:$MUJOCO_DIR/bin"
   ```
   
   Then reload:
   ```bash
   source ~/.zshrc
   ```

## Solution 3: Run Directly with mjpython

Once `mjpython` is available, use it directly:

```bash
mjpython scripts/view_robot_simulation.py
```

Or for the test script:

```bash
mjpython scripts/test_mujoco_simulator.py
```

## Solution 4: Use Full Path

If `mjpython` is not in your PATH, you can use the full path:

```bash
# First, find where it is
python3 -c "import mujoco; import os; from pathlib import Path; print(Path(mujoco.__file__).parent.parent / 'bin' / 'mjpython')"

# Then use the full path
/path/to/mjpython scripts/view_robot_simulation.py
```

## Verification

To check if `mjpython` is available:

```bash
which mjpython
```

If it returns a path, you're good to go!

## Alternative: Run Without Viewer

If you just want to test the simulation without visualization:

```bash
python scripts/test_mujoco_simulator.py
```

The simulation will run successfully, but you won't see the visual viewer. All simulation results (forces, contacts, trajectories) will still be computed and reported.

## Troubleshooting

### mjpython not found after installation

1. Make sure you're in the correct virtual environment:
   ```bash
   which python3  # Should show your venv path
   pip install --upgrade mujoco  # Install in the same venv
   ```

2. Check if mjpython was installed:
   ```bash
   find $(python3 -c "import site; print(site.getsitepackages()[0])") -name "mjpython*" 2>/dev/null
   ```

3. If still not found, try installing from source or check MuJoCo documentation for your specific version.

### Viewer still doesn't work

- Make sure you're running on macOS (this requirement is macOS-specific)
- Check that you have a display/GUI environment (not SSH without X11 forwarding)
- Try the helper script: `python scripts/run_viewer_with_mjpython.py`

### Permission errors

If you get permission errors when running mjpython:

```bash
chmod +x /path/to/mjpython
```

## Notes

- **Linux/Windows**: The viewer works with regular `python` - no `mjpython` needed
- **macOS**: Requires `mjpython` for the viewer, but simulation works fine without it
- The simulation itself (physics, forces, contacts) works perfectly without the viewer
- The viewer is only for visual debugging and demonstration

## Quick Reference

```bash
# macOS with viewer (requires mjpython)
mjpython scripts/view_robot_simulation.py

# macOS without viewer (works with regular python)
python scripts/view_robot_simulation.py

# Use helper script (auto-detects mjpython)
python scripts/run_viewer_with_mjpython.py

# Test simulation (no viewer needed)
python scripts/test_mujoco_simulator.py
```


#!/usr/bin/env python3
"""
Wrapper script to run viewer with mjpython on macOS.

This script automatically detects and uses mjpython if available,
or provides helpful instructions if not found.
"""

import subprocess
import sys
import shutil
import pathlib

def find_mjpython():
    """Try to find mjpython executable."""
    # Check if mjpython is in PATH
    mjpython_path = shutil.which("mjpython")
    if mjpython_path:
        return mjpython_path
    
    # Try to find it in common locations
    import site
    import os
    
    # Check in site-packages
    try:
        site_packages = site.getsitepackages()[0]
        # MuJoCo might install mjpython in bin directory
        possible_paths = [
            pathlib.Path(site_packages) / "bin" / "mjpython",
            pathlib.Path(site_packages) / "mujoco" / "bin" / "mjpython",
        ]
        
        for path in possible_paths:
            if path.exists() and os.access(path, os.X_OK):
                return str(path)
    except Exception:
        pass
    
    # Try to find via Python's mujoco module
    try:
        import mujoco
        mujoco_dir = pathlib.Path(mujoco.__file__).parent
        mjpython_path = mujoco_dir.parent / "bin" / "mjpython"
        if mjpython_path.exists():
            return str(mjpython_path)
    except Exception:
        pass
    
    return None


def main():
    """Run the viewer script with mjpython if available."""
    script_path = pathlib.Path(__file__).parent / "view_robot_simulation.py"
    
    if not script_path.exists():
        print(f"Error: Could not find {script_path}")
        return 1
    
    # Check if we're on macOS
    import platform
    is_macos = platform.system() == "Darwin"
    
    if is_macos:
        mjpython = find_mjpython()
        
        if mjpython:
            print(f"Found mjpython at: {mjpython}")
            print("Running viewer with mjpython...\n")
            # Run with mjpython
            result = subprocess.run([mjpython, str(script_path)] + sys.argv[1:])
            return result.returncode
        else:
            print("=" * 80)
            print("MUJOCO VIEWER SETUP FOR macOS")
            print("=" * 80)
            print("\nmjpython not found in PATH.")
            print("\nTo enable the viewer on macOS, you need to use 'mjpython' instead of 'python'.")
            print("\nSetup options:")
            print("\n1. Install/Reinstall MuJoCo (mjpython is included):")
            print("   pip install --upgrade mujoco")
            print("\n2. Add mjpython to your PATH:")
            print("   - Find where mujoco is installed:")
            print("     python3 -c \"import mujoco; import os; print(os.path.dirname(mujoco.__file__))\"")
            print("   - Look for mjpython in the bin/ directory")
            print("   - Add it to your PATH in ~/.zshrc:")
            print("     export PATH=\"$PATH:/path/to/mujoco/bin\"")
            print("\n3. Run directly with full path:")
            print("   /path/to/mjpython scripts/view_robot_simulation.py")
            print("\n4. Alternative: Use the regular Python (viewer won't work, but simulation will):")
            print("   python3 scripts/view_robot_simulation.py")
            print("\n" + "=" * 80)
            print("\nTrying to run without mjpython (viewer may not work)...\n")
            # Try running anyway - might work on some systems
            result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
            return result.returncode
    else:
        # Not macOS, use regular Python
        print("Running viewer with regular Python (not macOS, viewer should work)...\n")
        result = subprocess.run([sys.executable, str(script_path)] + sys.argv[1:])
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())


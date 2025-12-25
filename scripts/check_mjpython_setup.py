#!/usr/bin/env python3
"""
Check if mjpython is properly set up for macOS viewer.

This script helps diagnose viewer setup issues.
"""

import sys
import platform
import subprocess
import shutil
from pathlib import Path

def check_mujoco_installed():
    """Check if MuJoCo is installed."""
    try:
        import mujoco
        print(f"✓ MuJoCo is installed")
        print(f"  Version: {mujoco.__version__ if hasattr(mujoco, '__version__') else 'unknown'}")
        print(f"  Location: {mujoco.__file__}")
        return True, mujoco
    except ImportError:
        print("✗ MuJoCo is not installed")
        print("  Install with: pip install mujoco")
        return False, None

def find_mjpython():
    """Try to find mjpython."""
    # Check PATH
    mjpython_path = shutil.which("mjpython")
    if mjpython_path:
        print(f"✓ mjpython found in PATH: {mjpython_path}")
        return mjpython_path
    
    print("✗ mjpython not found in PATH")
    
    # Try to find via mujoco installation
    try:
        import mujoco
        import site
        import os
        
        mujoco_dir = Path(mujoco.__file__).parent
        site_packages = Path(site.getsitepackages()[0])
        
        # Common locations
        possible_locations = [
            site_packages / "bin" / "mjpython",
            site_packages.parent / "bin" / "mjpython",
            mujoco_dir.parent / "bin" / "mjpython",
            Path.home() / ".local" / "bin" / "mjpython",
        ]
        
        for loc in possible_locations:
            if loc.exists() and os.access(loc, os.X_OK):
                print(f"✓ mjpython found at: {loc}")
                print(f"  Add to PATH: export PATH=\"$PATH:{loc.parent}\"")
                return str(loc)
        
        print("  Could not find mjpython in common locations")
        print("  It should be included with mujoco installation")
        
    except Exception as e:
        print(f"  Error searching for mjpython: {e}")
    
    return None

def check_system():
    """Check system information."""
    print("=" * 80)
    print("SYSTEM INFORMATION")
    print("=" * 80)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Python executable: {sys.executable}")
    
    is_macos = platform.system() == "Darwin"
    if is_macos:
        print("\n✓ Running on macOS - mjpython is required for viewer")
    else:
        print("\n✓ Not macOS - regular python should work for viewer")
    
    return is_macos

def main():
    """Run all checks."""
    print("=" * 80)
    print("MUJOCO VIEWER SETUP CHECK")
    print("=" * 80)
    print()
    
    is_macos = check_system()
    print()
    
    mujoco_installed, mujoco_module = check_mujoco_installed()
    print()
    
    if not mujoco_installed:
        print("=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("Install MuJoCo first: pip install mujoco")
        return 1
    
    mjpython_path = find_mjpython()
    print()
    
    print("=" * 80)
    print("SETUP STATUS")
    print("=" * 80)
    
    if is_macos:
        if mjpython_path:
            print("✓ Setup looks good!")
            print(f"\nTo run the viewer, use:")
            print(f"  {mjpython_path} scripts/view_robot_simulation.py")
            print(f"\nOr use the helper script:")
            print(f"  python scripts/run_viewer_with_mjpython.py")
        else:
            print("✗ mjpython not found")
            print("\nSOLUTIONS:")
            print("\n1. Reinstall MuJoCo (mjpython should be included):")
            print("   pip install --upgrade mujoco")
            print("\n2. Check if mjpython exists but isn't in PATH:")
            print("   find $(python3 -c \"import site; print(site.getsitepackages()[0])\") -name \"mjpython*\" 2>/dev/null")
            print("\n3. Use the helper script (it will try to find mjpython):")
            print("   python scripts/run_viewer_with_mjpython.py")
            print("\n4. Run without viewer (simulation still works):")
            print("   python scripts/view_robot_simulation.py")
    else:
        print("✓ Setup looks good!")
        print("  On non-macOS systems, regular python should work for the viewer")
        print("\nTo run the viewer:")
        print("  python scripts/view_robot_simulation.py")
    
    print()
    return 0 if (not is_macos or mjpython_path) else 1

if __name__ == "__main__":
    sys.exit(main())


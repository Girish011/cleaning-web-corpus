#!/usr/bin/env python3
"""Test if the cleaning robot arm model loads correctly."""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.robot.mujoco_simulator import MuJoCoSimulator

def main():
    print("Testing model loading...")
    print("=" * 80)
    
    try:
        simulator = MuJoCoSimulator(robot_model="cleaning_robot_arm", enable_viewer=False)
        print(f"✓ Model loaded successfully!")
        print(f"  Model: {simulator.robot_model_name}")
        print(f"  DOF (joints): {simulator.model.nv}")
        print(f"  Actuators: {simulator.model.nu}")
        print(f"  Bodies: {simulator.model.nbody}")
        print(f"  Geoms: {simulator.model.ngeom}")
        
        # Check if it's actually the 6-DOF arm
        if simulator.model.nv == 6:
            print("\n✓ Correctly loaded 6-DOF robot arm!")
        else:
            print(f"\n⚠ Warning: Expected 6 DOF, got {simulator.model.nv}")
        
        simulator.close()
        return 0
    except Exception as e:
        print(f"\n✗ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


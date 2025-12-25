#!/usr/bin/env python3
"""Test script for pick-and-place functionality."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.robot.mujoco_simulator import MuJoCoSimulator


def test_pick_and_place():
    """Test pick-and-place action with bottle."""
    print("=" * 80)
    print("TEST: Pick-and-Place Action")
    print("=" * 80)
    
    try:
        # Initialize simulator with viewer
        simulator = MuJoCoSimulator(
            robot_model="cleaning_robot_arm",
            enable_viewer=False  # Set to True if you want visualization
        )
    except ImportError:
        print("MuJoCo not available, skipping test")
        return False
    except Exception as e:
        print(f"Error initializing simulator: {e}")
        return False
    
    # Create a pick action
    pick_action = {
        "action_type": "pick",
        "duration": 5.0,  # 5 seconds for pick
        "force": 0.0,
        "tool": "gripper",
        "order": 1,
    }
    
    print(f"\nSimulating pick action:")
    print(f"  Action: {pick_action['action_type']}")
    print(f"  Duration: {pick_action['duration']}s")
    
    try:
        result = simulator.simulate_action(pick_action)
        
        print(f"\nPick simulation result:")
        print(f"  Success: {result['success']}")
        print(f"  Trajectory points: {len(result['trajectory'])}")
        print(f"  Contacts: {len(result['contacts'])}")
        
        # Check for gripper contacts
        gripper_contacts = [c for c in result['contacts'] if c.get('gripper_contact', False)]
        print(f"  Gripper contacts: {len(gripper_contacts)}")
        
        if result['motion_log']['object_positions'].get('bottle'):
            bottle_pos = result['motion_log']['object_positions']['bottle']['position']
            print(f"  Bottle final position: [{bottle_pos[0]:.3f}, {bottle_pos[1]:.3f}, {bottle_pos[2]:.3f}]")
        
        print(f"  Validation: {result['validation']['summary']}")
        
    except Exception as e:
        print(f"  Error during pick simulation: {e}")
        import traceback
        traceback.print_exc()
        simulator.close()
        return False
    
    # Create a place action
    place_action = {
        "action_type": "place",
        "duration": 4.0,  # 4 seconds for place
        "force": 0.0,
        "tool": "gripper",
        "order": 2,
    }
    
    print(f"\nSimulating place action:")
    print(f"  Action: {place_action['action_type']}")
    print(f"  Duration: {place_action['duration']}s")
    
    try:
        result = simulator.simulate_action(place_action)
        
        print(f"\nPlace simulation result:")
        print(f"  Success: {result['success']}")
        print(f"  Trajectory points: {len(result['trajectory'])}")
        print(f"  Contacts: {len(result['contacts'])}")
        
        if result['motion_log']['object_positions'].get('bottle'):
            bottle_pos = result['motion_log']['object_positions']['bottle']['position']
            print(f"  Bottle final position: [{bottle_pos[0]:.3f}, {bottle_pos[1]:.3f}, {bottle_pos[2]:.3f}]")
        
        print(f"  Validation: {result['validation']['summary']}")
        
    except Exception as e:
        print(f"  Error during place simulation: {e}")
        import traceback
        traceback.print_exc()
        simulator.close()
        return False
    
    simulator.close()
    print("\n✓ Pick-and-place test completed!")
    return True


def main():
    """Run pick-and-place test."""
    success = test_pick_and_place()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())


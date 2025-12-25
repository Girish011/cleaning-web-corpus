#!/usr/bin/env python3
"""Interactive script to view robot simulation with live visualization."""

import pathlib
import sys
import logging

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# CHANGE: Configure logging to show detailed pick/place information
logging.basicConfig(
    level=logging.INFO,  # Show INFO level and above
    format='%(message)s',  # Simple format for cleaner output
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.robot.action_extractor import ActionExtractor
from src.robot.mujoco_simulator import MuJoCoSimulator


def main():
    """Run simulation with live viewer."""
    print("=" * 80)
    print("ROBOT SIMULATION VIEWER")
    print("=" * 80)
    
    # Check MuJoCo availability
    if not MuJoCoSimulator.is_available():
        print("\n✗ MuJoCo is not available!")
        print("  Install with: pip install mujoco")
        print("\n  Note: Viewer requires GUI environment (not headless)")
        return 1
    
    # Initialize
    print("\nInitializing simulator with viewer...")
    try:
        simulator = MuJoCoSimulator(
            robot_model="cleaning_robot_arm",  # Use the 6-DOF arm with props
            enable_viewer=True,
        )
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return 1
    
    # Extract actions
    print("\nExtracting actions from sample steps...")
    extractor = ActionExtractor()
    
    # CHANGE: Add pick action to test pick-and-place functionality
    test_steps = [
        "Pick up the cleaning bottle",
        "Place the bottle in the bucket",
        "Pick up the cleaning bottle",  # Test second attempt
        "Place the bottle on the table",
    ]
    
    actions = []
    for i, step in enumerate(test_steps, 1):
        action = extractor.extract_action(step, i)
        if action:
            # Cap durations for demo (max 12 seconds per action for viewer to allow slow movements)
            original_duration = action['duration']
            action['duration'] = min(action['duration'], 12.0)
            if original_duration != action['duration']:
                print(f"  [{i}] {action['action_type']} - {step[:50]}... (demo: {action['duration']}s)")
            else:
                print(f"  [{i}] {action['action_type']} - {step[:50]}...")
            actions.append(action)
    
    if not actions:
        print("✗ No actions extracted")
        simulator.close()
        return 1
    
    # Simulate with viewer
    print(f"\n{'=' * 80}")
    print(f"SIMULATING {len(actions)} ACTIONS")
    print(f"{'=' * 80}")
    print("\nViewer window should open showing robot motion...")
    print("Close viewer window or press Ctrl+C to stop\n")
    
    try:
        for i, action in enumerate(actions, 1):
            print(f"\nAction {i}/{len(actions)}: {action['action_type']} "
                  f"(duration: {action['duration']}s)")
            print("-" * 80)
            
            result = simulator.simulate_action(action)
            
            if result["success"]:
                print(f"\n  ✓ Success - Max force: {max(result['forces']):.2f}N, "
                      f"Contacts: {len(result['contacts'])}")
                
                # CHANGE: Show additional info for pick/place actions
                if action['action_type'] in ['pick', 'grasp', 'place', 'put']:
                    if result.get('motion_log', {}).get('object_positions', {}).get('bottle'):
                        bottle_pos = result['motion_log']['object_positions']['bottle']['position']
                        print(f"  Bottle final position: [{bottle_pos[0]:.3f}, {bottle_pos[1]:.3f}, {bottle_pos[2]:.3f}]")
                    
                    # Count gripper contacts
                    gripper_contacts = [c for c in result.get('contacts', []) if c.get('gripper_contact', False)]
                    print(f"  Gripper contacts: {len(gripper_contacts)}")
            else:
                print(f"\n  ✗ Failed - {result['validation']['summary']}")
            
            # Small pause between actions
            import time
            time.sleep(0.5)
        
        print(f"\n{'=' * 80}")
        print("SIMULATION COMPLETE")
        print(f"{'=' * 80}")
        print("\nClose viewer window when done...")
        
        # Keep viewer open (skip input in non-interactive environments)
        try:
            input("\nPress Enter to close viewer...")
        except (EOFError, KeyboardInterrupt):
            print("Closing viewer...")
        
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
    except Exception as e:
        print(f"\n✗ Simulation error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulator.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


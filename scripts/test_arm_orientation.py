#!/usr/bin/env python3
"""Test script to debug arm orientation and pick bottle step by step."""

import pathlib
import sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.robot.mujoco_simulator import MuJoCoSimulator


def test_step1_orientation():
    """Step 1: Just rotate base to face bottle."""
    print("=" * 80)
    print("STEP 1: Rotate base to face bottle")
    print("=" * 80)
    
    simulator = MuJoCoSimulator(robot_model="cleaning_robot_arm", enable_viewer=False)
    
    # Bottle position
    bottle_pos = np.array([0.1, 0.15, 0.17])
    base_pos = np.array([0.0, 0.0, 0.17])
    
    # Compute angle
    relative = bottle_pos - base_pos
    angle = np.arctan2(relative[1], relative[0])
    
    print(f"Bottle position: {bottle_pos}")
    print(f"Base position: {base_pos}")
    print(f"Relative: {relative}")
    print(f"Computed angle: {angle:.3f} rad ({np.degrees(angle):.1f}°)")
    
    # Reset and set base rotation
    mujoco.mj_resetData(simulator.model, simulator.data)
    
    # Try different angles to see which one works
    test_angles = [
        angle,  # Direct angle
        angle + np.pi,  # Opposite direction
        angle - np.pi/2,  # 90 degrees offset
        angle + np.pi/2,  # -90 degrees offset
    ]
    
    for i, test_angle in enumerate(test_angles):
        print(f"\nTest {i+1}: Setting base rotation to {test_angle:.3f} rad ({np.degrees(test_angle):.1f}°)")
        simulator.data.qpos[0] = np.clip(test_angle, -2.2, 2.2)
        simulator.data.qpos[1] = -0.2  # Shoulder
        simulator.data.qpos[2] = 0.3   # Elbow
        simulator.data.qpos[3] = 0.0   # Wrist pitch
        simulator.data.qpos[4] = 0.0   # Wrist roll
        simulator.data.qpos[5] = 0.0   # Gripper open
        
        mujoco.mj_forward(simulator.model, simulator.data)
        
        # Get end-effector position
        ee_pos = simulator.data.xpos[-1].copy()
        print(f"  End-effector position: [{ee_pos[0]:.3f}, {ee_pos[1]:.3f}, {ee_pos[2]:.3f}]")
        
        # Compute direction from base to end-effector
        ee_relative = ee_pos - base_pos
        ee_angle = np.arctan2(ee_relative[1], ee_relative[0])
        print(f"  End-effector direction: {ee_angle:.3f} rad ({np.degrees(ee_angle):.1f}°)")
        print(f"  Direction to bottle: {angle:.3f} rad ({np.degrees(angle):.1f}°)")
        print(f"  Angle difference: {abs(ee_angle - angle):.3f} rad ({np.degrees(abs(ee_angle - angle)):.1f}°)")
    
    simulator.close()
    return angle


def test_step2_ik_to_bottle():
    """Step 2: Use IK to reach bottle position."""
    print("\n" + "=" * 80)
    print("STEP 2: Use IK to reach bottle")
    print("=" * 80)
    
    simulator = MuJoCoSimulator(robot_model="cleaning_robot_arm", enable_viewer=False)
    
    # Bottle position
    bottle_pos = np.array([0.1, 0.15, 0.17])
    
    # Reset
    mujoco.mj_resetData(simulator.model, simulator.data)
    
    # Set initial pose
    current_qpos = simulator.data.qpos.copy()
    
    # Compute IK
    target_qpos = simulator._compute_ik_approximation(bottle_pos, current_qpos, len(current_qpos))
    
    print(f"Target position: {bottle_pos}")
    print(f"Computed joint angles:")
    print(f"  Base rotation: {target_qpos[0]:.3f} rad ({np.degrees(target_qpos[0]):.1f}°)")
    print(f"  Shoulder (pitch): {target_qpos[1]:.3f} rad ({np.degrees(target_qpos[1]):.1f}°)")
    print(f"  Elbow: {target_qpos[2]:.3f} rad ({np.degrees(target_qpos[2]):.1f}°)")
    print(f"  Wrist pitch: {target_qpos[3]:.3f} rad ({np.degrees(target_qpos[3]):.1f}°)")
    print(f"  Wrist roll: {target_qpos[4]:.3f} rad ({np.degrees(target_qpos[4]):.1f}°)")
    print(f"  Gripper: {target_qpos[5]:.3f} rad")
    
    # Set joint positions
    simulator.data.qpos[:] = target_qpos
    mujoco.mj_forward(simulator.model, simulator.data)
    
    # Check end-effector position
    ee_pos = simulator.data.xpos[-1].copy()
    print(f"\nActual end-effector position: [{ee_pos[0]:.3f}, {ee_pos[1]:.3f}, {ee_pos[2]:.3f}]")
    print(f"Target position: [{bottle_pos[0]:.3f}, {bottle_pos[1]:.3f}, {bottle_pos[2]:.3f}]")
    distance = np.linalg.norm(ee_pos - bottle_pos)
    print(f"Distance to target: {distance:.3f} m")
    
    # Check direction
    base_pos = np.array([0.0, 0.0, 0.17])
    ee_relative = ee_pos - base_pos
    target_relative = bottle_pos - base_pos
    ee_angle = np.arctan2(ee_relative[1], ee_relative[0])
    target_angle = np.arctan2(target_relative[1], target_relative[0])
    print(f"End-effector direction: {ee_angle:.3f} rad ({np.degrees(ee_angle):.1f}°)")
    print(f"Target direction: {target_angle:.3f} rad ({np.degrees(target_angle):.1f}°)")
    print(f"Direction difference: {abs(ee_angle - target_angle):.3f} rad ({np.degrees(abs(ee_angle - target_angle)):.1f}°)")
    
    simulator.close()
    return target_qpos[0]  # Return base rotation that worked


def test_step3_pick_bottle():
    """Step 3: Test pick action."""
    print("\n" + "=" * 80)
    print("STEP 3: Pick bottle action")
    print("=" * 80)
    
    simulator = MuJoCoSimulator(robot_model="cleaning_robot_arm", enable_viewer=False)
    
    pick_action = {
        "action_type": "pick",
        "duration": 5.0,
        "force": 0.0,
        "tool": "gripper",
        "order": 1,
    }
    
    print("Simulating pick action...")
    result = simulator.simulate_action(pick_action)
    
    print(f"Success: {result['success']}")
    print(f"Final end-effector: {result['motion_log']['final_end_effector']['position']}")
    if result['motion_log']['object_positions'].get('bottle'):
        bottle_pos = result['motion_log']['object_positions']['bottle']['position']
        print(f"Bottle position: {bottle_pos}")
    
    simulator.close()
    return result['success']


def main():
    """Run step-by-step tests."""
    print("\n" + "=" * 80)
    print("ARM ORIENTATION DEBUG TEST")
    print("=" * 80)
    
    # Step 1: Test orientation
    angle = test_step1_orientation()
    
    # Step 2: Test IK
    base_rot = test_step2_ik_to_bottle()
    
    # Step 3: Test pick
    success = test_step3_pick_bottle()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Computed angle to bottle: {angle:.3f} rad ({np.degrees(angle):.1f}°)")
    print(f"IK base rotation: {base_rot:.3f} rad ({np.degrees(base_rot):.1f}°)")
    print(f"Pick action: {'SUCCESS' if success else 'FAILED'}")
    print("=" * 80)
    
    return 0 if success else 1


if __name__ == "__main__":
    import mujoco
    sys.exit(main())


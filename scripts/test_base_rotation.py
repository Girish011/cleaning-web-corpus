#!/usr/bin/env python3
"""Simple test to find correct base rotation offset."""

import pathlib
import sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.robot.mujoco_simulator import MuJoCoSimulator
import mujoco

def test_base_rotation():
    """Test different base rotations to find correct orientation."""
    print("=" * 80)
    print("TEST: Find correct base rotation")
    print("=" * 80)
    
    simulator = MuJoCoSimulator(robot_model="cleaning_robot_arm", enable_viewer=False)
    
    # Bottle position
    bottle_pos = np.array([0.1, 0.15, 0.17])
    base_pos = np.array([0.0, 0.0, 0.17])
    target_angle = np.arctan2(bottle_pos[1] - base_pos[1], bottle_pos[0] - base_pos[0])
    
    print(f"Bottle position: {bottle_pos}")
    print(f"Target angle: {target_angle:.3f} rad ({np.degrees(target_angle):.1f}°)")
    print("\nTesting different base rotations:")
    print("-" * 80)
    
    # Test angles around the target
    test_angles = np.linspace(-np.pi, np.pi, 17)  # Test from -180° to +180°
    
    best_angle = None
    best_distance = float('inf')
    best_ee_pos = None
    
    for test_angle in test_angles:
        # Reset
        mujoco.mj_resetData(simulator.model, simulator.data)
        
        # Set base rotation
        simulator.data.qpos[0] = np.clip(test_angle, -2.2, 2.2)
        # Set other joints to a reasonable pose
        simulator.data.qpos[1] = -0.5  # Shoulder down
        simulator.data.qpos[2] = 0.5   # Elbow bent
        simulator.data.qpos[3] = 0.0   # Wrist
        simulator.data.qpos[4] = 0.0   # Wrist roll
        simulator.data.qpos[5] = 0.0   # Gripper
        
        # Forward kinematics
        mujoco.mj_forward(simulator.model, simulator.data)
        
        # Get end-effector position (gripper_moving_finger)
        try:
            ee_id = mujoco.mj_name2id(simulator.model, mujoco.mjtObj.mjOBJ_BODY, "gripper_moving_finger")
            if ee_id >= 0:
                ee_pos = simulator.data.xpos[ee_id].copy()
            else:
                ee_pos = simulator.data.xpos[-1].copy()
        except:
            ee_pos = simulator.data.xpos[-1].copy()
        ee_relative = ee_pos - base_pos
        ee_angle = np.arctan2(ee_relative[1], ee_relative[0])
        
        # Distance to bottle
        distance = np.linalg.norm(ee_pos - bottle_pos)
        
        # Angle difference
        angle_diff = abs(ee_angle - target_angle)
        if angle_diff > np.pi:
            angle_diff = 2 * np.pi - angle_diff
        
        print(f"Base rot: {test_angle:6.3f} rad ({np.degrees(test_angle):6.1f}°) | "
              f"EE: [{ee_pos[0]:5.2f}, {ee_pos[1]:5.2f}, {ee_pos[2]:5.2f}] | "
              f"EE angle: {ee_angle:5.2f} rad ({np.degrees(ee_angle):5.1f}°) | "
              f"Dist: {distance:.3f}m | Angle diff: {np.degrees(angle_diff):5.1f}°")
        
        # Track best (closest angle to target)
        if angle_diff < best_distance:
            best_distance = angle_diff
            best_angle = test_angle
            best_ee_pos = ee_pos.copy()
    
    print("\n" + "=" * 80)
    print(f"BEST BASE ROTATION: {best_angle:.3f} rad ({np.degrees(best_angle):.1f}°)")
    print(f"  End-effector: {best_ee_pos}")
    print(f"  Angle difference: {np.degrees(best_distance):.1f}°")
    print(f"  Target angle: {target_angle:.3f} rad ({np.degrees(target_angle):.1f}°)")
    print(f"  OFFSET NEEDED: {target_angle - best_angle:.3f} rad ({np.degrees(target_angle - best_angle):.1f}°)")
    print("=" * 80)
    
    simulator.close()
    return best_angle, target_angle - best_angle

if __name__ == "__main__":
    test_base_rotation()


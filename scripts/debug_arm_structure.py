#!/usr/bin/env python3
"""Debug arm structure to find end-effector body."""

import pathlib
import sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.robot.mujoco_simulator import MuJoCoSimulator
import mujoco

def debug_arm():
    """Debug arm structure."""
    simulator = MuJoCoSimulator(robot_model="cleaning_robot_arm", enable_viewer=False)
    
    print("=" * 80)
    print("ARM STRUCTURE DEBUG")
    print("=" * 80)
    
    # List all bodies
    print("\nAll bodies in model:")
    for i in range(simulator.model.nbody):
        body_name = mujoco.mj_id2name(simulator.model, mujoco.mjtObj.mjOBJ_BODY, i)
        body_pos = simulator.model.body_pos[i]
        print(f"  [{i:2d}] {body_name:30s} pos: [{body_pos[0]:6.3f}, {body_pos[1]:6.3f}, {body_pos[2]:6.3f}]")
    
    # List all joints
    print("\nAll joints in model:")
    for i in range(simulator.model.njnt):
        joint_name = mujoco.mj_id2name(simulator.model, mujoco.mjtObj.mjOBJ_JOINT, i)
        joint_type = simulator.model.jnt_type[i]
        joint_addr = simulator.model.jnt_qposadr[i]
        print(f"  [{i:2d}] {joint_name:30s} type: {joint_type} qpos_addr: {joint_addr}")
    
    # Reset and set base rotation
    mujoco.mj_resetData(simulator.model, simulator.data)
    simulator.data.qpos[0] = 0.0  # Base rotation = 0
    mujoco.mj_forward(simulator.model, simulator.data)
    
    print("\nWith base_rotation = 0:")
    for i in range(simulator.model.nbody):
        body_name = mujoco.mj_id2name(simulator.model, mujoco.mjtObj.mjOBJ_BODY, i)
        if body_name and ("gripper" in body_name.lower() or "finger" in body_name.lower()):
            body_pos = simulator.data.xpos[i]
            print(f"  {body_name:30s} pos: [{body_pos[0]:6.3f}, {body_pos[1]:6.3f}, {body_pos[2]:6.3f}]")
    
    # Try with base rotation = π/2
    simulator.data.qpos[0] = np.pi / 2
    mujoco.mj_forward(simulator.model, simulator.data)
    
    print("\nWith base_rotation = π/2:")
    for i in range(simulator.model.nbody):
        body_name = mujoco.mj_id2name(simulator.model, mujoco.mjtObj.mjOBJ_BODY, i)
        if body_name and ("gripper" in body_name.lower() or "finger" in body_name.lower()):
            body_pos = simulator.data.xpos[i]
            print(f"  {body_name:30s} pos: [{body_pos[0]:6.3f}, {body_pos[1]:6.3f}, {body_pos[2]:6.3f}]")
    
    # Find end-effector (gripper_moving_finger)
    try:
        ee_id = mujoco.mj_name2id(simulator.model, mujoco.mjtObj.mjOBJ_BODY, "gripper_moving_finger")
        if ee_id >= 0:
            print(f"\nEnd-effector body ID: {ee_id} (gripper_moving_finger)")
            print(f"  Position with base_rot=0: {simulator.data.xpos[ee_id]}")
            simulator.data.qpos[0] = np.pi / 2
            mujoco.mj_forward(simulator.model, simulator.data)
            print(f"  Position with base_rot=π/2: {simulator.data.xpos[ee_id]}")
    except:
        print("\nCould not find gripper_moving_finger")
    
    simulator.close()

if __name__ == "__main__":
    debug_arm()


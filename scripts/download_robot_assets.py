#!/usr/bin/env python3
"""Download STL assets for the low-cost robot arm from MuJoCo Menagerie."""

import pathlib
import urllib.request
import sys

BASE_URL = "https://raw.githubusercontent.com/google-deepmind/mujoco_menagerie/main/low_cost_robot_arm/assets/"
ASSETS_DIR = pathlib.Path(__file__).parent.parent / "models" / "low_cost_robot_arm" / "assets"

# List of required STL files
STL_FILES = [
    "base_link.stl",
    "shoulder_rotation.stl",
    "shoulder_to_elbow.stl",
    "elbow_to_wrist_extension.stl",
    "elbow_to_wrist.stl",
    "gripper_static_finger.stl",
    "gripper_moving_finger.stl",
    "base_link_motor.stl",
    "shoulder_rotation_motor.stl",
    "shoulder_to_elbow_motor.stl",
    "elbow_to_wrist_extension_motor.stl",
    "elbow_to_wrist_motor.stl",
    "gripper_static_finger_motor.stl",
    "base_link_collision.stl",
    "shoulder_rotation_collision.stl",
    "shoulder_to_elbow_collision.stl",
    "elbow_to_wrist_extension_collision.stl",
    "elbow_to_wrist_collision.stl",
    "gripper_static_finger_collision_1.stl",
    "gripper_static_finger_collision_2.stl",
    "gripper_moving_finger_collision_1.stl",
    "gripper_moving_finger_collision_2.stl",
]


def download_file(url: str, dest: pathlib.Path) -> bool:
    """Download a file from URL to destination."""
    try:
        print(f"Downloading {dest.name}...", end=" ", flush=True)
        urllib.request.urlretrieve(url, dest)
        print("✓")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Download all required STL assets."""
    print("=" * 80)
    print("DOWNLOADING ROBOT ARM ASSETS")
    print("=" * 80)
    print(f"\nDestination: {ASSETS_DIR}")
    print(f"Files to download: {len(STL_FILES)}\n")
    
    # Create assets directory
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download each file
    success_count = 0
    for stl_file in STL_FILES:
        url = BASE_URL + stl_file
        dest = ASSETS_DIR / stl_file
        if dest.exists():
            print(f"Skipping {stl_file} (already exists)")
            success_count += 1
        else:
            if download_file(url, dest):
                success_count += 1
    
    print(f"\n{'=' * 80}")
    print(f"DOWNLOAD COMPLETE: {success_count}/{len(STL_FILES)} files")
    print(f"{'=' * 80}")
    
    if success_count == len(STL_FILES):
        print("\n✓ All assets downloaded successfully!")
        print("You can now use the cleaning_robot_arm model.")
        return 0
    else:
        print(f"\n⚠ Warning: {len(STL_FILES) - success_count} files failed to download.")
        print("The robot model may not work correctly without all assets.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


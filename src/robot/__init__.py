"""
Robot simulation layer for converting cleaning knowledge into robot-executable actions.

This package provides:
- Action extraction from text steps
- MuJoCo simulation capabilities
- Command generation for robot execution
"""

from src.robot.action_extractor import ActionExtractor

# Try to import MuJoCo simulator (optional dependency)
try:
    from src.robot.mujoco_simulator import MuJoCoSimulator, simulate_actions_from_document
    __all__ = ["ActionExtractor", "MuJoCoSimulator", "simulate_actions_from_document"]
except ImportError:
    # MuJoCo not available, only export ActionExtractor
    __all__ = ["ActionExtractor"]


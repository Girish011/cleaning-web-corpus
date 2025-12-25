#!/usr/bin/env python3
"""Test script for MuJoCo simulator."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.robot.action_extractor import ActionExtractor
from src.robot.mujoco_simulator import MuJoCoSimulator, simulate_actions_from_document


def test_simulator_availability():
    """Test if MuJoCo is available."""
    print("=" * 80)
    print("TEST 1: MuJoCo Availability")
    print("=" * 80)
    
    try:
        simulator = MuJoCoSimulator(robot_model="simple_arm")
        available = simulator.is_available()
        print(f"MuJoCo available: {available}")
        
        if available:
            print(f"  Model DOF: {simulator.model.nv}")
            print(f"  Timestep: {simulator.timestep}s")
            simulator.close()
            return True
        else:
            print("  MuJoCo not installed. Install with: pip install mujoco")
            return False
    except ImportError as e:
        print(f"  MuJoCo import failed: {e}")
        print("  Install with: pip install mujoco")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def test_action_simulation():
    """Test simulating individual actions."""
    print("\n" + "=" * 80)
    print("TEST 2: Action Simulation")
    print("=" * 80)
    
    try:
        simulator = MuJoCoSimulator(robot_model="simple_arm")
    except ImportError:
        print("MuJoCo not available, skipping test")
        return False
    
    extractor = ActionExtractor()
    
    test_steps = [
        "Apply cleaning solution and scrub gently for 2 minutes",
        "Wait 5 minutes for the solution to soak in",
        "Remove excess stain with a paper towel",
    ]
    
    print(f"\nTesting {len(test_steps)} actions:")
    print("-" * 80)
    
    for i, step in enumerate(test_steps, 1):
        print(f"\nAction {i}: {step}")
        
        # Extract action
        action = extractor.extract_action(step, i)
        if not action:
            print("  Failed to extract action")
            continue
        
        print(f"  Extracted: {action['action_type']} | "
              f"Force: {action['force']} | Duration: {action['duration']}s")
        
        # Simulate
        try:
            result = simulator.simulate_action(action)
            
            print(f"  Simulation: {'SUCCESS' if result['success'] else 'FAILED'}")
            print(f"    Trajectory points: {len(result['trajectory'])}")
            print(f"    Max force: {max(result['forces']) if result['forces'] else 0:.2f}N")
            print(f"    Contacts: {len(result['contacts'])}")
            print(f"    Validation: {result['validation']['summary']}")
            
            if result['validation']['issues']:
                print(f"    Issues: {', '.join(result['validation']['issues'])}")
                
        except Exception as e:
            print(f"  Simulation error: {e}")
    
    simulator.close()
    return True


def test_document_simulation():
    """Test simulating actions from a document."""
    print("\n" + "=" * 80)
    print("TEST 3: Document Simulation")
    print("=" * 80)
    
    processed_file = ROOT / "data" / "processed" / "cleaning_docs.jsonl"
    if not processed_file.exists():
        print(f"Processed file not found: {processed_file}")
        return False
    
    try:
        with processed_file.open() as f:
            for line_num, line in enumerate(f, 1):
                if line_num > 1:  # Test first document only
                    break
                
                doc = json.loads(line)
                url = doc.get("url", "unknown")
                steps = doc.get("steps", [])
                
                if not steps:
                    print("No steps in document")
                    continue
                
                print(f"\nDocument: {url[:60]}...")
                print(f"  Steps: {len(steps)}")
                
                # Simulate
                try:
                    result = simulate_actions_from_document(
                        doc,
                        robot_model="simple_arm",
                    )
                    
                    if result.get("success"):
                        print(f"  Simulated: {result['num_successful']}/{result['num_actions']} actions")
                    else:
                        print(f"  Simulation failed: {result.get('error', 'unknown')}")
                        
                except Exception as e:
                    print(f"  Error: {e}")
                
    except Exception as e:
        print(f"Error reading document: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("MUJOCO SIMULATOR TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test 1: Availability
    results.append(("Availability", test_simulator_availability()))
    
    # Test 2: Action simulation
    if results[0][1]:  # Only if MuJoCo is available
        results.append(("Action Simulation", test_action_simulation()))
        results.append(("Document Simulation", test_document_simulation()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + ("=" * 80))
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed or were skipped")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


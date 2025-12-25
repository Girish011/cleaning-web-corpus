#!/usr/bin/env python3
"""Test script for action extractor."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.robot.action_extractor import ActionExtractor, extract_actions_from_document


def main():
    """Test action extractor with sample steps and real documents."""
    extractor = ActionExtractor()
    
    print("=" * 80)
    print("ACTION EXTRACTOR TEST")
    print("=" * 80)
    
    # Test 1: Sample steps
    print("\n1. Testing with sample steps:")
    print("-" * 80)
    
    test_steps = [
        "Apply cleaning solution and scrub gently for 2 minutes",
        "Wait 5 minutes for the solution to soak in",
        "Remove excess stain with a paper towel",
        "Rinse thoroughly with cold water",
        "Vacuum the carpet to remove debris",
        "Dry the surface with a clean cloth",
    ]
    
    for i, step in enumerate(test_steps, 1):
        action = extractor.extract_action(step, i)
        if action:
            print(f"\nStep {i}: {step}")
            print(f"  → Action: {action['action_type']} | Tool: {action['tool']} | "
                  f"Force: {action['force']} | Duration: {action['duration']}s | "
                  f"Confidence: {action['confidence']:.2f}")
        else:
            print(f"\nStep {i}: {step}")
            print("  → Failed to extract")
    
    # Test 2: Real document
    print("\n\n2. Testing with real document from corpus:")
    print("-" * 80)
    
    processed_file = ROOT / "data" / "processed" / "cleaning_docs.jsonl"
    if not processed_file.exists():
        print(f"Processed file not found: {processed_file}")
        return
    
    with processed_file.open() as f:
        for line_num, line in enumerate(f, 1):
            if line_num > 3:  # Test first 3 documents
                break
            
            doc = json.loads(line)
            url = doc.get("url", "unknown")
            steps = doc.get("steps", [])
            
            if not steps:
                continue
            
            print(f"\nDocument {line_num}: {url[:60]}...")
            print(f"  Steps in document: {len(steps)}")
            
            actions = extract_actions_from_document(doc)
            print(f"  Actions extracted: {len(actions)}")
            
            if actions:
                print("\n  Extracted actions:")
                for action in actions[:3]:  # Show first 3
                    print(f"    [{action['order']}] {action['action_type']} "
                          f"(tool: {action['tool']}, force: {action['force']}, "
                          f"duration: {action['duration']}s, conf: {action['confidence']:.2f})")
    
    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()


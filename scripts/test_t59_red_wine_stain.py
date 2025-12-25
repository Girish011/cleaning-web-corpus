#!/usr/bin/env python3
"""
Test script for T59: Red wine stain scenario.

Tests the /api/v1/plan_workflow endpoint with a red wine stain query
to verify that spot_clean is selected as the primary method and
method_selection metadata is populated correctly.
"""

import json
import requests
import sys

API_BASE_URL = "http://localhost:8000"


def test_red_wine_stain():
    """Test red wine stain scenario."""
    print("Testing red wine stain scenario...")
    print("=" * 60)
    
    request_body = {
        "query": "Remove red wine stain from wool carpet",
        "constraints": {
            "no_bleach": True,
            "gentle_only": True
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/plan_workflow",
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        print("\n✓ Request successful!")
        print("\nResponse Summary:")
        print("-" * 60)
        print(f"Workflow ID: {result.get('workflow_id')}")
        print(f"\nScenario:")
        scenario = result.get('scenario', {})
        print(f"  Surface Type: {scenario.get('surface_type')}")
        print(f"  Dirt Type: {scenario.get('dirt_type')}")
        print(f"  Cleaning Method: {scenario.get('cleaning_method')}")
        
        print(f"\nMethod Selection Metadata:")
        metadata = result.get('metadata', {})
        method_selection = metadata.get('method_selection')
        if method_selection:
            print(f"  Chosen Method: {method_selection.get('chosen_method')}")
            print(f"  Selection Reason: {method_selection.get('selection_reason')}")
            print(f"\n  Candidates:")
            for candidate in method_selection.get('candidates', [])[:5]:  # Show top 5
                print(f"    - {candidate.get('method')}: {candidate.get('score'):.3f}")
        else:
            print("  ⚠ No method_selection metadata found!")
        
        print(f"\nWorkflow Steps: {len(result.get('workflow', {}).get('steps', []))}")
        print(f"Required Tools: {len(result.get('workflow', {}).get('required_tools', []))}")
        
        print("\n" + "=" * 60)
        print("\nFull Response (JSON):")
        print(json.dumps(result, indent=2))
        
        return result
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Is the server running?")
        print("  Start it with: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"  Response text: {e.response.text}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_red_wine_stain()
    if result:
        print("\n✓ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Test failed!")
        sys.exit(1)


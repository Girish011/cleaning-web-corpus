#!/usr/bin/env python3
"""
Simple test script for the FastAPI /plan_workflow endpoint.

Usage:
    python scripts/test_api.py
"""

import json
import requests
import sys

API_BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        print(f"✓ Health check passed: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Is the server running?")
        print("  Start it with: uvicorn src.api.main:app --reload")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_plan_workflow():
    """Test the /plan_workflow endpoint."""
    print("\nTesting /plan_workflow endpoint...")
    
    # Test request
    request_data = {
        "query": "Remove red wine stain from wool carpet",
        "constraints": {
            "no_bleach": True,
            "gentle_only": True
        },
        "context": {
            "location": "living_room",
            "material": "wool",
            "urgency": "normal"
        }
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/plan_workflow",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Workflow planning succeeded!")
            print(f"\nWorkflow ID: {result.get('workflow_id')}")
            print(f"Scenario: {result.get('scenario', {}).get('surface_type')} × {result.get('scenario', {}).get('dirt_type')} × {result.get('scenario', {}).get('cleaning_method')}")
            print(f"Steps: {len(result.get('workflow', {}).get('steps', []))}")
            print(f"Tools: {len(result.get('workflow', {}).get('required_tools', []))}")
            print(f"Duration: {result.get('workflow', {}).get('estimated_duration_minutes')} minutes")
            print(f"Difficulty: {result.get('workflow', {}).get('difficulty')}")
            return True
        else:
            error = response.json()
            print(f"✗ Request failed: {error.get('error')}")
            print(f"  Message: {error.get('message')}")
            if error.get('details'):
                print(f"  Details: {error.get('details')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Is the server running?")
        return False
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("FastAPI /plan_workflow Endpoint Test")
    print("=" * 60)
    
    # Test health check
    if not test_health_check():
        sys.exit(1)
    
    # Test workflow planning
    if not test_plan_workflow():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()


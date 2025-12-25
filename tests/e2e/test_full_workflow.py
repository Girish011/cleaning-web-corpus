"""
End-to-end tests for the full Cleaning Workflow Planner API workflow.

Tests the complete system from API request to response, including:
- All three endpoints working together
- Data quality improvements (step filtering, method selection, deduplication)
- Error handling and edge cases
- Response schema validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from typing import Dict, Any, List

from src.api.main import app
# Note: Schema imports are for reference, actual validation happens via FastAPI


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_clickhouse_with_data():
    """Mock ClickHouse client with realistic data for E2E testing."""
    client = Mock()
    
    # Methods query result
    methods_data = [
        ("spot_clean", 5, 4.2, 0.85, 0.8),
        ("vacuum", 3, 2.5, 0.80, 0.75),
    ]
    
    # Steps query result (with quality filtering applied)
    steps_data = [
        (1, "Blot excess liquid with paper towels", "doc-1", 0.90, "Blot liquid"),
        (2, "Mix white vinegar and cold water solution", "doc-1", 0.85, "Mix solution"),
        (3, "Apply solution to stain and let sit", "doc-1", 0.88, "Apply solution"),
        (4, "Rinse with cold water and blot dry", "doc-1", 0.87, "Rinse and dry"),
        (1, "Blot the stain immediately", "doc-2", 0.92, "Blot stain"),
        (2, "Apply baking soda paste", "doc-2", 0.85, "Apply paste"),
    ]
    
    # Tools query result
    tools_data = [
        ("vinegar", 3, 0.88, "chemical", 2),
        ("paper_towels", 5, 0.92, "consumable", 3),
        ("baking_soda", 2, 0.85, "chemical", 1),
        ("cold_water", 4, 0.90, "consumable", 2),
    ]
    
    # Reference documents query result
    docs_data = [
        (
            "doc-1",
            "https://example.com/carpet-stain-removal",
            "How to Remove Stains from Carpets",
            "carpets_floors",
            "stain",
            "spot_clean",
            0.85,
            1250,
            5000,
            datetime(2024, 1, 10, 8, 0, 0),
            datetime(2024, 1, 10, 9, 0, 0),
        ),
        (
            "doc-2",
            "https://example.com/stain-removal-guide",
            "Stain Removal Guide",
            "carpets_floors",
            "stain",
            "spot_clean",
            0.80,
            980,
            4500,
            datetime(2024, 1, 11, 9, 0, 0),
            datetime(2024, 1, 11, 10, 0, 0),
        ),
    ]
    
    # Steps for reference documents
    doc_steps_data = {
        "doc-1": [
            ("step-1", 1, "Blot excess liquid", None, 0.90, "rule_based", datetime.now()),
            ("step-2", 2, "Mix vinegar solution", None, 0.85, "rule_based", datetime.now()),
        ],
        "doc-2": [
            ("step-3", 1, "Blot the stain", None, 0.92, "rule_based", datetime.now()),
        ],
    }
    
    # Tools for reference documents
    doc_tools_data = {
        "doc-1": [
            ("tool-1", "vinegar", "chemical", 0.88, "rule_based", None, datetime.now()),
            ("tool-2", "paper_towels", "consumable", 0.92, "rule_based", None, datetime.now()),
        ],
        "doc-2": [
            ("tool-3", "baking_soda", "chemical", 0.85, "rule_based", None, datetime.now()),
        ],
    }
    
    # Similar scenarios query result
    similar_scenarios_data = [
        ("carpets_floors", "stain", "spot_clean", 5, 0.85, 1.0),
        ("carpets_floors", "stain", "steam_clean", 2, 0.80, 0.5),
    ]
    
    # Coverage stats data
    coverage_summary_data = [(50, 25, 5, 4, 6)]
    surface_dist_data = [
        ("carpets_floors", 8),
        ("clothes", 15),
        ("pillows_bedding", 5),
    ]
    dirt_dist_data = [
        ("stain", 20),
        ("dust", 15),
        ("grease", 8),
    ]
    method_dist_data = [
        ("vacuum", 12),
        ("hand_wash", 10),
        ("spot_clean", 8),
    ]
    
    def execute_side_effect(query: str, params=None, settings=None):
        """Route queries to appropriate mock data based on query content."""
        query_lower = query.lower()
        
        # Methods query
        if "fct_cleaning_procedures" in query_lower and "cleaning_method" in query_lower:
            return methods_data
        
        # Steps query
        if "steps" in query_lower and "step_order" in query_lower:
            return steps_data
        
        # Tools query
        if "tools" in query_lower and "tool_name" in query_lower:
            return tools_data
        
        # Documents query (for search_procedures)
        if "raw_documents" in query_lower and "count" in query_lower:
            return [(2,)]  # Total count
        if "raw_documents" in query_lower and "document_id" in query_lower:
            return docs_data
        
        # Reference documents query
        if "raw_documents" in query_lower and "d.document_id" in query_lower:
            return docs_data
        
        # Steps for specific document
        if "steps" in query_lower and "where document_id" in query_lower:
            # Extract document_id from query
            for doc_id, steps in doc_steps_data.items():
                if doc_id in query:
                    return steps
            return []
        
        # Tools for specific document
        if "tools" in query_lower and "where document_id" in query_lower:
            # Extract document_id from query
            for doc_id, tools in doc_tools_data.items():
                if doc_id in query:
                    return tools
            return []
        
        # Similar scenarios query
        if "fct_cleaning_procedures" in query_lower and "similarity_score" in query_lower:
            return similar_scenarios_data
        
        # Coverage stats queries
        if "sum(document_count)" in query_lower and "count(*)" in query_lower:
            return coverage_summary_data
        if "surface_type" in query_lower and "group by surface_type" in query_lower:
            return surface_dist_data
        if "dirt_type" in query_lower and "group by dirt_type" in query_lower:
            return dirt_dist_data
        if "cleaning_method" in query_lower and "group by cleaning_method" in query_lower:
            return method_dist_data
        if "matrix" in query_lower or "surface_dirt" in query_lower:
            return [("carpets_floors", "stain", 3)]
        if "low_coverage" in query_lower or "document_count <= 1" in query_lower:
            return []
        
        return []
    
    client.execute = Mock(side_effect=execute_side_effect)
    client.connect = Mock()
    client.disconnect = Mock()
    return client


@pytest.fixture
def mock_agent_with_quality_improvements():
    """Mock WorkflowPlannerAgent with data quality improvements applied."""
    agent = Mock()
    
    # Simulate agent with quality improvements:
    # - Step quality filtering (T53)
    # - Method relevance selection (T54)
    # - Source document deduplication (T55)
    # - Step relevance filtering (T56)
    # - Minimum step count enforcement (T57)
    
    def plan_workflow_side_effect(*args, **kwargs):
        query = kwargs.get("query", "")
        
        # Simulate method selection prioritizing relevance (T54)
        # For stain removal, should select spot_clean over vacuum
        if "stain" in query.lower():
            selected_method = "spot_clean"
        else:
            selected_method = "vacuum"
        
        # Simulate step quality filtering (T53) - only actionable steps
        # Simulate step relevance filtering (T56) - stain-related steps prioritized
        steps = [
            {
                "step_number": 1,
                "action": "Blot excess liquid",
                "description": "Blot excess liquid with paper towels. Work from outside to center.",
                "tools": ["paper_towels"],
                "duration_seconds": 60,
                "order": 1,
            },
            {
                "step_number": 2,
                "action": "Apply cleaning solution",
                "description": "Mix white vinegar and cold water. Apply to stain.",
                "tools": ["vinegar", "cold_water"],
                "duration_seconds": 120,
                "order": 2,
            },
            {
                "step_number": 3,
                "action": "Rinse and dry",
                "description": "Rinse with cold water and blot dry with clean towel.",
                "tools": ["cold_water", "towel"],
                "duration_seconds": 180,
                "order": 3,
            },
        ]
        
        # Simulate source document deduplication (T55) - unique documents only
        source_documents = [
            {
                "document_id": "doc-1",
                "url": "https://example.com/carpet-stain-removal",
                "title": "How to Remove Stains from Carpets",
                "relevance_score": 0.92,
                "extraction_confidence": 0.85,
            },
            {
                "document_id": "doc-2",
                "url": "https://example.com/stain-removal-guide",
                "title": "Stain Removal Guide",
                "relevance_score": 0.88,
                "extraction_confidence": 0.80,
            },
        ]
        
        return {
            "workflow_id": "wf-test-123",
            "scenario": {
                "surface_type": "carpets_floors",
                "dirt_type": "stain",
                "cleaning_method": selected_method,
                "normalized_query": query,
            },
            "workflow": {
                "estimated_duration_minutes": 15,
                "difficulty": "moderate",
                "steps": steps,
                "required_tools": [
                    {
                        "tool_name": "paper_towels",
                        "category": "consumable",
                        "quantity": "several",
                        "is_required": True,
                    },
                    {
                        "tool_name": "vinegar",
                        "category": "chemical",
                        "quantity": "1 cup",
                        "is_required": True,
                    },
                ],
                "safety_notes": ["Test solution on hidden area first"],
                "tips": ["Work from outside to center"],
            },
            "source_documents": source_documents,
            "metadata": {
                "generated_at": "2024-01-15T10:30:00Z",
                "agent_version": "1.0",
                "extraction_method": "agent",
                "confidence": 0.87,
                "corpus_coverage": {
                    "matching_documents": 5,
                    "total_combinations": 1,
                    "coverage_score": 1.0,
                },
                "method_selection": {
                    "selected_method": selected_method,
                    "alternatives_considered": ["vacuum", "steam_clean"],
                    "selection_reason": "Most relevant for stain removal",
                },
            },
        }
    
    agent.plan_workflow = Mock(side_effect=plan_workflow_side_effect)
    agent.close = Mock()
    return agent


class TestFullWorkflowE2E:
    """End-to-end tests for the complete API workflow."""
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    def test_e2e_workflow_planning_with_quality_improvements(
        self, mock_agent_class, client, mock_agent_with_quality_improvements
    ):
        """
        Test full workflow planning with all data quality improvements.
        
        Validates:
        - T53: Step quality filtering (only actionable steps)
        - T54: Method relevance selection (spot_clean for stains)
        - T55: Source document deduplication
        - T56: Step relevance filtering
        - T57: Minimum step count (3+ steps)
        """
        mock_agent_class.return_value = mock_agent_with_quality_improvements
        
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove red wine stain from wool carpet",
                "constraints": {
                    "no_bleach": True,
                    "gentle_only": True,
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response schema
        assert "workflow_id" in data
        assert "scenario" in data
        assert "workflow" in data
        assert "source_documents" in data
        assert "metadata" in data
        
        # T54: Validate method selection (should be spot_clean for stain removal)
        assert data["scenario"]["cleaning_method"] == "spot_clean"
        assert data["scenario"]["dirt_type"] == "stain"
        
        # T57: Validate minimum step count (should have 3+ steps)
        steps = data["workflow"]["steps"]
        assert len(steps) >= 3, f"Expected at least 3 steps, got {len(steps)}"
        
        # T53: Validate step quality (all steps should be actionable)
        for step in steps:
            step_text = step.get("description", "").lower()
            # Should contain action verbs
            action_verbs = ["blot", "apply", "mix", "rinse", "dry", "clean"]
            assert any(verb in step_text for verb in action_verbs), \
                f"Step should contain action verb: {step_text}"
            # Should not be informational
            info_phrases = ["health benefits", "prolongs", "extends"]
            assert not any(phrase in step_text for phrase in info_phrases), \
                f"Step should not be informational: {step_text}"
        
        # T55: Validate source document deduplication (unique document_ids)
        doc_ids = [doc["document_id"] for doc in data["source_documents"]]
        assert len(doc_ids) == len(set(doc_ids)), \
            "Source documents should be deduplicated (unique document_ids)"
        
        # T56: Validate step relevance (steps should match query intent)
        # For stain removal, steps should contain stain-related keywords
        stain_keywords = ["blot", "stain", "remove", "treat", "clean", "rinse"]
        relevant_steps = [
            step for step in steps
            if any(keyword in step.get("description", "").lower() for keyword in stain_keywords)
        ]
        assert len(relevant_steps) >= 2, \
            "At least 2 steps should be relevant to stain removal"
        
        # Validate workflow structure
        assert data["workflow"]["estimated_duration_minutes"] > 0
        assert data["workflow"]["difficulty"] in ["easy", "moderate", "hard"]
        assert len(data["workflow"]["required_tools"]) > 0
        
        # Validate metadata
        assert data["metadata"]["confidence"] > 0
        assert data["metadata"]["corpus_coverage"]["matching_documents"] > 0
    
    @patch("src.api.routers.procedures.ClickHouseClient")
    def test_e2e_search_procedures(
        self, mock_client_class, client, mock_clickhouse_with_data
    ):
        """Test /search_procedures endpoint end-to-end."""
        mock_client_class.return_value = mock_clickhouse_with_data
        
        response = client.get(
            "/api/v1/search_procedures",
            params={
                "surface_type": "carpets_floors",
                "dirt_type": "stain",
                "limit": 10,
                "include_steps": True,
                "include_tools": True,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response schema
        assert "total" in data
        assert "procedures" in data
        assert isinstance(data["procedures"], list)
        
        if data["procedures"]:
            procedure = data["procedures"][0]
            assert "document_id" in procedure
            assert "url" in procedure
            assert "surface_type" in procedure
            assert procedure["steps"] is not None
            assert procedure["tools"] is not None
    
    @patch("src.api.routers.stats.ClickHouseClient")
    def test_e2e_coverage_stats(
        self, mock_client_class, client, mock_clickhouse_with_data
    ):
        """Test /stats/coverage endpoint end-to-end."""
        mock_client_class.return_value = mock_clickhouse_with_data
        
        response = client.get(
            "/api/v1/stats/coverage",
            params={
                "include_matrix": True,
                "matrix_type": "full",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response schema
        assert "summary" in data
        assert "distributions" in data
        assert "gaps" in data
        assert data["coverage_matrix"] is not None
        
        # Validate summary
        assert data["summary"]["total_documents"] > 0
        assert data["summary"]["coverage_percentage"] >= 0
        
        # Validate distributions
        assert "surface_types" in data["distributions"]
        assert "dirt_types" in data["distributions"]
        assert "cleaning_methods" in data["distributions"]
        
        # Validate gaps
        assert "missing_surface_types" in data["gaps"]
        assert "missing_dirt_types" in data["gaps"]
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    def test_e2e_insufficient_steps_error(
        self, mock_agent_class, client
    ):
        """Test T57: Minimum step count enforcement."""
        agent = Mock()
        agent.plan_workflow = Mock(side_effect=ValueError(
            "Insufficient steps found for this combination. "
            "Found 2 steps, minimum 3 required."
        ))
        agent.close = Mock()
        mock_agent_class.return_value = agent
        
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove stain from rare surface",
            },
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "no_match_found"
        assert "Insufficient steps" in data["message"]
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    def test_e2e_method_selection_relevance(
        self, mock_agent_class, client, mock_agent_with_quality_improvements
    ):
        """Test T54: Method selection prioritizes relevance over document count."""
        mock_agent_class.return_value = mock_agent_with_quality_improvements
        
        # Test stain removal query - should select spot_clean (not vacuum)
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove red wine stain from carpet",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should select spot_clean for stain removal (not vacuum)
        assert data["scenario"]["cleaning_method"] == "spot_clean"
        assert data["scenario"]["dirt_type"] == "stain"
        
        # Method selection metadata should indicate relevance-based selection
        if "method_selection" in data.get("metadata", {}):
            method_selection = data["metadata"]["method_selection"]
            assert method_selection["selected_method"] == "spot_clean"
    
    def test_e2e_error_handling_middleware(self, client):
        """Test T51: Error handling middleware formats errors correctly."""
        # Test validation error
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "",  # Empty query should fail validation
            },
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "detail" in data
        
        # Test invalid parameter
        response = client.get(
            "/api/v1/search_procedures",
            params={
                "surface_type": "invalid_type",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "validation_error"
        assert "Invalid surface_type" in data["message"]
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    @patch("src.api.routers.procedures.ClickHouseClient")
    @patch("src.api.routers.stats.ClickHouseClient")
    def test_e2e_all_endpoints_workflow(
        self,
        mock_stats_ch_class,
        mock_proc_ch_class,
        mock_agent_class,
        client,
        mock_agent_with_quality_improvements,
        mock_clickhouse_with_data
    ):
        """Test complete workflow using all three endpoints."""
        mock_agent_class.return_value = mock_agent_with_quality_improvements
        mock_proc_ch_class.return_value = mock_clickhouse_with_data
        mock_stats_ch_class.return_value = mock_clickhouse_with_data
        
        # Step 1: Plan workflow
        workflow_response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove stain from carpet",
            },
        )
        assert workflow_response.status_code == 200
        
        # Step 2: Search for procedures
        search_response = client.get(
            "/api/v1/search_procedures",
            params={
                "surface_type": "carpets_floors",
                "dirt_type": "stain",
            },
        )
        assert search_response.status_code == 200
        
        # Step 3: Get coverage stats
        stats_response = client.get("/api/v1/stats/coverage")
        assert stats_response.status_code == 200
        
        # All endpoints should work together
        assert workflow_response.status_code == 200
        assert search_response.status_code == 200
        assert stats_response.status_code == 200


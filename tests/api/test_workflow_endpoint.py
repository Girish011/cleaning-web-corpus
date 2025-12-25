"""
Integration tests for POST /plan_workflow endpoint.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_agent():
    """Mock WorkflowPlannerAgent."""
    agent = Mock()
    agent.plan_workflow = Mock(return_value={
        "workflow_id": "test-workflow-id",
        "scenario": {
            "surface_type": "carpets_floors",
            "dirt_type": "stain",
            "cleaning_method": "spot_clean",
            "normalized_query": "Remove stain from carpet",
        },
        "workflow": {
            "estimated_duration_minutes": 15,
            "difficulty": "moderate",
            "steps": [
                {
                    "step_number": 1,
                    "action": "Blot excess liquid",
                    "description": "Use paper towels to blot up as much liquid as possible",
                    "tools": ["paper_towels"],
                    "duration_seconds": 60,
                    "order": 1,
                }
            ],
            "required_tools": [
                {
                    "tool_name": "paper_towels",
                    "category": "consumable",
                    "quantity": "several",
                    "is_required": True,
                }
            ],
            "safety_notes": ["Test solution on hidden area first"],
            "tips": ["Work from outside to center"],
        },
        "source_documents": [
            {
                "document_id": "doc-123",
                "url": "https://example.com/carpet-stain",
                "title": "How to Remove Stains",
                "relevance_score": 0.9,
                "extraction_confidence": 0.85,
            }
        ],
        "metadata": {
            "generated_at": "2024-01-15T10:30:00Z",
            "agent_version": "1.0",
            "extraction_method": "llm",
            "confidence": 0.87,
            "corpus_coverage": {
                "matching_documents": 5,
                "total_combinations": 1,
                "coverage_score": 1.0,
            },
            "method_selection": {
                "selected_method": "spot_clean",
                "alternatives_considered": ["steam_clean"],
                "selection_reason": "Most documents",
            },
        },
    })
    agent.close = Mock()
    return agent


class TestPlanWorkflowEndpoint:
    """Tests for POST /plan_workflow endpoint."""
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    def test_plan_workflow_success(self, mock_agent_class, client, mock_agent):
        """Test successful workflow planning."""
        mock_agent_class.return_value = mock_agent
        
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove red wine stain from wool carpet",
                "constraints": {
                    "no_bleach": True,
                    "gentle_only": True,
                },
                "context": {
                    "location": "living_room",
                    "material": "wool",
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert data["scenario"]["surface_type"] == "carpets_floors"
        assert data["scenario"]["dirt_type"] == "stain"
        assert data["workflow"]["steps"][0]["step_number"] == 1
        assert len(data["source_documents"]) == 1
        mock_agent.plan_workflow.assert_called_once()
        mock_agent.close.assert_called_once()
    
    def test_plan_workflow_missing_query(self, client):
        """Test workflow planning with missing query."""
        response = client.post(
            "/api/v1/plan_workflow",
            json={},
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "error" in data or "detail" in data
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    def test_plan_workflow_no_match(self, mock_agent_class, client, mock_agent):
        """Test workflow planning when no match found."""
        mock_agent_class.return_value = mock_agent
        mock_agent.plan_workflow.side_effect = ValueError("No matching procedures found")
        
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove ink from outdoor surface",
            },
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "no_match_found"
        assert "request_id" in data
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    def test_plan_workflow_database_error(self, mock_agent_class, client, mock_agent):
        """Test workflow planning with database error."""
        mock_agent_class.return_value = mock_agent
        mock_agent.plan_workflow.side_effect = RuntimeError("Database connection failed")
        
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove stain from carpet",
            },
        )
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "service_unavailable"
        assert "request_id" in data
    
    @patch("src.api.routers.workflow.WorkflowPlannerAgent")
    def test_plan_workflow_internal_error(self, mock_agent_class, client, mock_agent):
        """Test workflow planning with internal error."""
        mock_agent_class.return_value = mock_agent
        mock_agent.plan_workflow.side_effect = Exception("Unexpected error")
        
        response = client.post(
            "/api/v1/plan_workflow",
            json={
                "query": "Remove stain from carpet",
            },
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "internal_error"
        assert "request_id" in data


"""
Integration tests for GET /search_procedures endpoint.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_clickhouse_client():
    """Mock ClickHouse client."""
    client = Mock()
    
    # Mock count query result
    client.execute = Mock(side_effect=[
        [(5,)],  # Total count
        [  # Documents query
            (
                "doc-1",
                "https://example.com/doc1",
                "Document 1",
                "carpets_floors",
                "stain",
                "spot_clean",
                0.85,
                "llm",
                datetime(2024, 1, 10, 8, 0, 0),
                1250,
            ),
            (
                "doc-2",
                "https://example.com/doc2",
                "Document 2",
                "carpets_floors",
                "stain",
                "spot_clean",
                0.80,
                "rule_based",
                datetime(2024, 1, 11, 9, 0, 0),
                980,
            ),
        ],
        [  # Steps query
            ("doc-1", 1, "Blot excess liquid", 0.90),
            ("doc-1", 2, "Apply cleaning solution", 0.85),
            ("doc-2", 1, "Blot the stain", 0.88),
        ],
        [  # Tools query
            ("doc-1", "vinegar", "chemical", 0.88),
            ("doc-1", "paper_towels", "consumable", 0.92),
            ("doc-2", "baking_soda", "chemical", 0.85),
        ],
    ])
    client.connect = Mock()
    client.disconnect = Mock()
    return client


class TestSearchProceduresEndpoint:
    """Tests for GET /search_procedures endpoint."""
    
    @patch("src.api.routers.procedures.ClickHouseClient")
    def test_search_procedures_success(self, mock_client_class, client, mock_clickhouse_client):
        """Test successful procedure search."""
        mock_client_class.return_value = mock_clickhouse_client
        
        response = client.get(
            "/api/v1/search_procedures",
            params={
                "surface_type": "carpets_floors",
                "dirt_type": "stain",
                "limit": 10,
                "min_confidence": 0.7,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "procedures" in data
        assert len(data["procedures"]) == 2
        assert data["procedures"][0]["document_id"] == "doc-1"
        assert data["procedures"][0]["surface_type"] == "carpets_floors"
        assert data["procedures"][0]["steps"] is not None
        assert len(data["procedures"][0]["steps"]) == 2
        assert data["procedures"][0]["tools"] is not None
        assert len(data["procedures"][0]["tools"]) == 2
    
    @patch("src.api.routers.procedures.ClickHouseClient")
    def test_search_procedures_without_steps_tools(self, mock_client_class, client, mock_clickhouse_client):
        """Test procedure search without steps and tools."""
        mock_client_class.return_value = mock_clickhouse_client
        
        response = client.get(
            "/api/v1/search_procedures",
            params={
                "surface_type": "carpets_floors",
                "include_steps": False,
                "include_tools": False,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["procedures"][0]["steps"] is None
        assert data["procedures"][0]["tools"] is None
    
    def test_search_procedures_invalid_surface_type(self, client):
        """Test procedure search with invalid surface type."""
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
    
    def test_search_procedures_invalid_limit(self, client):
        """Test procedure search with invalid limit."""
        response = client.get(
            "/api/v1/search_procedures",
            params={
                "limit": 200,  # Exceeds max of 100
            },
        )
        
        assert response.status_code == 422  # Validation error from Pydantic
    
    @patch("src.api.routers.procedures.ClickHouseClient")
    def test_search_procedures_database_error(self, mock_client_class, client, mock_clickhouse_client):
        """Test procedure search with database error."""
        mock_client_class.return_value = mock_clickhouse_client
        mock_clickhouse_client.execute.side_effect = ConnectionError("Database connection failed")
        
        response = client.get(
            "/api/v1/search_procedures",
            params={
                "surface_type": "carpets_floors",
            },
        )
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "service_unavailable"
    
    @patch("src.api.routers.procedures.ClickHouseClient")
    def test_search_procedures_pagination(self, mock_client_class, client, mock_clickhouse_client):
        """Test procedure search with pagination."""
        mock_client_class.return_value = mock_clickhouse_client
        
        response = client.get(
            "/api/v1/search_procedures",
            params={
                "limit": 1,
                "offset": 1,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1
        assert data["offset"] == 1
        assert len(data["procedures"]) <= 1


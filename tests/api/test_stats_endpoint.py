"""
Integration tests for GET /stats/coverage endpoint.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_clickhouse_client():
    """Mock ClickHouse client."""
    client = Mock()
    
    # Mock query results
    client.execute = Mock(side_effect=[
        [(50, 25, 5, 4, 6)],  # Summary: total_docs, combinations, surfaces, dirts, methods
        [  # Surface distribution
            ("carpets_floors", 8),
            ("clothes", 15),
            ("pillows_bedding", 5),
            ("upholstery", 12),
            ("hard_surfaces", 10),
        ],
        [  # Dirt distribution
            ("stain", 20),
            ("dust", 15),
            ("grease", 8),
            ("pet_hair", 7),
        ],
        [  # Method distribution
            ("vacuum", 12),
            ("hand_wash", 10),
            ("spot_clean", 8),
            ("steam_clean", 5),
            ("wipe", 10),
            ("scrub", 5),
        ],
        [  # Surface-dirt matrix
            ("carpets_floors", "stain", 3),
            ("carpets_floors", "dust", 2),
            ("clothes", "stain", 5),
        ],
        [  # Surface-method matrix
            ("carpets_floors", "spot_clean", 3),
            ("carpets_floors", "vacuum", 1),
            ("clothes", "hand_wash", 5),
        ],
        [  # Dirt-method matrix
            ("stain", "spot_clean", 3),
            ("stain", "hand_wash", 2),
            ("dust", "vacuum", 2),
        ],
        [  # Full matrix
            ("carpets_floors", "stain", "spot_clean", 3),
            ("carpets_floors", "stain", "vacuum", 1),
            ("carpets_floors", "dust", "vacuum", 2),
            ("clothes", "stain", "hand_wash", 5),
        ],
        [  # Low coverage combinations
            ("upholstery", "pet_hair", "vacuum", 1),
        ],
    ])
    client.connect = Mock()
    client.disconnect = Mock()
    return client


class TestCoverageStatsEndpoint:
    """Tests for GET /stats/coverage endpoint."""
    
    @patch("src.api.routers.stats.ClickHouseClient")
    def test_get_coverage_stats_success(self, mock_client_class, client, mock_clickhouse_client):
        """Test successful coverage stats retrieval."""
        mock_client_class.return_value = mock_clickhouse_client
        
        response = client.get("/api/v1/stats/coverage")
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "distributions" in data
        assert "gaps" in data
        assert data["summary"]["total_documents"] == 50
        assert data["summary"]["total_combinations"] == 25
        assert data["summary"]["coverage_percentage"] > 0
        assert "surface_types" in data["distributions"]
        assert "dirt_types" in data["distributions"]
        assert "cleaning_methods" in data["distributions"]
        assert "missing_surface_types" in data["gaps"]
        assert "missing_dirt_types" in data["gaps"]
        assert "missing_methods" in data["gaps"]
    
    @patch("src.api.routers.stats.ClickHouseClient")
    def test_get_coverage_stats_with_matrix(self, mock_client_class, client, mock_clickhouse_client):
        """Test coverage stats with matrix included."""
        mock_client_class.return_value = mock_clickhouse_client
        
        response = client.get(
            "/api/v1/stats/coverage",
            params={
                "include_matrix": True,
                "matrix_type": "full",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "coverage_matrix" in data
        assert data["coverage_matrix"] is not None
        assert data["coverage_matrix"]["type"] == "full"
        assert "matrix" in data["coverage_matrix"]
    
    @patch("src.api.routers.stats.ClickHouseClient")
    def test_get_coverage_stats_with_filters(self, mock_client_class, client, mock_clickhouse_client):
        """Test coverage stats with filters."""
        mock_client_class.return_value = mock_clickhouse_client
        
        response = client.get(
            "/api/v1/stats/coverage",
            params={
                "surface_type": "carpets_floors",
                "dirt_type": "stain",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_get_coverage_stats_invalid_matrix_type(self, client):
        """Test coverage stats with invalid matrix type."""
        response = client.get(
            "/api/v1/stats/coverage",
            params={
                "matrix_type": "invalid",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "validation_error"
        assert "Invalid matrix_type" in data["message"]
    
    def test_get_coverage_stats_invalid_surface_type(self, client):
        """Test coverage stats with invalid surface type."""
        response = client.get(
            "/api/v1/stats/coverage",
            params={
                "surface_type": "invalid",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "validation_error"
    
    @patch("src.api.routers.stats.ClickHouseClient")
    def test_get_coverage_stats_database_error(self, mock_client_class, client, mock_clickhouse_client):
        """Test coverage stats with database error."""
        mock_client_class.return_value = mock_clickhouse_client
        mock_clickhouse_client.execute.side_effect = ConnectionError("Database connection failed")
        
        response = client.get("/api/v1/stats/coverage")
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "service_unavailable"
    
    @patch("src.api.routers.stats.ClickHouseClient")
    def test_get_coverage_stats_surface_dirt_matrix(self, mock_client_class, client, mock_clickhouse_client):
        """Test coverage stats with surface_dirt matrix."""
        mock_client_class.return_value = mock_clickhouse_client
        
        response = client.get(
            "/api/v1/stats/coverage",
            params={
                "include_matrix": True,
                "matrix_type": "surface_dirt",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["coverage_matrix"]["type"] == "surface_dirt"
        assert "surface_dirt" in data["coverage_matrix"]["matrix"]


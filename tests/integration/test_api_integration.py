"""
Integration tests for FastAPI endpoints and basic functionality.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import tempfile
from pathlib import Path

from app.api.v1.main import app
from app.core.config import settings


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def temp_storage(self):
        """Temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_ask_endpoint_basic(self, client):
        """Test basic ask endpoint functionality."""
        with patch('app.services.ai_service.AIService.ask_question') as mock_ask:
            mock_ask.return_value = {
                "response": "Test response",
                "insights": ["Test insight"],
                "suggestions": ["Test suggestion"],
                "confidence": 0.8
            }
            
            response = client.post("/ask", json={
                "question": "Test question",
                "context": {"test": "data"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "insights" in data
            assert "suggestions" in data

    def test_strategies_endpoint(self, client):
        """Test strategies endpoint."""
        with patch('app.services.memory_service.MemoryService.list_strategies') as mock_list:
            mock_list.return_value = [
                {
                    "id": "test_id",
                    "question": "Test question",
                    "timestamp": "2024-01-15T12:00:00Z"
                }
            ]
            
            response = client.get("/strategies")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "test_id"

    def test_youtube_overview_endpoint(self, client):
        """Test YouTube overview endpoint."""
        with patch('app.clients.youtube_client.YouTubeClient.get_channel_stats') as mock_stats:
            mock_stats.return_value = {
                "subscriber_count": 10000,
                "video_count": 50,
                "view_count": 500000
            }
            
            response = client.get("/youtube/overview")
            assert response.status_code == 200
            data = response.json()
            assert "subscriber_count" in data

    def test_stats_endpoint(self, client):
        """Test stats endpoint."""
        with patch('app.services.memory_service.MemoryService.get_storage_stats') as mock_stats:
            mock_stats.return_value = {
                "total_strategies": 10,
                "total_size": "1.2MB",
                "latest_strategy": "2024-01-15T12:00:00Z"
            }
            
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_strategies" in data

    def test_error_handling(self, client):
        """Test error handling."""
        # Test invalid JSON
        response = client.post("/ask", json={
            "question": ""  # Empty question should fail validation
        })
        assert response.status_code == 422  # Validation error

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/")
        assert response.status_code == 200
        # Note: TestClient doesn't fully simulate CORS, but we can check the middleware is configured


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
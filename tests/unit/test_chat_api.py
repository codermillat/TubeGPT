"""
Comprehensive test suite for YouTube Analytics Chat API and CLI functionality.
Tests API endpoints, CLI commands, and integration with mocked Gemini responses.
"""

import pytest
import asyncio
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess
import sys

# FastAPI testing imports
from fastapi.testclient import TestClient
import httpx

# Import modules to test
try:
    from chat_api import app, ChatRequest, ChatResponse
    from main import main, run_cli_analysis, find_latest_csv
    CHAT_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import chat modules: {e}")
    CHAT_API_AVAILABLE = False

# Test configuration
TEST_DATA_DIR = Path("test_data")
SAMPLE_CSV = TEST_DATA_DIR / "sample_analytics.csv"
EMPTY_CSV = TEST_DATA_DIR / "empty_analytics.csv"
COMPARISON_CSV = TEST_DATA_DIR / "comparison_analytics.csv"

# Mock Gemini responses
MOCK_ENGLISH_RESPONSE = """Based on your YouTube analytics data, here are your top performing videos:

**Top Videos by Views:**
1. Food Challenge: 7 Dishes - 89,000 views (6.2% CTR)
2. Travel Vlog: Cox's Bazar - 67,000 views (5.8% CTR)  
3. Best Street Food in Dhaka - 45,000 views (4.5% CTR)

**Key Insights:**
• Food content performs exceptionally well (89K views average)
• Bangladesh audience shows highest engagement
• CTR above 5% indicates strong thumbnail/title performance

**Recommendations:**
• Create more food-related content
• Focus on Bangladesh-specific topics
• Maintain current thumbnail style for food videos"""

MOCK_BENGALI_RESPONSE = """আপনার YouTube অ্যানালিটিক্স ডেটার ভিত্তিতে, এখানে আপনার সেরা পারফরমিং ভিডিওগুলো:

**ভিউ অনুযায়ী টপ ভিডিও:**
১. খাবারের চ্যালেঞ্জ: ৭টি খাবার - ৮৯,০০০ ভিউ (৬.২% CTR)
২. ট্রাভেল ভ্লগ: কক্সবাজার - ৬৭,০০০ ভিউ (৫.৮% CTR)
৩. ঢাকার সেরা স্ট্রিট ফুড - ৪৫,০০০ ভিউ (৪.৫% CTR)

**মূল অন্তর্দৃষ্টি:**
• খাবারের কন্টেন্ট অসাধারণ ভাল পারফর্ম করে
• বাংলাদেশী দর্শকরা সবচেয়ে বেশি এনগেজড
• ৫% এর উপরে CTR ভাল থাম্বনেইল/টাইটেল নির্দেশ করে

**সুপারিশ:**
• আরো খাবার-সম্পর্কিত কন্টেন্ট তৈরি করুন
• বাংলাদেশ-নির্দিষ্ট বিষয়ে ফোকাস করুন
• খাবারের ভিডিওর জন্য বর্তমান থাম্বনেইল স্টাইল বজায় রাখুন"""

MOCK_ERROR_RESPONSE = "I apologize, but I encountered an error while analyzing your data. Please try again or rephrase your question."

class TestChatAPI:
    """Test suite for FastAPI chat endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        if not CHAT_API_AVAILABLE:
            pytest.skip("Chat API modules not available")
        return TestClient(app)
    
    @pytest.fixture
    def mock_gemini_analyzer(self):
        """Mock the Gemini analyzer to avoid API calls."""
        with patch('chat_api.GeminiYouTubeAnalyzer') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            mock_instance.analyze_youtube_data.return_value = MOCK_ENGLISH_RESPONSE
            yield mock_instance
    
    @pytest.fixture
    def mock_gemini_initialization(self):
        """Mock Gemini initialization."""
        with patch('chat_api.initialize_analyzer') as mock_init:
            mock_analyzer = Mock()
            mock_init.return_value = mock_analyzer
            yield mock_analyzer
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "gemini_analyzer" in data
        assert "api_key_configured" in data
        assert "active_sessions" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    @patch('chat_api.analyze_with_gemini')
    def test_chat_valid_request(self, mock_analyze, client):
        """Test POST /chat with valid message and CSV."""
        mock_analyze.return_value = MOCK_ENGLISH_RESPONSE
        
        request_data = {
            "message": "What are my best performing videos?",
            "csv_path": str(SAMPLE_CSV)
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "reply" in data
        assert "session_id" in data
        assert len(data["session_id"]) > 0
        
        # Verify mock was called
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        assert call_args[0][0] == request_data["message"]  # message
        assert call_args[0][1] == request_data["csv_path"]  # csv_path
    
    def test_chat_missing_csv(self, client):
        """Test POST /chat with non-existent CSV file."""
        request_data = {
            "message": "What are my best performing videos?",
            "csv_path": "nonexistent_file.csv"
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 404
        
        data = response.json()
        assert "CSV file not found" in data["detail"]
    
    def test_chat_empty_csv(self, client):
        """Test POST /chat with empty CSV file."""
        request_data = {
            "message": "What are my best performing videos?",
            "csv_path": str(EMPTY_CSV)
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "empty" in data["detail"].lower()
    
    @patch('chat_api.analyze_with_gemini')
    def test_chat_bengali_question(self, mock_analyze, client):
        """Test POST /chat with Bengali question."""
        mock_analyze.return_value = MOCK_BENGALI_RESPONSE
        
        request_data = {
            "message": "আমার সেরা পারফরমিং ভিডিওগুলো কোনগুলো?",
            "csv_path": str(SAMPLE_CSV)
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "reply" in data
        
        # Verify Bengali response
        assert "ভিডিও" in data["reply"] or "পারফর্ম" in data["reply"]
        
        # Verify mock was called with Bengali question
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        assert "আমার" in call_args[0][0]  # Bengali text in message
    
    @patch('chat_api.analyze_with_gemini')
    def test_chat_with_session_id(self, mock_analyze, client):
        """Test POST /chat with existing session ID."""
        mock_analyze.return_value = MOCK_ENGLISH_RESPONSE
        
        session_id = "test_session_123"
        request_data = {
            "message": "What are my best performing videos?",
            "csv_path": str(SAMPLE_CSV),
            "session_id": session_id
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["session_id"] == session_id
    
    @patch('chat_api.analyze_with_gemini')
    def test_chat_session_memory(self, mock_analyze, client):
        """Test that session memory works across multiple requests."""
        mock_analyze.return_value = MOCK_ENGLISH_RESPONSE
        
        session_id = "memory_test_session"
        
        # First request
        request1 = {
            "message": "What are my best videos?",
            "csv_path": str(SAMPLE_CSV),
            "session_id": session_id
        }
        
        response1 = client.post("/chat", json=request1)
        assert response1.status_code == 200
        
        # Second request (should have context from first)
        request2 = {
            "message": "Tell me more about the first one",
            "csv_path": str(SAMPLE_CSV),
            "session_id": session_id
        }
        
        response2 = client.post("/chat", json=request2)
        assert response2.status_code == 200
        
        # Verify both calls were made
        assert mock_analyze.call_count == 2
        
        # Second call should have context from first message
        second_call_args = mock_analyze.call_args_list[1]
        enhanced_message = second_call_args[0][0]  # First argument (message)
        assert "PREVIOUS CONVERSATION CONTEXT" in enhanced_message or len(enhanced_message) > len(request2["message"])
    
    def test_chat_invalid_request_format(self, client):
        """Test POST /chat with invalid request format."""
        # Missing required fields
        request_data = {
            "message": "What are my best videos?"
            # Missing csv_path
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_chat_empty_message(self, client):
        """Test POST /chat with empty message."""
        request_data = {
            "message": "",
            "csv_path": str(SAMPLE_CSV)
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('chat_api.analyze_with_gemini')
    def test_chat_gemini_error_handling(self, mock_analyze, client):
        """Test error handling when Gemini analysis fails."""
        mock_analyze.side_effect = Exception("Gemini API error")
        
        request_data = {
            "message": "What are my best performing videos?",
            "csv_path": str(SAMPLE_CSV)
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 200  # Should handle gracefully
        
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data["reply"].lower()


class TestCLIFunctionality:
    """Test suite for CLI functionality."""
    
    @pytest.fixture
    def temp_env_file(self):
        """Create temporary .env file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("GEMINI_API_KEY=test_api_key_12345\n")
            f.write("ENVIRONMENT=test\n")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_find_latest_csv(self):
        """Test CSV file discovery functionality."""
        # Should find our test CSV
        latest_csv = find_latest_csv(str(TEST_DATA_DIR))
        assert latest_csv is not None
        assert latest_csv.endswith('.csv')
        assert Path(latest_csv).exists()
    
    def test_find_latest_csv_no_files(self):
        """Test CSV discovery when no files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            latest_csv = find_latest_csv(temp_dir)
            assert latest_csv is None
    
    @patch('main.GeminiYouTubeAnalyzer')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'})
    def test_cli_analysis_with_message_only(self, mock_analyzer_class):
        """Test CLI call with --message only (auto CSV detection)."""
        # Setup mock
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_youtube_data.return_value = MOCK_ENGLISH_RESPONSE
        
        # Test the CLI analysis function directly
        with patch('main.find_latest_csv', return_value=str(SAMPLE_CSV)):
            with patch('builtins.print') as mock_print:
                run_cli_analysis("What are my best videos?")
                
                # Verify analyzer was called
                mock_analyzer.analyze_youtube_data.assert_called_once()
                call_args = mock_analyzer.analyze_youtube_data.call_args
                assert call_args[0][0] == "What are my best videos?"
                assert call_args[0][1] == str(SAMPLE_CSV)
                
                # Verify output was printed
                mock_print.assert_called()
                printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
                assert "ANALYSIS RESULTS" in printed_text
    
    @patch('main.GeminiYouTubeAnalyzer')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'})
    def test_cli_analysis_with_custom_csv(self, mock_analyzer_class):
        """Test CLI call with custom CSV path."""
        # Setup mock
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_youtube_data.return_value = MOCK_ENGLISH_RESPONSE
        
        custom_csv_path = str(COMPARISON_CSV)
        
        # Test the CLI analysis function directly
        with patch('builtins.print') as mock_print:
            run_cli_analysis("How did my performance change?", custom_csv_path)
            
            # Verify analyzer was called with custom CSV
            mock_analyzer.analyze_youtube_data.assert_called_once()
            call_args = mock_analyzer.analyze_youtube_data.call_args
            assert call_args[0][1] == custom_csv_path
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': ''})
    def test_cli_missing_api_key(self):
        """Test CLI behavior when API key is missing."""
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                run_cli_analysis("Test message")
                
                # Should exit with error
                mock_exit.assert_called_with(1)
                
                # Should print error message
                printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
                assert "GEMINI_API_KEY not found" in printed_text
    
    def test_cli_missing_csv_file(self):
        """Test CLI behavior when CSV file is missing."""
        with patch('main.find_latest_csv', return_value=None):
            with patch('builtins.print') as mock_print:
                with patch('sys.exit') as mock_exit:
                    run_cli_analysis("Test message")
                    
                    # Should exit with error
                    mock_exit.assert_called_with(1)
                    
                    # Should print helpful message
                    printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
                    assert "No YouTube analytics CSV file found" in printed_text
    
    @patch('main.GeminiYouTubeAnalyzer')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'})
    def test_cli_bengali_question(self, mock_analyzer_class):
        """Test CLI with Bengali question."""
        # Setup mock
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_youtube_data.return_value = MOCK_BENGALI_RESPONSE
        
        bengali_question = "আমার সেরা ভিডিওগুলো কোনগুলো?"
        
        with patch('main.find_latest_csv', return_value=str(SAMPLE_CSV)):
            with patch('builtins.print') as mock_print:
                run_cli_analysis(bengali_question)
                
                # Verify Bengali question was passed
                mock_analyzer.analyze_youtube_data.assert_called_once()
                call_args = mock_analyzer.analyze_youtube_data.call_args
                assert call_args[0][0] == bengali_question
                
                # Verify Bengali response was printed
                printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
                assert "ভিডিও" in printed_text or "ANALYSIS RESULTS" in printed_text


class TestIntegration:
    """Integration tests combining multiple components."""
    
    @patch('chat_api.analyze_with_gemini')
    def test_api_cli_consistency(self, mock_analyze):
        """Test that API and CLI produce consistent results."""
        if not CHAT_API_AVAILABLE:
            pytest.skip("Chat API modules not available")
            
        mock_analyze.return_value = MOCK_ENGLISH_RESPONSE
        
        # Test API
        client = TestClient(app)
        api_request = {
            "message": "What are my best performing videos?",
            "csv_path": str(SAMPLE_CSV)
        }
        
        api_response = client.post("/chat", json=api_request)
        assert api_response.status_code == 200
        api_data = api_response.json()
        
        # Test CLI (mock the analyzer to return same response)
        with patch('main.GeminiYouTubeAnalyzer') as mock_cli_analyzer:
            mock_cli_instance = Mock()
            mock_cli_analyzer.return_value = mock_cli_instance
            mock_cli_instance.analyze_youtube_data.return_value = MOCK_ENGLISH_RESPONSE
            
            with patch('builtins.print') as mock_print:
                with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
                    run_cli_analysis(api_request["message"], api_request["csv_path"])
            
            # Both should call the analyzer with same parameters
            assert mock_analyze.called
            assert mock_cli_instance.analyze_youtube_data.called
    
    def test_session_memory_persistence(self):
        """Test that session memory persists across multiple API calls."""
        if not CHAT_API_AVAILABLE:
            pytest.skip("Chat API modules not available")
            
        client = TestClient(app)
        session_id = "integration_test_session"
        
        with patch('chat_api.analyze_with_gemini') as mock_analyze:
            mock_analyze.return_value = MOCK_ENGLISH_RESPONSE
            
            # First request
            response1 = client.post("/chat", json={
                "message": "What are my top videos?",
                "csv_path": str(SAMPLE_CSV),
                "session_id": session_id
            })
            
            # Second request
            response2 = client.post("/chat", json={
                "message": "Tell me more about the first one",
                "csv_path": str(SAMPLE_CSV),
                "session_id": session_id
            })
            
            # Both should succeed
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            # Second call should have context
            assert mock_analyze.call_count == 2
            second_call_message = mock_analyze.call_args_list[1][0][0]
            assert len(second_call_message) > len("Tell me more about the first one")


# Test fixtures and utilities
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running tests."""
    # Ensure test data directory exists
    TEST_DATA_DIR.mkdir(exist_ok=True)
    
    # Set test environment variables
    os.environ['ENVIRONMENT'] = 'test'
    
    yield
    
    # Cleanup after tests
    # Note: We keep test data files for reuse


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    test_env = {
        'GEMINI_API_KEY': 'test_gemini_key_12345',
        'ENVIRONMENT': 'test'
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env


# Utility functions for tests
def create_test_csv(path: Path, data: list):
    """Create a test CSV file with given data."""
    import csv
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
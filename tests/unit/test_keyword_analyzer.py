"""
Unit tests for keyword_analyzer.py module.

Tests all major functions with mocked API responses to avoid
hitting real APIs during testing.
"""

import pytest
import pandas as pd
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from pytrends.exceptions import TooManyRequestsError, ResponseError

# Import the module to test
from keyword_analyzer import (
    get_youtube_autocomplete,
    get_google_trends,
    analyze_keywords,
    _parse_youtube_autocomplete_response,
    _generate_analysis_summary,
    KeywordAnalyzer
)

# Mock data for testing
MOCK_YOUTUBE_XML_RESPONSE = '''<?xml version="1.0"?>
<toplevel>
    <CompleteSuggestion>
        <suggestion data="cooking recipes"/>
    </CompleteSuggestion>
    <CompleteSuggestion>
        <suggestion data="cooking tips"/>
    </CompleteSuggestion>
    <CompleteSuggestion>
        <suggestion data="cooking channel"/>
    </CompleteSuggestion>
    <CompleteSuggestion>
        <suggestion data="cooking show"/>
    </CompleteSuggestion>
    <CompleteSuggestion>
        <suggestion data="cooking tutorial"/>
    </CompleteSuggestion>
</toplevel>'''

MOCK_TRENDS_DATA = {
    'cooking': {
        'interest_over_time': pd.DataFrame({
            'cooking': [45, 50, 55, 60, 65],
            'isPartial': [False, False, False, False, True]
        }),
        'related_queries': {
            'top': pd.DataFrame({
                'query': ['cooking recipes', 'cooking tips', 'cooking methods'],
                'value': [100, 80, 60]
            }),
            'rising': pd.DataFrame({
                'query': ['air fryer cooking', 'healthy cooking', 'quick cooking'],
                'value': [200, 150, 120]
            })
        }
    }
}

class TestYouTubeAutocomplete:
    """Test YouTube autocomplete functionality."""
    
    def test_get_youtube_autocomplete_success(self):
        """Test successful YouTube autocomplete request."""
        with patch('keyword_analyzer.KeywordAnalyzer') as mock_analyzer_class:
            # Setup mock
            mock_analyzer = Mock()
            mock_analyzer.retries = 3
            mock_analyzer.timeout = 30
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_response = Mock()
            mock_response.text = MOCK_YOUTUBE_XML_RESPONSE
            mock_response.raise_for_status.return_value = None
            
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_analyzer.session = mock_session
            
            # Test the function
            result = get_youtube_autocomplete("cooking", "US")
            
            # Assertions
            assert isinstance(result, list)
            assert len(result) <= 10
            assert "cooking recipes" in result
            assert "cooking tips" in result
            
            # Verify API call
            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            assert 'suggestqueries.google.com' in call_args[0][0]
    
    def test_get_youtube_autocomplete_empty_seed(self):
        """Test YouTube autocomplete with empty seed."""
        with pytest.raises(ValueError, match="Seed keyword cannot be empty"):
            get_youtube_autocomplete("", "US")
        
        with pytest.raises(ValueError, match="Seed keyword cannot be empty"):
            get_youtube_autocomplete("   ", "US")
    
    def test_get_youtube_autocomplete_request_failure(self):
        """Test YouTube autocomplete with request failure."""
        with patch('keyword_analyzer.KeywordAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.retries = 2
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_session = Mock()
            mock_session.get.side_effect = requests.RequestException("Network error")
            mock_analyzer.session = mock_session
            
            with pytest.raises(requests.RequestException):
                get_youtube_autocomplete("cooking", "US")
    
    def test_parse_youtube_autocomplete_response(self):
        """Test parsing of YouTube autocomplete XML response."""
        suggestions = _parse_youtube_autocomplete_response(MOCK_YOUTUBE_XML_RESPONSE)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 5
        assert "cooking recipes" in suggestions
        assert "cooking tips" in suggestions
        assert "cooking channel" in suggestions
    
    def test_parse_youtube_autocomplete_malformed_xml(self):
        """Test parsing with malformed XML (fallback to regex)."""
        malformed_xml = 'data="cooking recipes" data="cooking tips" invalid xml'
        
        suggestions = _parse_youtube_autocomplete_response(malformed_xml)
        
        assert isinstance(suggestions, list)
        assert "cooking recipes" in suggestions
        assert "cooking tips" in suggestions


class TestGoogleTrends:
    """Test Google Trends functionality."""
    
    @patch('keyword_analyzer.TrendReq')
    def test_get_google_trends_success(self, mock_trend_req):
        """Test successful Google Trends request."""
        # Setup mock pytrends
        mock_pytrends = Mock()
        mock_trend_req.return_value = mock_pytrends
        
        # Mock interest over time data
        interest_df = pd.DataFrame({
            'cooking': [45, 50, 55, 60, 65],
            'recipes': [40, 45, 50, 55, 60],
            'isPartial': [False, False, False, False, True]
        })
        mock_pytrends.interest_over_time.return_value = interest_df
        
        # Mock related queries
        mock_pytrends.related_queries.return_value = {
            'cooking': {
                'top': pd.DataFrame({
                    'query': ['cooking recipes', 'cooking tips'],
                    'value': [100, 80]
                }),
                'rising': pd.DataFrame({
                    'query': ['air fryer cooking', 'healthy cooking'],
                    'value': [200, 150]
                })
            },
            'recipes': {
                'top': pd.DataFrame({
                    'query': ['easy recipes', 'quick recipes'],
                    'value': [90, 70]
                }),
                'rising': pd.DataFrame({
                    'query': ['keto recipes', 'vegan recipes'],
                    'value': [180, 140]
                })
            }
        }
        
        # Test the function
        result = get_google_trends(['cooking', 'recipes'], 'today 3-m', 'US')
        
        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'keyword' in result.columns
        assert 'avg_interest' in result.columns
        assert 'peak_interest' in result.columns
        assert 'related_queries' in result.columns
        assert 'rising_terms' in result.columns
        
        # Check data values
        cooking_row = result[result['keyword'] == 'cooking'].iloc[0]
        assert cooking_row['avg_interest'] == 55.0  # Average of [45,50,55,60,65]
        assert cooking_row['peak_interest'] == 65
        assert 'cooking recipes' in cooking_row['related_queries']
        assert 'air fryer cooking' in cooking_row['rising_terms']
    
    def test_get_google_trends_empty_keywords(self):
        """Test Google Trends with empty keywords list."""
        with pytest.raises(ValueError, match="Keywords list cannot be empty"):
            get_google_trends([])
    
    def test_get_google_trends_too_many_keywords(self):
        """Test Google Trends with more than 5 keywords."""
        keywords = ['kw1', 'kw2', 'kw3', 'kw4', 'kw5', 'kw6', 'kw7']
        
        with patch('keyword_analyzer.TrendReq') as mock_trend_req:
            mock_pytrends = Mock()
            mock_trend_req.return_value = mock_pytrends
            
            # Mock empty response
            mock_pytrends.interest_over_time.return_value = pd.DataFrame()
            
            result = get_google_trends(keywords, 'today 3-m', 'US')
            
            # Should only process first 5 keywords
            assert len(result) == 5
            assert all(result['keyword'].isin(keywords[:5]))
    
    @patch('keyword_analyzer.TrendReq')
    def test_get_google_trends_rate_limit(self, mock_trend_req):
        """Test Google Trends rate limit handling."""
        mock_pytrends = Mock()
        mock_trend_req.return_value = mock_pytrends
        
        # First call raises rate limit error, second succeeds
        mock_pytrends.build_payload.side_effect = [
            TooManyRequestsError("Rate limit exceeded"),
            None
        ]
        
        # Mock successful response on retry
        interest_df = pd.DataFrame({
            'cooking': [50, 55, 60],
            'isPartial': [False, False, True]
        })
        mock_pytrends.interest_over_time.return_value = interest_df
        mock_pytrends.related_queries.return_value = {'cooking': {'top': None, 'rising': None}}
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = get_google_trends(['cooking'], 'today 3-m', 'US')
            
            assert len(result) == 1
            assert result.iloc[0]['keyword'] == 'cooking'
    
    @patch('keyword_analyzer.TrendReq')
    def test_get_google_trends_no_data(self, mock_trend_req):
        """Test Google Trends with no data returned."""
        mock_pytrends = Mock()
        mock_trend_req.return_value = mock_pytrends
        
        # Mock empty response
        mock_pytrends.interest_over_time.return_value = pd.DataFrame()
        
        result = get_google_trends(['obscure_keyword'], 'today 3-m', 'US')
        
        assert len(result) == 1
        assert result.iloc[0]['keyword'] == 'obscure_keyword'
        assert result.iloc[0]['avg_interest'] == 0
        assert result.iloc[0]['peak_interest'] == 0
        assert result.iloc[0]['related_queries'] == []
        assert result.iloc[0]['rising_terms'] == []


class TestAnalyzeKeywords:
    """Test the main analyze_keywords function."""
    
    @patch('keyword_analyzer.get_google_trends')
    @patch('keyword_analyzer.get_youtube_autocomplete')
    def test_analyze_keywords_success(self, mock_autocomplete, mock_trends):
        """Test successful keyword analysis."""
        # Mock autocomplete response
        mock_autocomplete.return_value = [
            'cooking recipes', 'cooking tips', 'cooking channel'
        ]
        
        # Mock trends response
        trends_df = pd.DataFrame([
            {
                'keyword': 'cooking',
                'avg_interest': 55.0,
                'peak_interest': 65,
                'related_queries': ['cooking recipes', 'cooking tips'],
                'rising_terms': ['air fryer cooking', 'healthy cooking']
            },
            {
                'keyword': 'cooking recipes',
                'avg_interest': 45.0,
                'peak_interest': 55,
                'related_queries': ['easy recipes', 'quick recipes'],
                'rising_terms': ['keto recipes', 'vegan recipes']
            }
        ])
        mock_trends.return_value = trends_df
        
        # Test the function
        result = analyze_keywords('cooking', 'US', 'today 3-m')
        
        # Assertions
        assert isinstance(result, dict)
        assert result['seed_keyword'] == 'cooking'
        assert result['region'] == 'US'
        assert result['timeframe'] == 'today 3-m'
        assert 'timestamp' in result
        
        # Check autocomplete results
        assert len(result['autocomplete']) == 3
        assert 'cooking recipes' in result['autocomplete']
        
        # Check trends results
        assert len(result['trends']) == 2
        assert 'cooking' in result['trends']
        assert result['trends']['cooking']['avg_interest'] == 55.0
        
        # Check summary
        assert 'summary' in result
        assert 'highest_interest' in result['summary']
        assert 'top_trending' in result['summary']
        
        # Verify function calls
        mock_autocomplete.assert_called_once_with('cooking', 'US')
        mock_trends.assert_called_once()
    
    def test_analyze_keywords_empty_seed(self):
        """Test analyze_keywords with empty seed."""
        with pytest.raises(ValueError, match="Seed keyword cannot be empty"):
            analyze_keywords('', 'US')
    
    @patch('keyword_analyzer.get_google_trends')
    @patch('keyword_analyzer.get_youtube_autocomplete')
    def test_analyze_keywords_partial_failure(self, mock_autocomplete, mock_trends):
        """Test analyze_keywords when one data source fails."""
        # Mock autocomplete failure
        mock_autocomplete.side_effect = Exception("Autocomplete API error")
        
        # Mock successful trends
        trends_df = pd.DataFrame([{
            'keyword': 'cooking',
            'avg_interest': 55.0,
            'peak_interest': 65,
            'related_queries': ['cooking recipes'],
            'rising_terms': ['air fryer cooking']
        }])
        mock_trends.return_value = trends_df
        
        result = analyze_keywords('cooking', 'US', 'today 3-m')
        
        # Should still return results with error logged
        assert isinstance(result, dict)
        assert len(result['errors']) == 1
        assert 'Autocomplete API error' in result['errors'][0]
        assert len(result['autocomplete']) == 0
        assert len(result['trends']) == 1
    
    @patch('keyword_analyzer.get_google_trends')
    @patch('keyword_analyzer.get_youtube_autocomplete')
    def test_analyze_keywords_complete_failure(self, mock_autocomplete, mock_trends):
        """Test analyze_keywords when both data sources fail."""
        mock_autocomplete.side_effect = Exception("Autocomplete failed")
        mock_trends.side_effect = Exception("Trends failed")
        
        with pytest.raises(Exception, match="Failed to fetch both autocomplete and trends data"):
            analyze_keywords('cooking', 'US', 'today 3-m')


class TestAnalysisSummary:
    """Test analysis summary generation."""
    
    def test_generate_analysis_summary(self):
        """Test summary generation with complete data."""
        analysis_results = {
            'autocomplete': ['cooking recipes', 'cooking tips', 'cooking channel'],
            'trends': {
                'cooking': {
                    'avg_interest': 55.0,
                    'peak_interest': 65,
                    'related_queries': ['cooking recipes', 'cooking tips'],
                    'rising_terms': ['air fryer cooking', 'healthy cooking']
                },
                'cooking recipes': {
                    'avg_interest': 45.0,
                    'peak_interest': 55,
                    'related_queries': ['easy recipes'],
                    'rising_terms': ['keto recipes']
                }
            }
        }
        
        summary = _generate_analysis_summary(analysis_results)
        
        assert summary['total_suggestions'] == 3
        assert summary['total_keywords_analyzed'] == 2
        assert summary['highest_interest']['keyword'] == 'cooking'
        assert summary['highest_interest']['avg_interest'] == 55.0
        assert summary['top_trending']['keyword'] == 'cooking'
        assert summary['top_trending']['peak_interest'] == 65
        assert len(summary['content_recommendations']) > 0
    
    def test_generate_analysis_summary_empty_data(self):
        """Test summary generation with empty data."""
        analysis_results = {
            'autocomplete': [],
            'trends': {}
        }
        
        summary = _generate_analysis_summary(analysis_results)
        
        assert summary['total_suggestions'] == 0
        assert summary['total_keywords_analyzed'] == 0
        assert summary['highest_interest'] is None
        assert summary['top_trending'] is None
        assert len(summary['best_opportunities']) == 0


class TestKeywordAnalyzerClass:
    """Test the KeywordAnalyzer class."""
    
    def test_keyword_analyzer_initialization(self):
        """Test KeywordAnalyzer initialization."""
        analyzer = KeywordAnalyzer(timeout=60, retries=5)
        
        assert analyzer.timeout == 60
        assert analyzer.retries == 5
        assert analyzer.session is not None
        assert 'User-Agent' in analyzer.session.headers
    
    def test_keyword_analyzer_default_values(self):
        """Test KeywordAnalyzer with default values."""
        analyzer = KeywordAnalyzer()
        
        assert analyzer.timeout == 30
        assert analyzer.retries == 3


# Integration tests
class TestIntegration:
    """Integration tests with mocked external APIs."""
    
    @patch('keyword_analyzer.get_google_trends')
    @patch('keyword_analyzer.get_youtube_autocomplete')
    def test_full_workflow(self, mock_autocomplete, mock_trends):
        """Test complete workflow from seed to analysis."""
        # Setup mocks
        mock_autocomplete.return_value = [
            'cooking recipes', 'cooking tips', 'cooking tutorial'
        ]
        
        trends_df = pd.DataFrame([
            {
                'keyword': 'cooking',
                'avg_interest': 60.0,
                'peak_interest': 75,
                'related_queries': ['cooking recipes', 'cooking methods'],
                'rising_terms': ['air fryer cooking', 'instant pot cooking']
            }
        ])
        mock_trends.return_value = trends_df
        
        # Run analysis
        result = analyze_keywords('cooking', 'BD', 'today 6-m')
        
        # Comprehensive checks
        assert result['seed_keyword'] == 'cooking'
        assert result['region'] == 'BD'
        assert result['timeframe'] == 'today 6-m'
        assert len(result['autocomplete']) == 3
        assert len(result['trends']) == 1
        assert len(result['errors']) == 0
        
        # Check that trends was called with correct parameters
        trends_call_args = mock_trends.call_args
        assert 'cooking' in trends_call_args[0][0]  # First argument (keywords list)
        assert trends_call_args[0][1] == 'today 6-m'  # Second argument (timeframe)
        assert trends_call_args[0][2] == 'BD'  # Third argument (geo)


# Fixtures for test data
@pytest.fixture
def sample_analysis_results():
    """Sample analysis results for testing."""
    return {
        'seed_keyword': 'cooking',
        'region': 'US',
        'timeframe': 'today 3-m',
        'timestamp': '2024-01-15T10:30:00',
        'autocomplete': ['cooking recipes', 'cooking tips', 'cooking channel'],
        'trends': {
            'cooking': {
                'avg_interest': 55.0,
                'peak_interest': 65,
                'related_queries': ['cooking recipes', 'cooking tips'],
                'rising_terms': ['air fryer cooking', 'healthy cooking']
            }
        },
        'summary': {
            'total_suggestions': 3,
            'total_keywords_analyzed': 1,
            'highest_interest': {'keyword': 'cooking', 'avg_interest': 55.0}
        },
        'errors': []
    }


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
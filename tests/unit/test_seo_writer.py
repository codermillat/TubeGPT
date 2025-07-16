"""
Unit tests for seo_writer.py module.

Tests SEO metadata generation with mocked Gemini responses
and validates output structure, content quality, and strategy influence.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the module to test
from seo_writer import (
    SEOWriter,
    load_strategy,
    _get_default_value
)

# Mock responses for testing
MOCK_GEMINI_RESPONSE_VIEWS = """{
  "titles": [
    "You Won't Believe These 5 Cooking Secrets from Bangladesh!",
    "Before You Cook Again - Watch This Bengali Technique",
    "Master Chef Reveals Traditional Bengali Cooking Methods"
  ],
  "tags": [
    "bengali cooking", "traditional recipes", "cooking techniques", "bangladesh food",
    "cooking tips", "cooking tutorial", "bengali cuisine", "cooking secrets",
    "food preparation", "cooking methods", "bengali recipes", "cooking channel"
  ],
  "description": "Discover the ancient cooking secrets that Bengali grandmothers have passed down for generations! In this comprehensive guide, you'll learn traditional techniques that will transform your cooking forever. From proper spice tempering to the art of slow cooking, these methods will elevate every dish you make. Don't miss out on these time-tested secrets that professional chefs don't want you to know! LIKE if this helped you cook better, SUBSCRIBE for more authentic recipes, and COMMENT with your favorite Bengali dish!",
  "thumbnail_text": [
    "SECRET REVEALED",
    "ANCIENT METHODS",
    "COOKING MAGIC"
  ]
}"""

MOCK_GEMINI_RESPONSE_SUBSCRIBERS = """{
  "titles": [
    "Complete Bengali Cooking Course - Everything You Need to Know",
    "Join My Kitchen: Learn Authentic Bengali Cooking Step by Step",
    "Bengali Cooking Mastery - Your Journey Starts Here"
  ],
  "tags": [
    "bengali cooking course", "cooking tutorial", "learn cooking", "bengali recipes",
    "cooking lessons", "traditional cooking", "cooking skills", "bengali cuisine",
    "cooking education", "food tutorial", "cooking basics", "bengali food"
  ],
  "description": "Welcome to your complete Bengali cooking journey! I'm here to teach you every technique, every secret, and every tradition that makes Bengali cuisine so special. This is the first video in our comprehensive series where you'll master authentic recipes, traditional methods, and modern adaptations. Join our cooking community and never feel lost in the kitchen again! SUBSCRIBE to follow along with the entire series, LIKE to show your support, and COMMENT to let me know what you want to learn next!",
  "thumbnail_text": [
    "COMPLETE COURSE",
    "LEARN WITH ME",
    "COOKING JOURNEY"
  ]
}"""

MOCK_GEMINI_MALFORMED = """Here's your SEO metadata:

The titles are great and the tags should work well.

{
  "titles": ["Title 1", "Title 2", "Title 3"],
  "tags": ["tag1", "tag2"],
  "description": "Short description"
}

Hope this helps!"""

class TestSEOWriter:
    """Test suite for SEOWriter class."""
    
    @pytest.fixture
    def mock_gemini_model(self):
        """Mock Gemini model for testing."""
        with patch('seo_writer.genai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            yield mock_model
    
    @pytest.fixture
    def sample_keyword_data(self):
        """Sample keyword data for testing."""
        return {
            'autocomplete': [
                'bengali cooking', 'cooking recipes', 'traditional cooking',
                'cooking tips', 'cooking tutorial'
            ],
            'trends': {
                'cooking': {
                    'avg_interest': 65.0,
                    'peak_interest': 80,
                    'related_queries': ['cooking recipes', 'cooking methods'],
                    'rising_terms': ['air fryer cooking', 'healthy cooking']
                },
                'bengali': {
                    'avg_interest': 45.0,
                    'peak_interest': 60,
                    'related_queries': ['bengali food', 'bengali recipes'],
                    'rising_terms': ['authentic bengali', 'traditional bengali']
                }
            },
            'summary': {
                'highest_interest': {'keyword': 'cooking', 'avg_interest': 65.0}
            }
        }
    
    @pytest.fixture
    def sample_strategy_views(self):
        """Sample strategy configuration for views goal."""
        return {
            'goal': 'views',
            'country': 'Bangladesh',
            'audience': 'general',
            'age_range': '18-35',
            'main_keywords': ['bengali cooking', 'traditional recipes']
        }
    
    @pytest.fixture
    def sample_strategy_subscribers(self):
        """Sample strategy configuration for subscribers goal."""
        return {
            'goal': 'subscribers',
            'country': 'India',
            'audience': 'cooking enthusiasts',
            'age_range': '25-45',
            'main_keywords': ['cooking course', 'learn cooking']
        }
    
    def test_seo_writer_initialization_success(self):
        """Test successful SEOWriter initialization."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}):
            writer = SEOWriter()
            assert writer.api_key == 'test_key'
            assert 'curiosity' in writer.psychology_triggers
            assert 'fomo' in writer.psychology_triggers
    
    def test_seo_writer_initialization_no_api_key(self):
        """Test SEOWriter initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Gemini API key not found"):
                SEOWriter()
    
    def test_seo_writer_initialization_custom_api_key(self):
        """Test SEOWriter initialization with custom API key."""
        writer = SEOWriter(api_key='custom_key')
        assert writer.api_key == 'custom_key'
    
    def test_generate_seo_metadata_views_goal(self, mock_gemini_model, sample_keyword_data, sample_strategy_views):
        """Test SEO metadata generation for views goal."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = MOCK_GEMINI_RESPONSE_VIEWS
        mock_gemini_model.generate_content.return_value = mock_response
        
        # Initialize writer and generate metadata
        writer = SEOWriter(api_key='test_key')
        writer.model = mock_gemini_model
        
        result = writer.generate_seo_metadata(
            "Traditional Bengali Cooking Techniques",
            sample_keyword_data,
            sample_strategy_views
        )
        
        # Validate structure
        assert isinstance(result, dict)
        assert 'titles' in result
        assert 'tags' in result
        assert 'description' in result
        assert 'thumbnail_text' in result
        
        # Validate titles
        assert isinstance(result['titles'], list)
        assert len(result['titles']) == 3
        assert all(isinstance(title, str) for title in result['titles'])
        
        # Check for psychology triggers in titles
        titles_text = ' '.join(result['titles']).lower()
        assert any(trigger in titles_text for trigger in ['won\'t believe', 'before you', 'reveals'])
        
        # Validate tags
        assert isinstance(result['tags'], list)
        assert 10 <= len(result['tags']) <= 15
        assert 'bengali cooking' in result['tags']
        
        # Validate description
        assert isinstance(result['description'], str)
        assert len(result['description']) >= 100
        assert 'bengali' in result['description'].lower()
        
        # Validate thumbnail text
        assert isinstance(result['thumbnail_text'], list)
        assert len(result['thumbnail_text']) == 3
        assert all(len(text.split()) <= 5 for text in result['thumbnail_text'])
    
    def test_generate_seo_metadata_subscribers_goal(self, mock_gemini_model, sample_keyword_data, sample_strategy_subscribers):
        """Test SEO metadata generation for subscribers goal."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = MOCK_GEMINI_RESPONSE_SUBSCRIBERS
        mock_gemini_model.generate_content.return_value = mock_response
        
        # Initialize writer and generate metadata
        writer = SEOWriter(api_key='test_key')
        writer.model = mock_gemini_model
        
        result = writer.generate_seo_metadata(
            "Bengali Cooking Course",
            sample_keyword_data,
            sample_strategy_subscribers
        )
        
        # Validate subscriber-focused content
        titles_text = ' '.join(result['titles']).lower()
        assert any(word in titles_text for word in ['complete', 'course', 'learn', 'join'])
        
        description_lower = result['description'].lower()
        assert any(word in description_lower for word in ['subscribe', 'community', 'series', 'journey'])
        
        # Verify Gemini was called
        mock_gemini_model.generate_content.assert_called_once()
        call_args = mock_gemini_model.generate_content.call_args[0][0]
        assert 'subscribers' in call_args.lower()
        assert 'community building' in call_args
    
    def test_generate_seo_metadata_malformed_response(self, mock_gemini_model, sample_keyword_data, sample_strategy_views):
        """Test handling of malformed Gemini response."""
        # Setup malformed mock response
        mock_response = Mock()
        mock_response.text = MOCK_GEMINI_MALFORMED
        mock_gemini_model.generate_content.return_value = mock_response
        
        writer = SEOWriter(api_key='test_key')
        writer.model = mock_gemini_model
        
        result = writer.generate_seo_metadata(
            "Test Topic",
            sample_keyword_data,
            sample_strategy_views
        )
        
        # Should still return valid structure (fallback)
        assert isinstance(result, dict)
        assert 'titles' in result
        assert 'tags' in result
        assert 'description' in result
        assert 'thumbnail_text' in result
        
        # Validate fallback content
        assert len(result['titles']) == 3
        assert len(result['thumbnail_text']) == 3
        assert isinstance(result['tags'], list)
    
    def test_generate_seo_metadata_empty_response(self, mock_gemini_model, sample_keyword_data, sample_strategy_views):
        """Test handling of empty Gemini response."""
        # Setup empty mock response
        mock_response = Mock()
        mock_response.text = ""
        mock_gemini_model.generate_content.return_value = mock_response
        
        writer = SEOWriter(api_key='test_key')
        writer.model = mock_gemini_model
        
        result = writer.generate_seo_metadata(
            "Test Topic",
            sample_keyword_data,
            sample_strategy_views
        )
        
        # Should return fallback metadata
        assert isinstance(result, dict)
        assert len(result['titles']) == 3
        assert 'Ultimate Guide' in result['titles'][0]
    
    def test_generate_seo_metadata_api_error(self, mock_gemini_model, sample_keyword_data, sample_strategy_views):
        """Test handling of Gemini API errors."""
        # Setup API error
        mock_gemini_model.generate_content.side_effect = Exception("API Error")
        
        writer = SEOWriter(api_key='test_key')
        writer.model = mock_gemini_model
        
        result = writer.generate_seo_metadata(
            "Test Topic",
            sample_keyword_data,
            sample_strategy_views
        )
        
        # Should return fallback metadata
        assert isinstance(result, dict)
        assert 'titles' in result
        assert len(result['titles']) == 3
    
    def test_build_seo_prompt_content(self, sample_keyword_data, sample_strategy_views):
        """Test that SEO prompt includes required elements."""
        writer = SEOWriter(api_key='test_key')
        
        prompt = writer._build_seo_prompt(
            "Bengali Cooking",
            sample_keyword_data,
            sample_strategy_views
        )
        
        # Check for key elements
        assert 'Bengali Cooking' in prompt
        assert 'Bangladesh' in prompt
        assert 'views' in prompt
        assert 'PSYCHOLOGY TRIGGERS' in prompt
        assert 'curiosity' in prompt.lower()
        assert 'fomo' in prompt.lower()
        assert 'cooking' in prompt  # From keyword data
        assert 'JSON' in prompt
    
    def test_psychology_triggers_coverage(self):
        """Test that all psychology trigger categories are present."""
        writer = SEOWriter(api_key='test_key')
        
        expected_categories = ['curiosity', 'fomo', 'authority', 'scarcity', 'relatability']
        
        for category in expected_categories:
            assert category in writer.psychology_triggers
            assert len(writer.psychology_triggers[category]) > 0
            assert all(isinstance(trigger, str) for trigger in writer.psychology_triggers[category])


class TestLoadStrategy:
    """Test suite for strategy configuration loading."""
    
    def test_load_strategy_valid_file(self):
        """Test loading valid strategy configuration."""
        strategy_data = {
            'goal': 'views',
            'country': 'Bangladesh',
            'audience': 'general',
            'age_range': '18-35',
            'main_keywords': ['cooking', 'recipe']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(strategy_data, f)
            temp_path = f.name
        
        try:
            result = load_strategy(temp_path)
            
            assert result['goal'] == 'views'
            assert result['country'] == 'Bangladesh'
            assert result['audience'] == 'general'
            assert result['age_range'] == '18-35'
            assert result['main_keywords'] == ['cooking', 'recipe']
        finally:
            os.unlink(temp_path)
    
    def test_load_strategy_missing_file(self):
        """Test loading strategy when file doesn't exist."""
        result = load_strategy('nonexistent_file.json')
        
        # Should return default strategy
        assert result['goal'] == 'views'
        assert result['country'] == 'Global'
        assert result['audience'] == 'general'
        assert result['age_range'] == '18-35'
        assert result['main_keywords'] == []
    
    def test_load_strategy_invalid_json(self):
        """Test loading strategy with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_strategy(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_strategy_missing_fields(self):
        """Test loading strategy with missing required fields."""
        incomplete_strategy = {
            'goal': 'subscribers',
            'country': 'India'
            # Missing audience and age_range
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(incomplete_strategy, f)
            temp_path = f.name
        
        try:
            result = load_strategy(temp_path)
            
            # Should fill in defaults
            assert result['goal'] == 'subscribers'
            assert result['country'] == 'India'
            assert result['audience'] == 'general'  # Default
            assert result['age_range'] == '18-35'   # Default
            assert result['main_keywords'] == []    # Default
        finally:
            os.unlink(temp_path)
    
    def test_load_strategy_invalid_goal(self):
        """Test loading strategy with invalid goal."""
        invalid_strategy = {
            'goal': 'invalid_goal',
            'country': 'Bangladesh',
            'audience': 'general',
            'age_range': '18-35'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_strategy, f)
            temp_path = f.name
        
        try:
            result = load_strategy(temp_path)
            
            # Should default to 'views'
            assert result['goal'] == 'views'
        finally:
            os.unlink(temp_path)
    
    def test_load_strategy_non_list_keywords(self):
        """Test loading strategy with non-list main_keywords."""
        invalid_strategy = {
            'goal': 'views',
            'country': 'Bangladesh',
            'audience': 'general',
            'age_range': '18-35',
            'main_keywords': 'not a list'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_strategy, f)
            temp_path = f.name
        
        try:
            result = load_strategy(temp_path)
            
            # Should convert to empty list
            assert result['main_keywords'] == []
        finally:
            os.unlink(temp_path)


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_get_default_value(self):
        """Test default value retrieval."""
        assert _get_default_value('goal') == 'views'
        assert _get_default_value('country') == 'Global'
        assert _get_default_value('audience') == 'general'
        assert _get_default_value('age_range') == '18-35'
        assert _get_default_value('unknown_field') == ''


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_workflow_views_strategy(self, mock_gemini_model):
        """Test complete workflow with views strategy."""
        # Setup
        mock_response = Mock()
        mock_response.text = MOCK_GEMINI_RESPONSE_VIEWS
        mock_gemini_model.generate_content.return_value = mock_response
        
        keyword_data = {
            'autocomplete': ['cooking tips', 'bengali recipes'],
            'trends': {
                'cooking': {'avg_interest': 70.0, 'rising_terms': ['healthy cooking']}
            },
            'summary': {'highest_interest': {'keyword': 'cooking', 'avg_interest': 70.0}}
        }
        
        strategy = {
            'goal': 'views',
            'country': 'Bangladesh',
            'audience': 'food lovers',
            'age_range': '20-40',
            'main_keywords': ['bengali cooking']
        }
        
        # Execute
        writer = SEOWriter(api_key='test_key')
        writer.model = mock_gemini_model
        
        result = writer.generate_seo_metadata("Bengali Street Food", keyword_data, strategy)
        
        # Validate
        assert len(result['titles']) == 3
        assert len(result['tags']) >= 10
        assert len(result['description']) > 100
        assert len(result['thumbnail_text']) == 3
        
        # Check that strategy influenced the prompt
        call_args = mock_gemini_model.generate_content.call_args[0][0]
        assert 'Bangladesh' in call_args
        assert 'views' in call_args
        assert 'viral potential' in call_args


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
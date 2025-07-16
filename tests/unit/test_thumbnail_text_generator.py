"""
Unit tests for thumbnail_text_generator.py module.

Tests thumbnail text generation with mocked Gemini responses
and validates output structure, psychology triggers, and power word usage.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Import the module to test
from thumbnail_text_generator import (
    ThumbnailTextGenerator,
    generate_thumbnail_texts
)

# Mock Gemini responses for testing
MOCK_AI_RESPONSE = """1. SECRET REVEALED NOW
2. YOU WON'T BELIEVE
3. EXPERT TIPS INSIDE"""

MOCK_MALFORMED_RESPONSE = """Here are some thumbnail ideas:
- Great cooking tips
- Amazing results
- Must watch video

Hope this helps!"""

class TestThumbnailTextGenerator:
    """Test suite for ThumbnailTextGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create ThumbnailTextGenerator instance for testing."""
        return ThumbnailTextGenerator(api_key='test_api_key')
    
    @pytest.fixture
    def generator_no_key(self):
        """Create ThumbnailTextGenerator without API key."""
        return ThumbnailTextGenerator()
    
    @pytest.fixture
    def sample_ideas(self):
        """Sample video ideas for testing."""
        return [
            {
                'title': 'Ultimate Guide to Cooking Perfect Rice',
                'brief': 'Learn professional techniques for perfect rice every time.',
                'target_keywords': ['cooking rice', 'perfect rice', 'rice tutorial'],
                'psychology_triggers': ['authority', 'curiosity'],
                'call_to_action': '🔔 SUBSCRIBE for more cooking secrets!'
            },
            {
                'title': 'You Won\'t Believe These Study Secrets',
                'brief': 'Hidden study techniques that top students use.',
                'target_keywords': ['study secrets', 'study tips', 'academic success'],
                'psychology_triggers': ['curiosity', 'scarcity'],
                'call_to_action': '💬 COMMENT your study questions!'
            }
        ]
    
    @pytest.fixture
    def sample_strategy_views(self):
        """Sample strategy for views goal."""
        return {
            'goal': 'views',
            'country': 'Bangladesh',
            'audience': 'students',
            'age_range': '18-25'
        }
    
    @pytest.fixture
    def sample_strategy_subscribers(self):
        """Sample strategy for subscribers goal."""
        return {
            'goal': 'subscribers',
            'country': 'India',
            'audience': 'professionals',
            'age_range': '25-35'
        }
    
    def test_generator_initialization_with_key(self, generator):
        """Test generator initialization with API key."""
        assert generator.api_key == 'test_api_key'
        assert generator.model is not None
        assert 'curiosity' in generator.psychology_triggers
        assert 'views' in generator.goal_strategies
    
    def test_generator_initialization_no_key(self, generator_no_key):
        """Test generator initialization without API key."""
        assert generator_no_key.api_key is None
        assert generator_no_key.model is None
        assert len(generator_no_key.psychology_triggers) == 5
    
    def test_psychology_triggers_structure(self, generator):
        """Test psychology triggers data structure."""
        expected_triggers = ['curiosity', 'fomo', 'authority', 'emotional', 'scarcity']
        
        for trigger in expected_triggers:
            assert trigger in generator.psychology_triggers
            trigger_data = generator.psychology_triggers[trigger]
            assert 'templates' in trigger_data
            assert 'power_words' in trigger_data
            assert len(trigger_data['templates']) >= 5
            assert len(trigger_data['power_words']) >= 3
    
    def test_goal_strategies_structure(self, generator):
        """Test goal strategies configuration."""
        expected_goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        
        for goal in expected_goals:
            assert goal in generator.goal_strategies
            strategy = generator.goal_strategies[goal]
            assert 'primary_triggers' in strategy
            assert 'style' in strategy
            assert 'emphasis' in strategy
    
    @patch('thumbnail_text_generator.genai.GenerativeModel')
    def test_generate_texts_with_ai_success(self, mock_model_class, generator, sample_ideas, sample_strategy_views):
        """Test successful thumbnail text generation with AI."""
        # Setup mock
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = MOCK_AI_RESPONSE
        mock_model.generate_content.return_value = mock_response
        
        generator.model = mock_model
        
        # Test the function
        result = generator.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Validate structure
        assert isinstance(result, list)
        assert len(result) == len(sample_ideas)
        
        # Validate each enhanced idea
        for idea in result:
            assert isinstance(idea, dict)
            assert 'thumbnail_texts' in idea
            assert isinstance(idea['thumbnail_texts'], list)
            assert len(idea['thumbnail_texts']) == 3
            
            # Validate each thumbnail text
            for text in idea['thumbnail_texts']:
                assert isinstance(text, str)
                assert len(text) > 0
                assert len(text.split()) <= 6  # Max 6 words
                assert text.isupper()  # Should be uppercase
    
    def test_generate_texts_fallback_mode(self, generator_no_key, sample_ideas, sample_strategy_views):
        """Test thumbnail text generation in fallback mode (no API key)."""
        result = generator_no_key.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Should still return valid structure
        assert isinstance(result, list)
        assert len(result) == len(sample_ideas)
        
        # Validate each idea has thumbnail texts
        for idea in result:
            assert 'thumbnail_texts' in idea
            assert len(idea['thumbnail_texts']) == 3
            
            # Check text quality
            for text in idea['thumbnail_texts']:
                assert isinstance(text, str)
                assert len(text.split()) <= 6
                assert text.isupper()
    
    def test_generate_texts_different_goals(self, generator, sample_ideas):
        """Test that different goals produce different types of texts."""
        goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        results = {}
        
        for goal in goals:
            strategy = {
                'goal': goal,
                'country': 'Bangladesh',
                'audience': 'general',
                'age_range': '18-35'
            }
            
            result = generator.generate_thumbnail_texts(sample_ideas, strategy)
            results[goal] = result
        
        # Different goals should produce different text styles
        all_texts = []
        for goal in goals:
            for idea in results[goal]:
                all_texts.extend(idea['thumbnail_texts'])
        
        # Should have variety in texts
        unique_texts = set(all_texts)
        assert len(unique_texts) > len(goals)  # More unique texts than goals
    
    @patch('thumbnail_text_generator.genai.GenerativeModel')
    def test_generate_texts_ai_error_handling(self, mock_model_class, generator, sample_ideas, sample_strategy_views):
        """Test error handling when AI generation fails."""
        # Setup mock to raise exception
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")
        
        generator.model = mock_model
        
        result = generator.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Should still return valid result using fallback
        assert isinstance(result, list)
        assert len(result) == len(sample_ideas)
        assert all('thumbnail_texts' in idea for idea in result)
    
    @patch('thumbnail_text_generator.genai.GenerativeModel')
    def test_generate_texts_malformed_ai_response(self, mock_model_class, generator, sample_ideas, sample_strategy_views):
        """Test handling of malformed AI response."""
        # Setup malformed mock response
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = MOCK_MALFORMED_RESPONSE
        mock_model.generate_content.return_value = mock_response
        
        generator.model = mock_model
        
        result = generator.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Should fall back to template generation
        assert isinstance(result, list)
        assert len(result) == len(sample_ideas)
        assert all('thumbnail_texts' in idea for idea in result)
    
    def test_generate_texts_fallback_quality(self, generator, sample_ideas, sample_strategy_views):
        """Test fallback text generation quality."""
        # Force fallback by removing model
        generator.model = None
        
        result = generator.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Validate text quality
        for idea in result:
            texts = idea['thumbnail_texts']
            
            # Should have power words
            has_power_word = False
            for text in texts:
                if any(word in text.upper() for word in generator.power_words):
                    has_power_word = True
                    break
            assert has_power_word, f"No power words found in: {texts}"
            
            # Should have psychology triggers
            has_trigger = False
            for text in texts:
                for trigger_data in generator.psychology_triggers.values():
                    if any(template_word in text for template in trigger_data['templates'] 
                          for template_word in template.split()):
                        has_trigger = True
                        break
                if has_trigger:
                    break
            assert has_trigger, f"No psychology triggers found in: {texts}"
    
    def test_validate_thumbnail_texts(self, generator, sample_ideas, sample_strategy_views):
        """Test thumbnail text validation functionality."""
        # Generate texts first
        enhanced_ideas = generator.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Validate the results
        validation = generator.validate_thumbnail_texts(enhanced_ideas)
        
        assert isinstance(validation, dict)
        assert 'total_ideas' in validation
        assert 'valid_texts' in validation
        assert 'power_word_coverage' in validation
        assert 'length_compliance' in validation
        assert 'issues' in validation
        
        # Should have processed all ideas
        assert validation['total_ideas'] == len(sample_ideas)
        
        # Should have high compliance rates
        assert validation['valid_texts'] >= len(sample_ideas) * 0.8  # At least 80%
        assert validation['length_compliance'] >= len(sample_ideas) * 0.8
    
    def test_create_emergency_fallback(self, generator):
        """Test emergency fallback text creation."""
        fallback_texts = generator._create_emergency_fallback()
        
        assert isinstance(fallback_texts, list)
        assert len(fallback_texts) == 3
        assert all(isinstance(text, str) for text in fallback_texts)
        assert all(len(text.split()) <= 6 for text in fallback_texts)
    
    def test_invalid_inputs(self, generator):
        """Test handling of invalid inputs."""
        # Test with invalid ideas
        result = generator.generate_thumbnail_texts("invalid", {'goal': 'views'})
        assert isinstance(result, list)
        
        # Test with empty ideas
        result = generator.generate_thumbnail_texts([], {'goal': 'views'})
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test with invalid strategy
        result = generator.generate_thumbnail_texts([{'title': 'test'}], "invalid")
        assert isinstance(result, list)
    
    def test_power_word_integration(self, generator, sample_ideas, sample_strategy_views):
        """Test that power words are properly integrated."""
        result = generator.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Check that power words appear in generated texts
        all_texts = []
        for idea in result:
            all_texts.extend(idea['thumbnail_texts'])
        
        combined_text = ' '.join(all_texts).upper()
        
        # Should contain at least some power words
        power_word_count = sum(1 for word in generator.power_words if word in combined_text)
        assert power_word_count > 0, f"No power words found in: {all_texts}"
    
    def test_psychology_trigger_variety(self, generator, sample_ideas, sample_strategy_views):
        """Test that different psychology triggers are used."""
        result = generator.generate_thumbnail_texts(sample_ideas, sample_strategy_views)
        
        # Collect all texts
        all_texts = []
        for idea in result:
            all_texts.extend(idea['thumbnail_texts'])
        
        # Check for trigger variety
        trigger_found = {trigger: False for trigger in generator.psychology_triggers.keys()}
        
        for text in all_texts:
            for trigger, trigger_data in generator.psychology_triggers.items():
                for template in trigger_data['templates']:
                    if any(word in text.upper() for word in template.split()):
                        trigger_found[trigger] = True
        
        # Should use multiple different triggers
        triggers_used = sum(trigger_found.values())
        assert triggers_used >= 2, f"Only {triggers_used} triggers used: {trigger_found}"


class TestUtilityFunctions:
    """Test utility functions."""
    
    @patch('thumbnail_text_generator.ThumbnailTextGenerator')
    def test_generate_thumbnail_texts_utility(self, mock_generator_class):
        """Test generate_thumbnail_texts utility function."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_thumbnail_texts.return_value = [{'thumbnail_texts': ['TEST']}]
        
        ideas = [{'title': 'test'}]
        strategy = {'goal': 'views'}
        
        result = generate_thumbnail_texts(ideas, strategy)
        
        mock_generator_class.assert_called_once()
        mock_generator.generate_thumbnail_texts.assert_called_once_with(ideas, strategy)
        assert result == [{'thumbnail_texts': ['TEST']}]


class TestIntegration:
    """Integration tests for complete workflow."""
    
    @patch('thumbnail_text_generator.genai.GenerativeModel')
    def test_complete_thumbnail_generation_workflow(self, mock_model_class):
        """Test complete thumbnail text generation workflow."""
        # Setup mock
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = MOCK_AI_RESPONSE
        mock_model.generate_content.return_value = mock_response
        
        # Test data
        ideas = [
            {
                'title': 'Amazing Cooking Secrets Revealed',
                'brief': 'Professional chef shares insider techniques.',
                'target_keywords': ['cooking secrets', 'chef tips'],
                'psychology_triggers': ['authority', 'curiosity'],
                'call_to_action': 'Subscribe for more!'
            }
        ]
        
        strategy = {
            'goal': 'subscribers',
            'country': 'Bangladesh',
            'audience': 'home cooks',
            'age_range': '25-45'
        }
        
        # Run generation
        generator = ThumbnailTextGenerator(api_key='test_key')
        generator.model = mock_model
        
        result = generator.generate_thumbnail_texts(ideas, strategy)
        
        # Validate complete result
        assert len(result) == 1
        idea = result[0]
        
        # Should have all original fields plus thumbnail_texts
        assert 'title' in idea
        assert 'brief' in idea
        assert 'target_keywords' in idea
        assert 'psychology_triggers' in idea
        assert 'call_to_action' in idea
        assert 'thumbnail_texts' in idea
        
        # Validate thumbnail texts
        texts = idea['thumbnail_texts']
        assert len(texts) == 3
        assert all(isinstance(text, str) for text in texts)
        assert all(text.isupper() for text in texts)
        assert all(len(text.split()) <= 6 for text in texts)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
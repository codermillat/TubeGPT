"""
Unit tests for emotion_optimizer.py module.

Tests psychological trigger optimization with mocked Gemini responses
and validates trigger classification and strategy influence.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the module to test
from emotion_optimizer import (
    EmotionOptimizer,
    optimize_metadata,
    label_psychology
)

# Mock Gemini responses for testing
MOCK_TITLE_RESPONSE = """1. You Won't Believe This Secret Rice Cooking Method!
2. Before You Cook Rice Again - Watch This Bengali Technique
3. Expert Reveals: Traditional Rice Cooking Secrets"""

MOCK_THUMBNAIL_RESPONSE = """1. SECRET REVEALED
2. BEFORE YOU COOK
3. EXPERT TIPS"""

MOCK_MALFORMED_RESPONSE = """Here are some enhanced titles:
- Great rice cooking tips
- Amazing Bengali methods
- Wonderful traditional techniques

Hope this helps!"""

class TestEmotionOptimizer:
    """Test suite for EmotionOptimizer class."""
    
    @pytest.fixture
    def optimizer(self):
        """Create EmotionOptimizer instance for testing."""
        return EmotionOptimizer(api_key='test_api_key')
    
    @pytest.fixture
    def optimizer_no_key(self):
        """Create EmotionOptimizer without API key."""
        return EmotionOptimizer()
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            'titles': [
                'How to Cook Perfect Rice',
                'Bengali Rice Cooking Tutorial',
                'Traditional Rice Methods'
            ],
            'description': 'Learn to cook perfect rice with traditional Bengali methods. This guide covers everything you need to know.',
            'thumbnail_text': [
                'PERFECT RICE',
                'EASY METHOD',
                'BENGALI STYLE'
            ],
            'tags': ['rice cooking', 'bengali food', 'tutorial']
        }
    
    @pytest.fixture
    def sample_strategy_views(self):
        """Sample strategy for views goal."""
        return {
            'goal': 'views',
            'country': 'Bangladesh',
            'audience': 'home cooks',
            'age_range': '25-45'
        }
    
    @pytest.fixture
    def sample_strategy_subscribers(self):
        """Sample strategy for subscribers goal."""
        return {
            'goal': 'subscribers',
            'country': 'India',
            'audience': 'cooking enthusiasts',
            'age_range': '30-50'
        }
    
    def test_optimizer_initialization_with_key(self, optimizer):
        """Test optimizer initialization with API key."""
        assert optimizer.api_key == 'test_api_key'
        assert optimizer.model is not None
        assert 'curiosity' in optimizer.psychology_triggers
        assert 'views' in optimizer.goal_strategies
    
    def test_optimizer_initialization_no_key(self, optimizer_no_key):
        """Test optimizer initialization without API key."""
        assert optimizer_no_key.api_key is None
        assert optimizer_no_key.model is None
        assert len(optimizer_no_key.psychology_triggers) == 5
    
    def test_psychology_triggers_structure(self, optimizer):
        """Test psychology triggers data structure."""
        expected_triggers = ['curiosity', 'fomo', 'authority', 'emotional', 'scarcity']
        
        for trigger in expected_triggers:
            assert trigger in optimizer.psychology_triggers
            trigger_data = optimizer.psychology_triggers[trigger]
            assert 'emoji' in trigger_data
            assert 'patterns' in trigger_data
            assert 'keywords' in trigger_data
            assert len(trigger_data['patterns']) >= 5
            assert len(trigger_data['keywords']) >= 3
    
    def test_goal_strategies_structure(self, optimizer):
        """Test goal strategies configuration."""
        expected_goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        
        for goal in expected_goals:
            assert goal in optimizer.goal_strategies
            strategy = optimizer.goal_strategies[goal]
            assert 'primary_triggers' in strategy
            assert 'cta_style' in strategy
            assert 'tone' in strategy
            assert 'focus' in strategy
    
    @patch('emotion_optimizer.genai.GenerativeModel')
    def test_optimize_metadata_with_ai_success(self, mock_model_class, sample_metadata, sample_strategy_views):
        """Test successful metadata optimization with AI."""
        # Setup mock
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        # Mock title optimization response
        mock_response_titles = Mock()
        mock_response_titles.text = MOCK_TITLE_RESPONSE
        
        # Mock thumbnail optimization response
        mock_response_thumbnails = Mock()
        mock_response_thumbnails.text = MOCK_THUMBNAIL_RESPONSE
        
        # Set up side effects for multiple calls
        mock_model.generate_content.side_effect = [mock_response_titles, mock_response_thumbnails]
        
        optimizer = EmotionOptimizer(api_key='test_key')
        optimizer.model = mock_model
        
        result = optimizer.optimize_metadata(sample_metadata, sample_strategy_views)
        
        # Validate structure
        assert isinstance(result, dict)
        assert 'titles' in result
        assert 'description' in result
        assert 'thumbnail_text' in result
        assert 'tags' in result
        assert 'cta_suggestions' in result
        assert 'psychology_labels' in result
        
        # Validate enhanced titles
        assert len(result['titles']) <= 3
        titles_text = ' '.join(result['titles']).lower()
        assert any(trigger_word in titles_text for trigger_word in ['secret', 'before', 'expert'])
        
        # Validate enhanced thumbnail text
        assert len(result['thumbnail_text']) <= 3
        assert all(text.isupper() for text in result['thumbnail_text'])
        
        # Validate CTA suggestions
        assert len(result['cta_suggestions']) >= 1
        assert any('🔥' in cta or '🔔' in cta for cta in result['cta_suggestions'])
    
    def test_optimize_metadata_fallback_mode(self, optimizer_no_key, sample_metadata, sample_strategy_views):
        """Test metadata optimization in fallback mode (no API key)."""
        result = optimizer_no_key.optimize_metadata(sample_metadata, sample_strategy_views)
        
        # Should still return valid structure
        assert isinstance(result, dict)
        assert 'titles' in result
        assert 'description' in result
        assert 'thumbnail_text' in result
        assert 'cta_suggestions' in result
        
        # Titles should be enhanced with fallback patterns
        assert len(result['titles']) <= 3
        
        # Should have CTA suggestions
        assert len(result['cta_suggestions']) >= 1
    
    def test_optimize_metadata_different_goals(self, optimizer, sample_metadata):
        """Test optimization varies by goal."""
        goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        results = {}
        
        for goal in goals:
            strategy = {
                'goal': goal,
                'country': 'Bangladesh',
                'audience': 'general',
                'age_range': '18-35'
            }
            
            result = optimizer.optimize_metadata(sample_metadata, strategy)
            results[goal] = result
        
        # Different goals should produce different CTAs
        cta_texts = [' '.join(results[goal]['cta_suggestions']) for goal in goals]
        
        # Views should focus on sharing/engagement
        assert any('share' in cta.lower() or 'like' in cta.lower() for cta in cta_texts)
        
        # Subscribers should focus on subscription
        subscribers_cta = results['subscribers']['cta_suggestions']
        assert any('subscribe' in cta.lower() for cta in subscribers_cta)
    
    @patch('emotion_optimizer.genai.GenerativeModel')
    def test_optimize_metadata_ai_error_handling(self, mock_model_class, sample_metadata, sample_strategy_views):
        """Test error handling when AI optimization fails."""
        # Setup mock to raise exception
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")
        
        optimizer = EmotionOptimizer(api_key='test_key')
        optimizer.model = mock_model
        
        result = optimizer.optimize_metadata(sample_metadata, sample_strategy_views)
        
        # Should still return valid result using fallback
        assert isinstance(result, dict)
        assert 'titles' in result
        assert len(result['titles']) > 0
    
    def test_optimize_titles_fallback(self, optimizer, sample_strategy_views):
        """Test fallback title optimization."""
        titles = ['How to Cook Rice', 'Bengali Cooking Tips', 'Traditional Methods']
        goal_strategy = optimizer.goal_strategies['views']
        
        result = optimizer._optimize_titles_fallback(titles, goal_strategy)
        
        assert len(result) == 3
        assert all(isinstance(title, str) for title in result)
        
        # Should contain psychological triggers
        all_titles = ' '.join(result).lower()
        trigger_words = ['secret', 'before', 'expert', 'exclusive', 'if you']
        assert any(word in all_titles for word in trigger_words)
    
    def test_optimize_thumbnail_text_fallback(self, optimizer, sample_strategy_views):
        """Test fallback thumbnail text optimization."""
        texts = ['COOKING TIPS', 'RICE GUIDE', 'BENGALI STYLE']
        goal_strategy = optimizer.goal_strategies['views']
        
        result = optimizer._optimize_thumbnail_text_fallback(texts, goal_strategy)
        
        assert len(result) <= 3
        assert all(text.isupper() for text in result)
        assert all(len(text) <= 20 for text in result)
    
    def test_generate_cta_suggestions(self, optimizer):
        """Test CTA generation for different goals."""
        strategies = [
            {'goal': 'views', 'audience': 'students'},
            {'goal': 'subscribers', 'audience': 'professionals'},
            {'goal': 'engagement', 'audience': 'creators'}
        ]
        
        for strategy in strategies:
            goal_strategy = optimizer.goal_strategies[strategy['goal']]
            ctas = optimizer._generate_cta_suggestions(strategy, goal_strategy)
            
            assert len(ctas) >= 1
            assert all(isinstance(cta, str) for cta in ctas)
            assert any(strategy['audience'] in cta.lower() for cta in ctas)
    
    def test_label_psychology_comprehensive(self, optimizer):
        """Test comprehensive psychology labeling."""
        metadata = {
            'titles': [
                'You Won\'t Believe This Secret Method!',
                'Before It\'s Too Late - Limited Time',
                'Expert Reveals Professional Tips'
            ],
            'thumbnail_text': [
                'SECRET REVEALED',
                'LIMITED TIME',
                'EXPERT TIPS'
            ],
            'description': 'Discover the hidden truth that experts don\'t want you to know. This exclusive method is only available for a limited time.'
        }
        
        result = optimizer.label_psychology(metadata)
        
        assert isinstance(result, dict)
        assert 'title_triggers' in result
        assert 'thumbnail_triggers' in result
        assert 'description_triggers' in result
        assert 'dominant_trigger' in result
        assert 'trigger_distribution' in result
        
        # Should identify multiple triggers
        assert len(result['trigger_distribution']) > 0
        assert result['dominant_trigger'] is not None
    
    def test_identify_triggers_in_text(self, optimizer):
        """Test trigger identification in text."""
        test_cases = [
            ('You won\'t believe this secret!', ['curiosity']),
            ('Limited time offer - don\'t miss out!', ['fomo', 'scarcity']),
            ('Expert reveals proven method', ['authority']),
            ('If you\'ve ever felt frustrated...', ['emotional']),
            ('Exclusive access only today', ['scarcity'])
        ]
        
        for text, expected_triggers in test_cases:
            result = optimizer._identify_triggers_in_text(text)
            
            # Should identify at least one expected trigger
            assert any(trigger in result for trigger in expected_triggers)
    
    def test_invalid_inputs(self, optimizer):
        """Test handling of invalid inputs."""
        # Test with invalid metadata
        with pytest.raises(ValueError, match="Metadata must be a dictionary"):
            optimizer.optimize_metadata("invalid", {'goal': 'views'})
        
        # Test with invalid strategy
        with pytest.raises(ValueError, match="Strategy must be a dictionary"):
            optimizer.optimize_metadata({'titles': []}, "invalid")
        
        # Test with empty inputs
        result = optimizer.optimize_metadata({}, {})
        assert isinstance(result, dict)
        assert 'titles' in result


class TestUtilityFunctions:
    """Test utility functions."""
    
    @patch('emotion_optimizer.EmotionOptimizer')
    def test_optimize_metadata_utility(self, mock_optimizer_class):
        """Test optimize_metadata utility function."""
        mock_optimizer = Mock()
        mock_optimizer_class.return_value = mock_optimizer
        mock_optimizer.optimize_metadata.return_value = {'titles': ['test']}
        
        metadata = {'titles': ['original']}
        strategy = {'goal': 'views'}
        
        result = optimize_metadata(metadata, strategy)
        
        mock_optimizer_class.assert_called_once()
        mock_optimizer.optimize_metadata.assert_called_once_with(metadata, strategy)
        assert result == {'titles': ['test']}
    
    @patch('emotion_optimizer.EmotionOptimizer')
    def test_label_psychology_utility(self, mock_optimizer_class):
        """Test label_psychology utility function."""
        mock_optimizer = Mock()
        mock_optimizer_class.return_value = mock_optimizer
        mock_optimizer.label_psychology.return_value = {'dominant_trigger': 'curiosity'}
        
        metadata = {'titles': ['test']}
        
        result = label_psychology(metadata)
        
        mock_optimizer_class.assert_called_once()
        mock_optimizer.label_psychology.assert_called_once_with(metadata)
        assert result == {'dominant_trigger': 'curiosity'}


class TestIntegration:
    """Integration tests for complete workflow."""
    
    @patch('emotion_optimizer.genai.GenerativeModel')
    def test_complete_optimization_workflow(self, mock_model_class):
        """Test complete optimization workflow."""
        # Setup mock
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = MOCK_TITLE_RESPONSE
        mock_model.generate_content.return_value = mock_response
        
        # Test data
        metadata = {
            'titles': ['Basic Cooking Tutorial', 'Simple Recipe Guide'],
            'description': 'Learn basic cooking techniques.',
            'thumbnail_text': ['COOKING', 'RECIPE'],
            'tags': ['cooking', 'tutorial']
        }
        
        strategy = {
            'goal': 'subscribers',
            'country': 'Bangladesh',
            'audience': 'home cooks',
            'age_range': '25-45'
        }
        
        # Run optimization
        optimizer = EmotionOptimizer(api_key='test_key')
        optimizer.model = mock_model
        
        result = optimizer.optimize_metadata(metadata, strategy)
        
        # Validate complete result
        assert 'titles' in result
        assert 'description' in result
        assert 'thumbnail_text' in result
        assert 'cta_suggestions' in result
        assert 'psychology_labels' in result
        
        # Validate psychology labeling
        labels = result['psychology_labels']
        assert 'trigger_distribution' in labels
        assert 'dominant_trigger' in labels
        
        # Should be optimized for subscribers goal
        cta_text = ' '.join(result['cta_suggestions']).lower()
        assert 'subscribe' in cta_text or 'community' in cta_text


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
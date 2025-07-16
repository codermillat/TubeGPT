"""
Unit tests for video_idea_generator.py module.

Tests video idea generation with mocked data and validates
output structure, content quality, and strategy influence.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Import the module to test
from video_idea_generator import (
    VideoIdeaGenerator,
    generate_video_ideas
)

# Mock Gemini responses for testing
MOCK_AI_RESPONSE = """[
  {
    "title": "You Won't Believe These Visa Interview Secrets!",
    "brief": "Discover insider tips that visa officers don't want you to know, guaranteed to improve your chances.",
    "target_keywords": ["visa interview", "visa tips", "interview secrets"],
    "psychology_triggers": ["curiosity", "scarcity"],
    "estimated_appeal": "high"
  },
  {
    "title": "Before You Apply - Study Abroad Mistakes to Avoid",
    "brief": "Critical mistakes that could ruin your study abroad dreams and how to avoid them.",
    "target_keywords": ["study abroad", "application mistakes", "student guide"],
    "psychology_triggers": ["fomo", "authority"],
    "estimated_appeal": "high"
  },
  {
    "title": "Expert Reveals: Cooking Techniques That Changed Everything",
    "brief": "Professional chef shares game-changing techniques that will transform your cooking forever.",
    "target_keywords": ["cooking techniques", "chef secrets", "cooking tips"],
    "psychology_triggers": ["authority", "curiosity"],
    "estimated_appeal": "medium"
  }
]"""

MOCK_MALFORMED_RESPONSE = """Here are some great video ideas:
1. Cooking tips for beginners
2. Study abroad guide
3. Visa interview preparation

Hope this helps!"""

class TestVideoIdeaGenerator:
    """Test suite for VideoIdeaGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create VideoIdeaGenerator instance for testing."""
        return VideoIdeaGenerator(api_key='test_api_key')
    
    @pytest.fixture
    def generator_no_key(self):
        """Create VideoIdeaGenerator without API key."""
        return VideoIdeaGenerator()
    
    @pytest.fixture
    def sample_keyword_data(self):
        """Sample keyword data for testing."""
        return {
            'autocomplete': [
                'cooking tips', 'cooking tutorial', 'cooking for beginners',
                'cooking recipes', 'cooking techniques'
            ],
            'trends': {
                'cooking': {
                    'avg_interest': 75.0,
                    'peak_interest': 90,
                    'related_queries': ['cooking recipes', 'cooking tips'],
                    'rising_terms': ['air fryer cooking', 'healthy cooking', 'quick cooking']
                },
                'recipes': {
                    'avg_interest': 65.0,
                    'peak_interest': 80,
                    'related_queries': ['easy recipes', 'quick recipes'],
                    'rising_terms': ['keto recipes', 'vegan recipes']
                }
            },
            'summary': {
                'highest_interest': {'keyword': 'cooking', 'avg_interest': 75.0}
            }
        }
    
    @pytest.fixture
    def sample_gap_data(self):
        """Sample gap data for testing."""
        return {
            'missing_topics': [
                {
                    'topic': 'visa_interview',
                    'competitor_videos': 15,
                    'your_videos': 0,
                    'opportunity_score': 45,
                    'sample_titles': ['Visa Interview Tips', 'How to Pass Visa Interview']
                },
                {
                    'topic': 'study_abroad',
                    'competitor_videos': 12,
                    'your_videos': 1,
                    'opportunity_score': 36,
                    'sample_titles': ['Study Abroad Guide', 'Best Countries to Study']
                }
            ],
            'frequency_gaps': [
                {
                    'topic': 'cooking_tips',
                    'your_videos': 3,
                    'competitor_videos': 12,
                    'gap_ratio': 4.0
                }
            ]
        }
    
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
            assert 'patterns' in trigger_data
            assert 'keywords' in trigger_data
            assert len(trigger_data['patterns']) >= 5
            assert len(trigger_data['keywords']) >= 3
    
    def test_goal_strategies_structure(self, generator):
        """Test goal strategies configuration."""
        expected_goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        
        for goal in expected_goals:
            assert goal in generator.goal_strategies
            strategy = generator.goal_strategies[goal]
            assert 'content_types' in strategy
            assert 'triggers' in strategy
            assert 'formats' in strategy
            assert 'cta_style' in strategy
    
    @patch('video_idea_generator.genai.GenerativeModel')
    def test_generate_ideas_with_ai_success(self, mock_model_class, generator, 
                                          sample_keyword_data, sample_gap_data, sample_strategy_views):
        """Test successful idea generation with AI."""
        # Setup mock
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = MOCK_AI_RESPONSE
        mock_model.generate_content.return_value = mock_response
        
        generator.model = mock_model
        
        # Test the function
        result = generator.generate_video_ideas(
            sample_keyword_data, sample_gap_data, sample_strategy_views, num_ideas=3
        )
        
        # Validate structure
        assert isinstance(result, list)
        assert len(result) == 3
        
        # Validate each idea
        for idea in result:
            assert isinstance(idea, dict)
            assert 'title' in idea
            assert 'brief' in idea
            assert 'target_keywords' in idea
            assert 'psychology_triggers' in idea
            assert 'call_to_action' in idea
            assert 'estimated_appeal' in idea
            
            # Validate data types
            assert isinstance(idea['title'], str)
            assert isinstance(idea['brief'], str)
            assert isinstance(idea['target_keywords'], list)
            assert isinstance(idea['psychology_triggers'], list)
            assert isinstance(idea['call_to_action'], str)
            
            # Validate content quality
            assert len(idea['title']) > 10
            assert len(idea['brief']) > 20
            assert len(idea['target_keywords']) >= 1
            assert len(idea['psychology_triggers']) >= 1
    
    def test_generate_ideas_fallback_mode(self, generator_no_key, sample_keyword_data, 
                                        sample_gap_data, sample_strategy_views):
        """Test idea generation in fallback mode (no API key)."""
        result = generator_no_key.generate_video_ideas(
            sample_keyword_data, sample_gap_data, sample_strategy_views, num_ideas=3
        )
        
        # Should still return valid structure
        assert isinstance(result, list)
        assert len(result) == 3
        
        # Validate each idea has required fields
        for idea in result:
            assert 'title' in idea
            assert 'brief' in idea
            assert 'target_keywords' in idea
            assert 'psychology_triggers' in idea
            assert 'call_to_action' in idea
    
    def test_generate_ideas_different_goals(self, generator, sample_keyword_data, sample_gap_data):
        """Test that different goals produce different types of ideas."""
        goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        results = {}
        
        for goal in goals:
            strategy = {
                'goal': goal,
                'country': 'Bangladesh',
                'audience': 'general',
                'age_range': '18-35'
            }
            
            result = generator.generate_video_ideas(
                sample_keyword_data, sample_gap_data, strategy, num_ideas=2
            )
            results[goal] = result
        
        # Different goals should produce different CTAs
        cta_texts = []
        for goal in goals:
            for idea in results[goal]:
                cta_texts.append(idea['call_to_action'].lower())
        
        # Should have variety in CTAs
        unique_ctas = set(cta_texts)
        assert len(unique_ctas) > 1
        
        # Subscribers should focus on subscription
        subscribers_ctas = [idea['call_to_action'].lower() for idea in results['subscribers']]
        assert any('subscribe' in cta for cta in subscribers_ctas)
    
    @patch('video_idea_generator.genai.GenerativeModel')
    def test_generate_ideas_ai_error_handling(self, mock_model_class, generator,
                                            sample_keyword_data, sample_gap_data, sample_strategy_views):
        """Test error handling when AI generation fails."""
        # Setup mock to raise exception
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")
        
        generator.model = mock_model
        
        result = generator.generate_video_ideas(
            sample_keyword_data, sample_gap_data, sample_strategy_views, num_ideas=3
        )
        
        # Should still return valid result using fallback
        assert isinstance(result, list)
        assert len(result) == 3
        assert all('title' in idea for idea in result)
    
    @patch('video_idea_generator.genai.GenerativeModel')
    def test_generate_ideas_malformed_ai_response(self, mock_model_class, generator,
                                                sample_keyword_data, sample_gap_data, sample_strategy_views):
        """Test handling of malformed AI response."""
        # Setup malformed mock response
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = MOCK_MALFORMED_RESPONSE
        mock_model.generate_content.return_value = mock_response
        
        generator.model = mock_model
        
        result = generator.generate_video_ideas(
            sample_keyword_data, sample_gap_data, sample_strategy_views, num_ideas=3
        )
        
        # Should fall back to template generation
        assert isinstance(result, list)
        assert len(result) == 3
        assert all('title' in idea for idea in result)
    
    def test_extract_opportunities(self, generator, sample_keyword_data, sample_gap_data, sample_strategy_views):
        """Test opportunity extraction from data."""
        opportunities = generator._extract_opportunities(sample_keyword_data, sample_gap_data, sample_strategy_views)
        
        assert isinstance(opportunities, dict)
        assert 'trending_keywords' in opportunities
        assert 'rising_terms' in opportunities
        assert 'missing_topics' in opportunities
        assert 'frequency_gaps' in opportunities
        assert 'autocomplete_suggestions' in opportunities
        assert 'high_interest_keywords' in opportunities
        
        # Should extract data from inputs
        assert len(opportunities['autocomplete_suggestions']) > 0
        assert len(opportunities['missing_topics']) > 0
        assert len(opportunities['rising_terms']) > 0
    
    def test_enhance_idea(self, generator, sample_strategy_views):
        """Test idea enhancement with psychology and CTAs."""
        basic_idea = {
            'title': 'Basic Cooking Tutorial',
            'brief': 'Learn basic cooking techniques.',
            'target_keywords': ['cooking', 'tutorial'],
            'psychology_triggers': [],
            'estimated_appeal': 'medium'
        }
        
        enhanced = generator._enhance_idea(basic_idea, sample_strategy_views)
        
        assert 'call_to_action' in enhanced
        assert 'content_type' in enhanced
        assert 'format' in enhanced
        assert len(enhanced['psychology_triggers']) > 0
        assert len(enhanced['call_to_action']) > 0
    
    def test_generate_ideas_empty_inputs(self, generator):
        """Test idea generation with empty inputs."""
        result = generator.generate_video_ideas({}, {}, {}, num_ideas=2)
        
        # Should still generate fallback ideas
        assert isinstance(result, list)
        assert len(result) == 2
        assert all('title' in idea for idea in result)
    
    def test_generate_ideas_invalid_inputs(self, generator):
        """Test idea generation with invalid inputs."""
        # Test with non-dict inputs
        result = generator.generate_video_ideas("invalid", [], "invalid", num_ideas=2)
        
        # Should handle gracefully and return fallback ideas
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_create_fallback_ideas(self, generator, sample_strategy_views):
        """Test fallback idea creation."""
        result = generator._create_fallback_ideas(sample_strategy_views, num_ideas=3)
        
        assert isinstance(result, list)
        assert len(result) == 3
        
        for idea in result:
            assert 'title' in idea
            assert 'brief' in idea
            assert 'target_keywords' in idea
            assert 'psychology_triggers' in idea
            assert 'call_to_action' in idea
            assert 'estimated_appeal' in idea


class TestUtilityFunctions:
    """Test utility functions."""
    
    @patch('video_idea_generator.VideoIdeaGenerator')
    def test_generate_video_ideas_utility(self, mock_generator_class):
        """Test generate_video_ideas utility function."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_video_ideas.return_value = [{'title': 'test'}]
        
        keyword_data = {'autocomplete': ['test']}
        gap_data = {'missing_topics': []}
        strategy = {'goal': 'views'}
        
        result = generate_video_ideas(keyword_data, gap_data, strategy, num_ideas=3)
        
        mock_generator_class.assert_called_once()
        mock_generator.generate_video_ideas.assert_called_once_with(
            keyword_data, gap_data, strategy, 3
        )
        assert result == [{'title': 'test'}]


class TestIntegration:
    """Integration tests for complete workflow."""
    
    @patch('video_idea_generator.genai.GenerativeModel')
    def test_complete_idea_generation_workflow(self, mock_model_class):
        """Test complete idea generation workflow."""
        # Setup mock
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        mock_response = Mock()
        mock_response.text = MOCK_AI_RESPONSE
        mock_model.generate_content.return_value = mock_response
        
        # Test data
        keyword_data = {
            'autocomplete': ['cooking tips', 'cooking tutorial'],
            'trends': {
                'cooking': {
                    'avg_interest': 75.0,
                    'rising_terms': ['air fryer cooking', 'healthy cooking']
                }
            }
        }
        
        gap_data = {
            'missing_topics': [
                {
                    'topic': 'visa_interview',
                    'competitor_videos': 15,
                    'your_videos': 0,
                    'opportunity_score': 45
                }
            ]
        }
        
        strategy = {
            'goal': 'subscribers',
            'country': 'Bangladesh',
            'audience': 'students',
            'age_range': '18-25'
        }
        
        # Run generation
        generator = VideoIdeaGenerator(api_key='test_key')
        generator.model = mock_model
        
        result = generator.generate_video_ideas(keyword_data, gap_data, strategy, num_ideas=3)
        
        # Validate complete result
        assert len(result) == 3
        
        for idea in result:
            # Should have all required fields
            assert 'title' in idea
            assert 'brief' in idea
            assert 'target_keywords' in idea
            assert 'psychology_triggers' in idea
            assert 'call_to_action' in idea
            assert 'estimated_appeal' in idea
            assert 'content_type' in idea
            assert 'format' in idea
            
            # Should be optimized for subscribers goal
            cta = idea['call_to_action'].lower()
            assert 'subscribe' in cta or 'join' in cta or 'community' in cta


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
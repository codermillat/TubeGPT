"""
Video Idea Generator Module for YouTube Content Strategy.

This module generates strategic video ideas by combining keyword trends,
competitor gap analysis, and psychological triggers to maximize engagement
and achieve specific channel goals.

Features:
1. Trend-based idea generation from keyword data
2. Gap-based opportunities from competitor analysis
3. Strategy-aligned content suggestions
4. Psychology trigger integration
5. Gemini AI enhancement with fallback generation
"""

import os
import json
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoIdeaGenerator:
    """
    Generates strategic video ideas combining keyword trends, competitor gaps,
    and psychological triggers for maximum engagement and goal achievement.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Video Idea Generator.
        
        Args:
            api_key (str, optional): Gemini API key. Uses GEMINI_API_KEY env var if not provided.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning(
                "Gemini API key not found. Will use fallback generation methods. "
                "Set GEMINI_API_KEY environment variable for AI-enhanced ideas."
            )
        
        # Configure Gemini if API key available
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
        
        # Psychology triggers for different goals
        self.psychology_triggers = {
            'curiosity': {
                'patterns': [
                    "What happens when you...",
                    "The secret behind...",
                    "You won't believe what...",
                    "What nobody tells you about...",
                    "The truth about...",
                    "Hidden secrets of...",
                    "What I discovered when..."
                ],
                'keywords': ['secret', 'hidden', 'truth', 'discover', 'reveal', 'mystery']
            },
            'fomo': {
                'patterns': [
                    "Before it's too late...",
                    "Don't miss out on...",
                    "Last chance to...",
                    "Everyone is doing this except you",
                    "While you still can...",
                    "Time is running out for...",
                    "Don't let this opportunity pass..."
                ],
                'keywords': ['limited', 'last chance', 'running out', 'before', 'miss out', 'opportunity']
            },
            'authority': {
                'patterns': [
                    "Expert reveals...",
                    "Professional guide to...",
                    "Master class in...",
                    "Proven method for...",
                    "Industry insider shares...",
                    "Years of experience show...",
                    "Certified expert teaches..."
                ],
                'keywords': ['expert', 'professional', 'proven', 'master', 'certified', 'insider']
            },
            'emotional': {
                'patterns': [
                    "If you've ever struggled with...",
                    "For anyone who has felt...",
                    "The emotional journey of...",
                    "Why this made me cry...",
                    "The heartbreaking truth about...",
                    "What every [audience] wishes they knew...",
                    "The pain of..."
                ],
                'keywords': ['struggle', 'emotional', 'heartbreaking', 'pain', 'journey', 'feel']
            },
            'scarcity': {
                'patterns': [
                    "Only available today...",
                    "Exclusive access to...",
                    "Limited edition...",
                    "Never before revealed...",
                    "One-time opportunity...",
                    "Rare behind-the-scenes...",
                    "First time ever..."
                ],
                'keywords': ['exclusive', 'limited', 'rare', 'first time', 'only', 'never before']
            }
        }
        
        # Goal-specific content strategies
        self.goal_strategies = {
            'views': {
                'content_types': ['viral', 'trending', 'reaction', 'challenge', 'entertainment'],
                'triggers': ['curiosity', 'fomo', 'emotional'],
                'formats': ['listicle', 'reaction', 'experiment', 'comparison', 'story'],
                'cta_style': 'engagement'
            },
            'subscribers': {
                'content_types': ['series', 'tutorial', 'behind_scenes', 'personal', 'educational'],
                'triggers': ['authority', 'emotional', 'scarcity'],
                'formats': ['tutorial', 'series', 'guide', 'personal_story', 'expertise'],
                'cta_style': 'subscription'
            },
            'engagement': {
                'content_types': ['interactive', 'q_and_a', 'community', 'discussion', 'poll'],
                'triggers': ['emotional', 'curiosity', 'fomo'],
                'formats': ['q_and_a', 'discussion', 'community_post', 'interactive', 'poll'],
                'cta_style': 'interaction'
            },
            'leads': {
                'content_types': ['educational', 'how_to', 'case_study', 'problem_solving', 'tips'],
                'triggers': ['authority', 'scarcity', 'fomo'],
                'formats': ['how_to', 'case_study', 'tips', 'guide', 'problem_solution'],
                'cta_style': 'conversion'
            },
            'sales': {
                'content_types': ['product_demo', 'testimonial', 'comparison', 'benefits', 'urgency'],
                'triggers': ['scarcity', 'authority', 'fomo'],
                'formats': ['demo', 'testimonial', 'comparison', 'benefits', 'urgency'],
                'cta_style': 'purchase'
            }
        }
        
        # CTA templates by style
        self.cta_templates = {
            'engagement': [
                "👍 LIKE if this helped you!",
                "💬 COMMENT your thoughts below!",
                "🔄 SHARE with someone who needs this!"
            ],
            'subscription': [
                "🔔 SUBSCRIBE for more exclusive content!",
                "👥 JOIN our community!",
                "📺 Don't miss future videos - SUBSCRIBE!"
            ],
            'interaction': [
                "💬 What's YOUR experience? Comment below!",
                "🤔 Which tip surprised you most?",
                "📤 SHARE your own tips!"
            ],
            'conversion': [
                "📧 Get the complete guide - link in description!",
                "🎯 Ready to take action? Check resources below!",
                "💼 Want personalized help? Let's connect!"
            ],
            'purchase': [
                "🛒 Get yours today - link in description!",
                "⏰ Limited time offer - don't wait!",
                "💰 Transform your results now!"
            ]
        }
        
        logger.info("Video Idea Generator initialized successfully")
    
    def generate_video_ideas(self, keyword_data: Dict[str, Any], gap_data: Dict[str, Any], 
                           strategy: Dict[str, Any], num_ideas: int = 5) -> List[Dict[str, Any]]:
        """
        Generate strategic video ideas combining trends, gaps, and psychology.
        
        Args:
            keyword_data (dict): Output from analyze_keywords()
            gap_data (dict): Output from compare_with_competitors()
            strategy (dict): User strategy configuration
            num_ideas (int): Number of ideas to generate
            
        Returns:
            List[dict]: List of video idea dictionaries
        """
        try:
            logger.info(f"Generating {num_ideas} video ideas for goal: {strategy.get('goal', 'views')}")
            
            # Validate inputs
            if not isinstance(keyword_data, dict):
                keyword_data = {}
            if not isinstance(gap_data, dict):
                gap_data = {}
            if not isinstance(strategy, dict):
                strategy = {'goal': 'views'}
            
            # Extract opportunity data
            opportunities = self._extract_opportunities(keyword_data, gap_data, strategy)
            
            # Generate ideas using AI or fallback
            if self.model and self.api_key:
                try:
                    ideas = self._generate_ideas_with_ai(opportunities, strategy, num_ideas)
                except Exception as e:
                    logger.warning(f"AI generation failed: {e}, using fallback")
                    ideas = self._generate_ideas_fallback(opportunities, strategy, num_ideas)
            else:
                ideas = self._generate_ideas_fallback(opportunities, strategy, num_ideas)
            
            # Enhance ideas with psychology and CTAs
            enhanced_ideas = []
            for idea in ideas[:num_ideas]:
                enhanced_idea = self._enhance_idea(idea, strategy)
                enhanced_ideas.append(enhanced_idea)
            
            logger.info(f"Successfully generated {len(enhanced_ideas)} video ideas")
            return enhanced_ideas
            
        except Exception as e:
            logger.error(f"Error generating video ideas: {e}")
            return self._create_fallback_ideas(strategy, num_ideas)
    
    def _extract_opportunities(self, keyword_data: Dict[str, Any], gap_data: Dict[str, Any], 
                             strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content opportunities from keyword and gap data."""
        opportunities = {
            'trending_keywords': [],
            'rising_terms': [],
            'missing_topics': [],
            'frequency_gaps': [],
            'autocomplete_suggestions': [],
            'high_interest_keywords': []
        }
        
        # Extract from keyword data
        if keyword_data:
            # Autocomplete suggestions
            opportunities['autocomplete_suggestions'] = keyword_data.get('autocomplete', [])
            
            # Trending and high-interest keywords
            trends = keyword_data.get('trends', {})
            for keyword, data in trends.items():
                if data.get('avg_interest', 0) > 50:
                    opportunities['high_interest_keywords'].append(keyword)
                
                # Rising terms
                rising = data.get('rising_terms', [])
                opportunities['rising_terms'].extend(rising[:3])  # Top 3 per keyword
        
        # Extract from gap data
        if gap_data:
            # Missing topics (biggest opportunities)
            missing = gap_data.get('missing_topics', [])
            opportunities['missing_topics'] = missing[:5]  # Top 5 missing topics
            
            # Frequency gaps
            freq_gaps = gap_data.get('frequency_gaps', [])
            opportunities['frequency_gaps'] = freq_gaps[:3]  # Top 3 frequency gaps
        
        return opportunities
    
    def _generate_ideas_with_ai(self, opportunities: Dict[str, Any], strategy: Dict[str, Any], 
                              num_ideas: int) -> List[Dict[str, Any]]:
        """Generate ideas using Gemini AI."""
        goal = strategy.get('goal', 'views')
        audience = strategy.get('audience', 'general')
        country = strategy.get('country', 'Global')
        age_range = strategy.get('age_range', '18-35')
        
        # Build context from opportunities
        context_parts = []
        
        if opportunities['missing_topics']:
            topics = [topic.get('topic', 'Unknown') for topic in opportunities['missing_topics'][:3]]
            context_parts.append(f"Missing content topics: {', '.join(topics)}")
        
        if opportunities['high_interest_keywords']:
            context_parts.append(f"High-interest keywords: {', '.join(opportunities['high_interest_keywords'][:5])}")
        
        if opportunities['rising_terms']:
            context_parts.append(f"Rising search terms: {', '.join(opportunities['rising_terms'][:5])}")
        
        if opportunities['autocomplete_suggestions']:
            context_parts.append(f"Popular searches: {', '.join(opportunities['autocomplete_suggestions'][:5])}")
        
        context = '\n'.join(context_parts) if context_parts else "General content opportunities"
        
        # Get goal strategy
        goal_strategy = self.goal_strategies.get(goal, self.goal_strategies['views'])
        content_types = ', '.join(goal_strategy['content_types'])
        triggers = ', '.join(goal_strategy['triggers'])
        
        prompt = f"""You are a YouTube content strategist. Generate {num_ideas} video ideas based on the following data:

GOAL: {goal} optimization
AUDIENCE: {audience} in {country} (age {age_range})
CONTENT TYPES: {content_types}
PSYCHOLOGY TRIGGERS: {triggers}

OPPORTUNITY DATA:
{context}

REQUIREMENTS:
1. Each idea should be a complete video concept
2. Include compelling titles with psychological hooks
3. Brief 1-2 sentence descriptions
4. Target specific keywords from the data
5. Consider the {country} audience and {audience} interests
6. Align with {goal} optimization strategy

OUTPUT FORMAT (JSON):
[
  {{
    "title": "Compelling video title with hook",
    "brief": "1-2 sentence description of video content and value",
    "target_keywords": ["keyword1", "keyword2", "keyword3"],
    "psychology_triggers": ["curiosity", "fomo"],
    "estimated_appeal": "high/medium/low"
  }}
]

Generate {num_ideas} strategic video ideas:"""
        
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                # Try to parse JSON response
                response_text = response.text.strip()
                
                # Extract JSON array
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
                    ideas = json.loads(json_text)
                    
                    if isinstance(ideas, list) and len(ideas) > 0:
                        return ideas[:num_ideas]
            
            # If parsing failed, use fallback
            return self._generate_ideas_fallback(opportunities, strategy, num_ideas)
            
        except Exception as e:
            logger.error(f"AI idea generation error: {e}")
            return self._generate_ideas_fallback(opportunities, strategy, num_ideas)
    
    def _generate_ideas_fallback(self, opportunities: Dict[str, Any], strategy: Dict[str, Any], 
                               num_ideas: int) -> List[Dict[str, Any]]:
        """Generate ideas using fallback templates."""
        goal = strategy.get('goal', 'views')
        audience = strategy.get('audience', 'general')
        goal_strategy = self.goal_strategies.get(goal, self.goal_strategies['views'])
        
        ideas = []
        
        # Template-based idea generation
        templates = {
            'missing_topic': {
                'title': "Complete Guide to {topic} - Everything You Need to Know",
                'brief': "Comprehensive tutorial covering {topic} from basics to advanced techniques.",
                'triggers': ['authority', 'curiosity']
            },
            'trending_keyword': {
                'title': "Why Everyone is Talking About {keyword} Right Now",
                'brief': "Explore the trending topic of {keyword} and what it means for {audience}.",
                'triggers': ['fomo', 'curiosity']
            },
            'gap_opportunity': {
                'title': "What Nobody Tells You About {topic}",
                'brief': "Uncover hidden insights about {topic} that competitors aren't sharing.",
                'triggers': ['curiosity', 'scarcity']
            },
            'rising_term': {
                'title': "The Future of {term} - What You Need to Know",
                'brief': "Stay ahead of the curve with insights into the emerging trend of {term}.",
                'triggers': ['authority', 'fomo']
            },
            'how_to': {
                'title': "How to Master {skill} in 30 Days",
                'brief': "Step-by-step guide to quickly develop {skill} with proven methods.",
                'triggers': ['authority', 'scarcity']
            }
        }
        
        # Generate ideas from missing topics
        for topic_data in opportunities.get('missing_topics', [])[:2]:
            topic = topic_data.get('topic', 'Unknown').replace('_', ' ').title()
            template = templates['missing_topic']
            
            idea = {
                'title': template['title'].format(topic=topic),
                'brief': template['brief'].format(topic=topic, audience=audience),
                'target_keywords': [topic.lower(), f"{topic} guide", f"{topic} tutorial"],
                'psychology_triggers': template['triggers'],
                'estimated_appeal': 'high'
            }
            ideas.append(idea)
        
        # Generate ideas from high-interest keywords
        for keyword in opportunities.get('high_interest_keywords', [])[:2]:
            template = templates['trending_keyword']
            
            idea = {
                'title': template['title'].format(keyword=keyword),
                'brief': template['brief'].format(keyword=keyword, audience=audience),
                'target_keywords': [keyword, f"{keyword} trend", f"{keyword} explained"],
                'psychology_triggers': template['triggers'],
                'estimated_appeal': 'high'
            }
            ideas.append(idea)
        
        # Generate ideas from rising terms
        for term in opportunities.get('rising_terms', [])[:2]:
            template = templates['rising_term']
            
            idea = {
                'title': template['title'].format(term=term),
                'brief': template['brief'].format(term=term),
                'target_keywords': [term, f"{term} future", f"{term} trend"],
                'psychology_triggers': template['triggers'],
                'estimated_appeal': 'medium'
            }
            ideas.append(idea)
        
        # Fill remaining slots with general ideas
        while len(ideas) < num_ideas:
            general_topics = ['productivity', 'success', 'motivation', 'learning', 'growth']
            topic = random.choice(general_topics)
            template = templates['how_to']
            
            idea = {
                'title': template['title'].format(skill=topic),
                'brief': template['brief'].format(skill=topic),
                'target_keywords': [topic, f"{topic} tips", f"improve {topic}"],
                'psychology_triggers': template['triggers'],
                'estimated_appeal': 'medium'
            }
            ideas.append(idea)
        
        return ideas[:num_ideas]
    
    def _enhance_idea(self, idea: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance idea with psychology triggers and CTAs."""
        goal = strategy.get('goal', 'views')
        goal_strategy = self.goal_strategies.get(goal, self.goal_strategies['views'])
        
        # Ensure required fields exist
        enhanced_idea = {
            'title': idea.get('title', 'Untitled Video'),
            'brief': idea.get('brief', 'Video description not available.'),
            'target_keywords': idea.get('target_keywords', []),
            'psychology_triggers': idea.get('psychology_triggers', []),
            'call_to_action': '',
            'estimated_appeal': idea.get('estimated_appeal', 'medium'),
            'content_type': random.choice(goal_strategy['content_types']),
            'format': random.choice(goal_strategy['formats'])
        }
        
        # Add appropriate CTA
        cta_style = goal_strategy['cta_style']
        cta_options = self.cta_templates.get(cta_style, self.cta_templates['engagement'])
        enhanced_idea['call_to_action'] = random.choice(cta_options)
        
        # Ensure psychology triggers are from our defined set
        if not enhanced_idea['psychology_triggers']:
            enhanced_idea['psychology_triggers'] = random.sample(
                goal_strategy['triggers'], 
                min(2, len(goal_strategy['triggers']))
            )
        
        return enhanced_idea
    
    def _create_fallback_ideas(self, strategy: Dict[str, Any], num_ideas: int) -> List[Dict[str, Any]]:
        """Create basic fallback ideas when all else fails."""
        goal = strategy.get('goal', 'views')
        audience = strategy.get('audience', 'general')
        
        fallback_ideas = [
            {
                'title': f'Ultimate Guide for {audience.title()}s - Everything You Need',
                'brief': f'Comprehensive guide covering essential topics for {audience}s.',
                'target_keywords': [audience, 'guide', 'tutorial'],
                'psychology_triggers': ['authority', 'curiosity'],
                'call_to_action': '👍 LIKE if this helped you!',
                'estimated_appeal': 'medium',
                'content_type': 'educational',
                'format': 'guide'
            },
            {
                'title': 'What Nobody Tells You About Success',
                'brief': 'Uncover hidden truths about achieving success that others won\'t share.',
                'target_keywords': ['success', 'secrets', 'tips'],
                'psychology_triggers': ['curiosity', 'scarcity'],
                'call_to_action': '🔔 SUBSCRIBE for more exclusive content!',
                'estimated_appeal': 'high',
                'content_type': 'motivational',
                'format': 'story'
            },
            {
                'title': 'Before It\'s Too Late - Important Message',
                'brief': 'Time-sensitive insights that could change your perspective.',
                'target_keywords': ['important', 'message', 'urgent'],
                'psychology_triggers': ['fomo', 'emotional'],
                'call_to_action': '💬 COMMENT your thoughts below!',
                'estimated_appeal': 'medium',
                'content_type': 'personal',
                'format': 'message'
            }
        ]
        
        # Repeat and shuffle to fill requested number
        while len(fallback_ideas) < num_ideas:
            fallback_ideas.extend(fallback_ideas[:num_ideas - len(fallback_ideas)])
        
        return fallback_ideas[:num_ideas]

# Utility functions for easy integration

def generate_video_ideas(keyword_data: Dict[str, Any], gap_data: Dict[str, Any], 
                        strategy: Dict[str, Any], num_ideas: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to generate video ideas.
    
    Args:
        keyword_data (dict): Output from analyze_keywords()
        gap_data (dict): Output from compare_with_competitors()
        strategy (dict): User strategy configuration
        num_ideas (int): Number of ideas to generate
        
    Returns:
        List[dict]: List of video idea dictionaries
    """
    generator = VideoIdeaGenerator()
    return generator.generate_video_ideas(keyword_data, gap_data, strategy, num_ideas)

def main():
    """
    Example usage of the Video Idea Generator.
    """
    try:
        # Example keyword data
        keyword_data = {
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
        
        # Example gap data
        gap_data = {
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
        
        # Example strategy
        strategy = {
            'goal': 'subscribers',
            'country': 'Bangladesh',
            'audience': 'students',
            'age_range': '18-25'
        }
        
        print("Video Idea Generator Example")
        print("=" * 40)
        
        # Generate ideas
        generator = VideoIdeaGenerator()
        ideas = generator.generate_video_ideas(keyword_data, gap_data, strategy, num_ideas=5)
        
        # Display results
        print(f"\n🎯 GENERATED {len(ideas)} VIDEO IDEAS")
        print(f"Goal: {strategy['goal']} | Audience: {strategy['audience']} | Country: {strategy['country']}")
        
        for i, idea in enumerate(ideas, 1):
            print(f"\n📹 IDEA {i}:")
            print(f"Title: {idea['title']}")
            print(f"Brief: {idea['brief']}")
            print(f"Keywords: {', '.join(idea['target_keywords'])}")
            print(f"Psychology: {', '.join(idea['psychology_triggers'])}")
            print(f"CTA: {idea['call_to_action']}")
            print(f"Appeal: {idea['estimated_appeal']}")
            print(f"Type: {idea.get('content_type', 'N/A')} | Format: {idea.get('format', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()
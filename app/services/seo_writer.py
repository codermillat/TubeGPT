"""
SEO Writer Module for YouTube Content Optimization.

This module generates SEO-optimized metadata for YouTube videos using:
1. Keyword data from keyword_analyzer.py
2. Strategy configuration from strategy_config.json
3. Gemini AI for content generation with psychological triggers

Features:
- Psychology-aware title generation (curiosity, FOMO, authority, scarcity)
- SEO-optimized descriptions with emotional triggers
- Relevant tag generation based on keyword research
- Thumbnail text suggestions with strong hooks
- Strategy-based customization for different goals
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SEOWriter:
    """
    SEO content writer for YouTube metadata generation.
    
    Uses Gemini AI with psychological triggers and keyword optimization
    to create compelling titles, descriptions, tags, and thumbnail text.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SEO Writer.
        
        Args:
            api_key (str, optional): Gemini API key. Uses GEMINI_API_KEY env var if not provided.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please set GEMINI_API_KEY environment variable "
                "or pass it as a parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Psychology triggers for content optimization
        self.psychology_triggers = {
            'curiosity': [
                "You won't believe what happens when...",
                "What happens when...",
                "The secret behind...",
                "What nobody tells you about...",
                "The truth about...",
                "What I discovered when...",
                "The surprising reason why..."
            ],
            'fomo': [
                "Before it's too late",
                "Don't miss out on...",
                "Last chance to...",
                "Everyone is talking about...",
                "While you still can",
                "Before everyone else finds out",
                "Limited time only"
            ],
            'authority': [
                "Expert reveals...",
                "Doctor explains...",
                "Professional guide to...",
                "Master class in...",
                "Proven method for...",
                "Scientific approach to...",
                "Industry insider shares..."
            ],
            'scarcity': [
                "Only today",
                "Limited time",
                "Exclusive access",
                "Never before revealed",
                "One-time opportunity",
                "While supplies last",
                "Secret method"
            ],
            'relatability': [
                "If you're struggling with...",
                "For anyone who has ever...",
                "We've all been there...",
                "Every [audience] needs to know...",
                "The problem we all face...",
                "What every [audience] wishes they knew",
                "If you're like me..."
            ]
        }
        
        logger.info("SEO Writer initialized successfully")
    
    def _build_seo_prompt(self, topic: str, keyword_data: Dict[str, Any], 
                         strategy: Dict[str, Any]) -> str:
        """
        Build a comprehensive prompt for Gemini to generate SEO metadata.
        
        Args:
            topic (str): Video topic or seed phrase
            keyword_data (dict): Output from analyze_keywords()
            strategy (dict): Strategy configuration
            
        Returns:
            str: Formatted prompt for Gemini
        """
        # Extract key information
        autocomplete = keyword_data.get('autocomplete', [])
        trends = keyword_data.get('trends', {})
        summary = keyword_data.get('summary', {})
        
        # Get top keywords from trends data
        top_keywords = []
        if trends:
            # Sort keywords by average interest
            sorted_keywords = sorted(
                trends.items(), 
                key=lambda x: x[1].get('avg_interest', 0), 
                reverse=True
            )
            top_keywords = [kw for kw, _ in sorted_keywords[:7]]
        
        # Build keyword context
        keyword_context = f"Primary Keywords: {', '.join(top_keywords[:5])}\n"
        if autocomplete:
            keyword_context += f"YouTube Suggestions: {', '.join(autocomplete[:5])}\n"
        
        # Add trending terms
        all_rising_terms = []
        for kw_data in trends.values():
            all_rising_terms.extend(kw_data.get('rising_terms', []))
        if all_rising_terms:
            unique_rising = list(set(all_rising_terms))[:5]
            keyword_context += f"Trending Terms: {', '.join(unique_rising)}\n"
        
        # Strategy context
        goal = strategy.get('goal', 'views')
        country = strategy.get('country', 'Global')
        audience = strategy.get('audience', 'general')
        age_range = strategy.get('age_range', '18-35')
        
        strategy_context = f"""
Goal: {goal}
Target Country: {country}
Audience: {audience}
Age Range: {age_range}
Main Keywords: {', '.join(strategy.get('main_keywords', []))}
"""
        
        # Psychology triggers context
        triggers_text = """
PSYCHOLOGY TRIGGERS TO USE:
- Curiosity: "You won't believe...", "What happens when...", "The secret behind..."
- FOMO: "Before it's too late", "Don't miss out", "Everyone is talking about..."
- Authority: "Expert reveals...", "Proven method", "Professional guide"
- Scarcity: "Limited time", "Exclusive access", "Never before revealed"
- Relatability: "If you're struggling with...", "We've all been there..."
"""
        
        # Goal-specific instructions
        goal_instructions = {
            'views': 'Focus on viral potential, emotional hooks, and broad appeal',
            'subscribers': 'Emphasize channel value, consistent content, and community building',
            'engagement': 'Encourage comments, questions, and interaction',
            'leads': 'Include clear value propositions and call-to-actions',
            'sales': 'Focus on benefits, solutions, and conversion-oriented language'
        }
        
        goal_instruction = goal_instructions.get(goal, goal_instructions['views'])
        
        prompt = f"""You are a YouTube SEO expert and content strategist. Create optimized metadata for a video about "{topic}".

KEYWORD DATA:
{keyword_context}

STRATEGY:
{strategy_context}
Goal-specific focus: {goal_instruction}

{triggers_text}

REQUIREMENTS:
1. TITLES (3 options):
   - Use psychology triggers (curiosity, FOMO, authority, scarcity)
   - Include primary keywords naturally
   - 60 characters or less
   - Each title should use a different psychological approach
   - Make them click-worthy but not clickbait

2. TAGS (10-15 tags):
   - Mix of broad and specific keywords
   - Include trending terms from keyword data
   - Consider {country} audience if relevant
   - Use both single words and phrases

3. DESCRIPTION (150-200 words):
   - Strong hook in first 2 lines
   - Include primary keywords naturally (don't stuff)
   - Add emotional triggers and benefits
   - Include relevant call-to-action for {goal}
   - End with engagement prompt (like, subscribe, comment)

4. THUMBNAIL_TEXT (3 options):
   - 3-5 words maximum each
   - High contrast, readable text
   - Use power words and emotional triggers
   - Different approaches: question, benefit, curiosity

COUNTRY/AUDIENCE CONSIDERATIONS:
- Adapt language and references for {country} audience
- Consider {age_range} age group preferences
- Use culturally relevant examples if applicable

OUTPUT FORMAT (JSON):
{{
  "titles": ["title1", "title2", "title3"],
  "tags": ["tag1", "tag2", ...],
  "description": "full description text",
  "thumbnail_text": ["text1", "text2", "text3"]
}}

Generate compelling, SEO-optimized content that balances psychology, keywords, and strategy goals."""
        
        return prompt
    
    def generate_seo_metadata(self, topic: str, keyword_data: Dict[str, Any], 
                            strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SEO-optimized metadata for YouTube videos.
        
        Args:
            topic (str): Video topic or seed phrase
            keyword_data (dict): Output from analyze_keywords()
            strategy (dict): Strategy configuration
            
        Returns:
            dict: SEO metadata with titles, tags, description, thumbnail_text
        """
        try:
            logger.info(f"Generating SEO metadata for topic: '{topic}'")
            
            # Build the prompt
            prompt = self._build_seo_prompt(topic, keyword_data, strategy)
            
            # Get response from Gemini
            logger.info("Sending request to Gemini Pro...")
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                response_text = response.text.strip()
                
                # Find JSON block
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("No JSON found in response")
                
                json_text = response_text[start_idx:end_idx]
                metadata = json.loads(json_text)
                
                # Validate required fields
                required_fields = ['titles', 'tags', 'description', 'thumbnail_text']
                for field in required_fields:
                    if field not in metadata:
                        raise ValueError(f"Missing required field: {field}")
                
                # Validate data types and lengths
                if not isinstance(metadata['titles'], list) or len(metadata['titles']) != 3:
                    raise ValueError("Titles must be a list of 3 items")
                
                if not isinstance(metadata['tags'], list) or not (10 <= len(metadata['tags']) <= 15):
                    logger.warning(f"Tags count ({len(metadata['tags'])}) outside recommended range 10-15")
                
                if not isinstance(metadata['description'], str) or len(metadata['description']) < 100:
                    logger.warning(f"Description length ({len(metadata['description'])}) below recommended 150-200 words")
                
                if not isinstance(metadata['thumbnail_text'], list) or len(metadata['thumbnail_text']) != 3:
                    raise ValueError("Thumbnail text must be a list of 3 items")
                
                logger.info("Successfully generated SEO metadata")
                return metadata
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Raw response: {response.text}")
                
                # Fallback: create basic metadata
                return self._create_fallback_metadata(topic, keyword_data, strategy)
                
        except Exception as e:
            logger.error(f"Error generating SEO metadata: {e}")
            return self._create_fallback_metadata(topic, keyword_data, strategy)
    
    def _create_fallback_metadata(self, topic: str, keyword_data: Dict[str, Any], 
                                 strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create basic fallback metadata when AI generation fails.
        
        Args:
            topic (str): Video topic
            keyword_data (dict): Keyword data
            strategy (dict): Strategy configuration
            
        Returns:
            dict: Basic metadata structure
        """
        logger.info("Creating fallback metadata")
        
        # Extract keywords
        autocomplete = keyword_data.get('autocomplete', [])
        main_keywords = strategy.get('main_keywords', [])
        
        # Basic titles with psychology triggers
        titles = [
            f"The Ultimate Guide to {topic} - You Need to See This!",
            f"What Nobody Tells You About {topic} (Shocking Results)",
            f"How to Master {topic} - Expert Tips Revealed"
        ]
        
        # Basic tags
        tags = [topic.lower()]
        if autocomplete:
            tags.extend(autocomplete[:8])
        if main_keywords:
            tags.extend(main_keywords)
        tags = list(set(tags))[:12]  # Remove duplicates and limit
        
        # Basic description
        description = f"""Discover everything you need to know about {topic} in this comprehensive guide!
        
In this video, you'll learn:
- Key insights about {topic}
- Practical tips you can use immediately
- Expert strategies that actually work

Don't forget to LIKE this video if it helped you, SUBSCRIBE for more content like this, and COMMENT below with your questions!

#{'#'.join(tags[:5])}"""
        
        # Basic thumbnail text
        thumbnail_text = [
            "ULTIMATE GUIDE",
            "SHOCKING TRUTH",
            "EXPERT TIPS"
        ]
        
        return {
            'titles': titles,
            'tags': tags,
            'description': description,
            'thumbnail_text': thumbnail_text
        }

def load_strategy(config_path: str = 'strategy_config.json') -> Dict[str, Any]:
    """
    Load and validate strategy configuration from JSON file.
    
    Args:
        config_path (str): Path to strategy configuration file
        
    Returns:
        dict: Validated strategy configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Strategy config file not found: {config_path}")
            # Return default strategy
            return {
                'goal': 'views',
                'country': 'Global',
                'audience': 'general',
                'age_range': '18-35',
                'main_keywords': []
            }
        
        with open(config_file, 'r', encoding='utf-8') as f:
            strategy = json.load(f)
        
        # Validate required fields
        required_fields = ['goal', 'country', 'audience', 'age_range']
        for field in required_fields:
            if field not in strategy:
                logger.warning(f"Missing required field '{field}' in strategy config")
                strategy[field] = _get_default_value(field)
        
        # Validate goal
        valid_goals = ['views', 'subscribers', 'engagement', 'leads', 'sales']
        if strategy['goal'] not in valid_goals:
            logger.warning(f"Invalid goal '{strategy['goal']}', using 'views'")
            strategy['goal'] = 'views'
        
        # Ensure main_keywords is a list
        if 'main_keywords' not in strategy:
            strategy['main_keywords'] = []
        elif not isinstance(strategy['main_keywords'], list):
            strategy['main_keywords'] = []
        
        logger.info(f"Loaded strategy config: {strategy['goal']} goal for {strategy['country']} audience")
        return strategy
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in strategy config: {e}")
        raise ValueError(f"Invalid JSON in strategy config: {e}")
    except Exception as e:
        logger.error(f"Error loading strategy config: {e}")
        raise

def _get_default_value(field: str) -> str:
    """Get default value for missing strategy fields."""
    defaults = {
        'goal': 'views',
        'country': 'Global',
        'audience': 'general',
        'age_range': '18-35'
    }
    return defaults.get(field, '')

def main():
    """
    Example usage of the SEO Writer.
    """
    try:
        # Load strategy
        strategy = load_strategy()
        print(f"Loaded strategy: {strategy}")
        
        # Example keyword data (would come from keyword_analyzer.py)
        keyword_data = {
            'autocomplete': [
                'cooking recipes', 'cooking tips', 'cooking tutorial',
                'cooking channel', 'cooking show'
            ],
            'trends': {
                'cooking': {
                    'avg_interest': 65.0,
                    'peak_interest': 80,
                    'related_queries': ['cooking recipes', 'cooking methods'],
                    'rising_terms': ['air fryer cooking', 'healthy cooking']
                },
                'recipes': {
                    'avg_interest': 55.0,
                    'peak_interest': 70,
                    'related_queries': ['easy recipes', 'quick recipes'],
                    'rising_terms': ['keto recipes', 'vegan recipes']
                }
            },
            'summary': {
                'highest_interest': {'keyword': 'cooking', 'avg_interest': 65.0}
            }
        }
        
        # Initialize SEO Writer
        writer = SEOWriter()
        
        # Generate metadata
        topic = "Traditional Bengali Cooking Techniques"
        metadata = writer.generate_seo_metadata(topic, keyword_data, strategy)
        
        # Display results
        print(f"\n🎯 SEO METADATA for '{topic}'")
        print("=" * 50)
        
        print(f"\n📝 TITLES:")
        for i, title in enumerate(metadata['titles'], 1):
            print(f"  {i}. {title}")
        
        print(f"\n🏷️  TAGS ({len(metadata['tags'])}):")
        print(f"  {', '.join(metadata['tags'])}")
        
        print(f"\n📄 DESCRIPTION ({len(metadata['description'])} chars):")
        print(f"  {metadata['description']}")
        
        print(f"\n🖼️  THUMBNAIL TEXT:")
        for i, text in enumerate(metadata['thumbnail_text'], 1):
            print(f"  {i}. {text}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()
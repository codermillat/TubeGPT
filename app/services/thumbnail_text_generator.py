"""
Thumbnail Text Generator Module for YouTube Content Optimization.

This module generates psychology-driven thumbnail overlay text that maximizes
click-through rates using proven marketing triggers and power words.

Features:
1. Psychology-based text generation (FOMO, curiosity, authority, emotional, scarcity)
2. Power word integration for maximum impact
3. Gemini AI enhancement with fallback generation
4. Strategy-aligned optimization for different goals
5. Typography-aware text length optimization (5-6 words max)
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThumbnailTextGenerator:
    """
    Generates psychology-driven thumbnail overlay text for YouTube videos.
    
    Creates short, punchy text overlays that use psychological triggers
    and power words to maximize click-through rates and engagement.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Thumbnail Text Generator.
        
        Args:
            api_key (str, optional): Gemini API key. Uses GEMINI_API_KEY env var if not provided.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning(
                "Gemini API key not found. Will use fallback generation methods. "
                "Set GEMINI_API_KEY environment variable for AI-enhanced text generation."
            )
        
        # Configure Gemini if API key available
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
        
        # Psychology triggers with thumbnail-optimized templates
        self.psychology_triggers = {
            'curiosity': {
                'templates': [
                    "FIND OUT WHY",
                    "SEE WHAT HAPPENS",
                    "YOU WON'T BELIEVE",
                    "SHOCKING TRUTH",
                    "HIDDEN SECRET",
                    "WHAT HAPPENS NEXT",
                    "MYSTERY REVEALED"
                ],
                'power_words': ['SECRET', 'HIDDEN', 'TRUTH', 'REVEALED', 'SHOCKING', 'MYSTERY']
            },
            'fomo': {
                'templates': [
                    "LIMITED TIME",
                    "DON'T MISS OUT",
                    "BEFORE IT'S GONE",
                    "LAST CHANCE",
                    "RUNNING OUT",
                    "ACT NOW",
                    "TIME SENSITIVE"
                ],
                'power_words': ['LIMITED', 'LAST', 'NOW', 'URGENT', 'QUICK', 'FAST']
            },
            'authority': {
                'templates': [
                    "EXPERT TIPS",
                    "PRO GUIDE",
                    "OFFICIAL METHOD",
                    "PROVEN SYSTEM",
                    "MASTER CLASS",
                    "INSIDER SECRETS",
                    "PROFESSIONAL ADVICE"
                ],
                'power_words': ['EXPERT', 'PRO', 'MASTER', 'PROVEN', 'OFFICIAL', 'INSIDER']
            },
            'emotional': {
                'templates': [
                    "WE'VE ALL BEEN THERE",
                    "YOU'RE NOT ALONE",
                    "FINALLY UNDERSTAND",
                    "FEEL BETTER NOW",
                    "OVERCOME THIS",
                    "BREAKTHROUGH MOMENT",
                    "LIFE CHANGING"
                ],
                'power_words': ['FEEL', 'OVERCOME', 'BREAKTHROUGH', 'LIFE', 'FINALLY', 'UNDERSTAND']
            },
            'scarcity': {
                'templates': [
                    "ONLY TODAY",
                    "EXCLUSIVE ACCESS",
                    "RARE OPPORTUNITY",
                    "FIRST TIME EVER",
                    "NEVER SEEN BEFORE",
                    "SPECIAL EDITION",
                    "VIP ONLY"
                ],
                'power_words': ['ONLY', 'EXCLUSIVE', 'RARE', 'SPECIAL', 'VIP', 'FIRST']
            }
        }
        
        # Universal power words for maximum impact
        self.power_words = [
            'YOU', 'NOW', 'NEW', 'FREE', 'INSTANT', 'AMAZING', 'INCREDIBLE',
            'ULTIMATE', 'BEST', 'TOP', 'GUARANTEED', 'PROVEN', 'EASY',
            'QUICK', 'FAST', 'SIMPLE', 'POWERFUL', 'EFFECTIVE', 'RESULTS'
        ]
        
        # Goal-specific optimization strategies
        self.goal_strategies = {
            'views': {
                'primary_triggers': ['curiosity', 'fomo', 'emotional'],
                'style': 'viral',
                'emphasis': 'broad_appeal'
            },
            'subscribers': {
                'primary_triggers': ['authority', 'emotional', 'scarcity'],
                'style': 'trustworthy',
                'emphasis': 'value_proposition'
            },
            'engagement': {
                'primary_triggers': ['emotional', 'curiosity', 'fomo'],
                'style': 'interactive',
                'emphasis': 'conversation_starter'
            },
            'leads': {
                'primary_triggers': ['authority', 'scarcity', 'fomo'],
                'style': 'professional',
                'emphasis': 'credibility'
            },
            'sales': {
                'primary_triggers': ['scarcity', 'authority', 'fomo'],
                'style': 'persuasive',
                'emphasis': 'urgency'
            }
        }
        
        logger.info("Thumbnail Text Generator initialized successfully")
    
    def generate_thumbnail_texts(self, ideas: List[Dict[str, Any]], strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate thumbnail overlay texts for video ideas.
        
        Args:
            ideas (List[dict]): Output from generate_video_ideas()
            strategy (dict): User strategy configuration
            
        Returns:
            List[dict]: Enhanced ideas with thumbnail_texts added
        """
        try:
            logger.info(f"Generating thumbnail texts for {len(ideas)} video ideas")
            
            # Validate inputs
            if not isinstance(ideas, list):
                raise ValueError("Ideas must be a list")
            if not isinstance(strategy, dict):
                strategy = {'goal': 'views'}
            
            enhanced_ideas = []
            
            for i, idea in enumerate(ideas):
                try:
                    # Generate thumbnail texts for this idea
                    if self.model and self.api_key:
                        try:
                            thumbnail_texts = self._generate_texts_with_ai(idea, strategy)
                        except Exception as e:
                            logger.warning(f"AI generation failed for idea {i+1}: {e}, using fallback")
                            thumbnail_texts = self._generate_texts_fallback(idea, strategy)
                    else:
                        thumbnail_texts = self._generate_texts_fallback(idea, strategy)
                    
                    # Add thumbnail texts to the idea
                    enhanced_idea = idea.copy()
                    enhanced_idea['thumbnail_texts'] = thumbnail_texts
                    enhanced_ideas.append(enhanced_idea)
                    
                except Exception as e:
                    logger.error(f"Error processing idea {i+1}: {e}")
                    # Add fallback thumbnail texts
                    enhanced_idea = idea.copy()
                    enhanced_idea['thumbnail_texts'] = self._create_emergency_fallback()
                    enhanced_ideas.append(enhanced_idea)
            
            logger.info(f"Successfully generated thumbnail texts for {len(enhanced_ideas)} ideas")
            return enhanced_ideas
            
        except Exception as e:
            logger.error(f"Error in generate_thumbnail_texts: {e}")
            # Return original ideas with emergency fallback texts
            return self._add_emergency_fallbacks(ideas)
    
    def _generate_texts_with_ai(self, idea: Dict[str, Any], strategy: Dict[str, Any]) -> List[str]:
        """Generate thumbnail texts using Gemini AI."""
        title = idea.get('title', 'Video Title')
        keywords = idea.get('target_keywords', [])
        triggers = idea.get('psychology_triggers', [])
        goal = strategy.get('goal', 'views')
        audience = strategy.get('audience', 'general')
        
        # Get goal strategy
        goal_strategy = self.goal_strategies.get(goal, self.goal_strategies['views'])
        primary_triggers = goal_strategy['primary_triggers']
        
        # Build trigger examples
        trigger_examples = []
        for trigger in primary_triggers:
            if trigger in self.psychology_triggers:
                examples = self.psychology_triggers[trigger]['templates'][:3]
                trigger_examples.append(f"{trigger.title()}: {', '.join(examples)}")
        
        prompt = f"""You are a YouTube thumbnail text expert specializing in high-converting overlay text.

VIDEO TITLE: "{title}"
TARGET KEYWORDS: {', '.join(keywords[:5])}
PSYCHOLOGY TRIGGERS: {', '.join(triggers)}
GOAL: {goal} optimization
AUDIENCE: {audience}

PSYCHOLOGY TRIGGER EXAMPLES:
{chr(10).join(trigger_examples)}

REQUIREMENTS:
1. Generate 3 thumbnail overlay texts
2. Maximum 5-6 words each
3. Use UPPERCASE for impact
4. Include power words: {', '.join(self.power_words[:10])}
5. Each text should use different psychological triggers
6. Make them readable at small thumbnail sizes
7. Focus on {goal_strategy['emphasis']}

POWER WORDS TO PRIORITIZE:
YOU, NOW, NEW, FREE, AMAZING, ULTIMATE, PROVEN, EASY, QUICK, RESULTS

OUTPUT FORMAT:
1. [Text 1]
2. [Text 2]  
3. [Text 3]

Generate 3 high-impact thumbnail texts:"""
        
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                # Parse the response
                lines = response.text.strip().split('\n')
                thumbnail_texts = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith(('1.', '2.', '3.')) or line.startswith('-')):
                        # Extract text after number/bullet
                        text = re.sub(r'^[\d\-\.\s]+', '', line).strip()
                        if text and len(text.split()) <= 6:
                            thumbnail_texts.append(text.upper())
                
                if len(thumbnail_texts) >= 2:
                    return thumbnail_texts[:3]  # Return up to 3 texts
            
            # If parsing failed, use fallback
            return self._generate_texts_fallback(idea, strategy)
            
        except Exception as e:
            logger.error(f"AI thumbnail text generation error: {e}")
            return self._generate_texts_fallback(idea, strategy)
    
    def _generate_texts_fallback(self, idea: Dict[str, Any], strategy: Dict[str, Any]) -> List[str]:
        """Generate thumbnail texts using fallback templates."""
        title = idea.get('title', 'Video Title')
        triggers = idea.get('psychology_triggers', [])
        goal = strategy.get('goal', 'views')
        
        # Get goal strategy
        goal_strategy = self.goal_strategies.get(goal, self.goal_strategies['views'])
        primary_triggers = goal_strategy['primary_triggers']
        
        thumbnail_texts = []
        
        # Generate text for each primary trigger
        for i, trigger in enumerate(primary_triggers[:3]):
            if trigger in self.psychology_triggers:
                trigger_data = self.psychology_triggers[trigger]
                templates = trigger_data['templates']
                power_words = trigger_data['power_words']
                
                # Choose template based on index to ensure variety
                template = templates[i % len(templates)]
                
                # Try to incorporate title keywords
                title_words = title.upper().split()
                key_word = None
                
                # Find a good keyword from title
                for word in title_words:
                    if len(word) > 3 and word not in ['THE', 'AND', 'FOR', 'WITH', 'THIS', 'THAT']:
                        key_word = word
                        break
                
                # Create text based on template and context
                if key_word and len(f"{template} {key_word}".split()) <= 6:
                    text = f"{template} {key_word}"
                else:
                    text = template
                
                thumbnail_texts.append(text)
            else:
                # Generic fallback
                generic_texts = ["AMAZING RESULTS", "YOU NEED THIS", "WATCH NOW"]
                thumbnail_texts.append(generic_texts[i % len(generic_texts)])
        
        # Ensure we have exactly 3 texts
        while len(thumbnail_texts) < 3:
            fallback_options = [
                "INCREDIBLE TIPS",
                "MUST WATCH",
                "GAME CHANGER",
                "LIFE HACK",
                "PRO SECRETS"
            ]
            thumbnail_texts.append(fallback_options[len(thumbnail_texts) % len(fallback_options)])
        
        return thumbnail_texts[:3]
    
    def _create_emergency_fallback(self) -> List[str]:
        """Create emergency fallback thumbnail texts."""
        return [
            "AMAZING RESULTS",
            "YOU NEED THIS",
            "WATCH NOW"
        ]
    
    def _add_emergency_fallbacks(self, ideas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add emergency fallback texts to all ideas."""
        enhanced_ideas = []
        
        for idea in ideas:
            enhanced_idea = idea.copy()
            enhanced_idea['thumbnail_texts'] = self._create_emergency_fallback()
            enhanced_ideas.append(enhanced_idea)
        
        return enhanced_ideas
    
    def validate_thumbnail_texts(self, ideas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate thumbnail texts for quality and compliance.
        
        Args:
            ideas (List[dict]): Ideas with thumbnail_texts
            
        Returns:
            dict: Validation report with quality metrics
        """
        try:
            validation_report = {
                'total_ideas': len(ideas),
                'valid_texts': 0,
                'power_word_coverage': 0,
                'trigger_coverage': 0,
                'length_compliance': 0,
                'issues': []
            }
            
            for i, idea in enumerate(ideas):
                thumbnail_texts = idea.get('thumbnail_texts', [])
                
                if len(thumbnail_texts) == 3:
                    validation_report['valid_texts'] += 1
                else:
                    validation_report['issues'].append(f"Idea {i+1}: Expected 3 texts, got {len(thumbnail_texts)}")
                
                # Check for power words
                has_power_word = False
                for text in thumbnail_texts:
                    if any(word in text.upper() for word in self.power_words):
                        has_power_word = True
                        break
                
                if has_power_word:
                    validation_report['power_word_coverage'] += 1
                
                # Check length compliance (5-6 words max)
                length_compliant = True
                for text in thumbnail_texts:
                    if len(text.split()) > 6:
                        length_compliant = False
                        validation_report['issues'].append(f"Idea {i+1}: Text too long: '{text}'")
                
                if length_compliant:
                    validation_report['length_compliance'] += 1
            
            # Calculate percentages
            if validation_report['total_ideas'] > 0:
                total = validation_report['total_ideas']
                validation_report['valid_texts_percent'] = (validation_report['valid_texts'] / total) * 100
                validation_report['power_word_percent'] = (validation_report['power_word_coverage'] / total) * 100
                validation_report['length_compliance_percent'] = (validation_report['length_compliance'] / total) * 100
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Error validating thumbnail texts: {e}")
            return {'error': str(e)}

# Utility functions for easy integration

def generate_thumbnail_texts(ideas: List[Dict[str, Any]], strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convenience function to generate thumbnail texts.
    
    Args:
        ideas (List[dict]): Output from generate_video_ideas()
        strategy (dict): User strategy configuration
        
    Returns:
        List[dict]: Enhanced ideas with thumbnail_texts added
    """
    generator = ThumbnailTextGenerator()
    return generator.generate_thumbnail_texts(ideas, strategy)

def main():
    """
    Example usage of the Thumbnail Text Generator.
    """
    try:
        # Example video ideas
        sample_ideas = [
            {
                'title': 'Ultimate Guide to Cooking Perfect Rice Every Time',
                'brief': 'Learn the secret techniques that professional chefs use to cook perfect rice.',
                'target_keywords': ['cooking rice', 'perfect rice', 'rice tutorial'],
                'psychology_triggers': ['authority', 'curiosity'],
                'call_to_action': '🔔 SUBSCRIBE for more cooking secrets!'
            },
            {
                'title': 'You Won\'t Believe These Study Abroad Secrets',
                'brief': 'Hidden tips that universities don\'t want international students to know.',
                'target_keywords': ['study abroad', 'student secrets', 'university tips'],
                'psychology_triggers': ['curiosity', 'scarcity'],
                'call_to_action': '💬 COMMENT your study abroad questions!'
            },
            {
                'title': 'Before You Apply - Visa Interview Mistakes to Avoid',
                'brief': 'Critical mistakes that could ruin your visa application and how to avoid them.',
                'target_keywords': ['visa interview', 'visa mistakes', 'application tips'],
                'psychology_triggers': ['fomo', 'authority'],
                'call_to_action': '📧 Get the complete visa guide in description!'
            }
        ]
        
        # Example strategy
        sample_strategy = {
            'goal': 'subscribers',
            'country': 'Bangladesh',
            'audience': 'students',
            'age_range': '18-25'
        }
        
        print("Thumbnail Text Generator Example")
        print("=" * 40)
        
        # Generate thumbnail texts
        generator = ThumbnailTextGenerator()
        enhanced_ideas = generator.generate_thumbnail_texts(sample_ideas, sample_strategy)
        
        # Display results
        print(f"\n🎨 GENERATED THUMBNAIL TEXTS")
        print(f"Goal: {sample_strategy['goal']} | Audience: {sample_strategy['audience']}")
        
        for i, idea in enumerate(enhanced_ideas, 1):
            print(f"\n📹 IDEA {i}: {idea['title'][:50]}...")
            print(f"🖼️  Thumbnail Texts:")
            for j, text in enumerate(idea['thumbnail_texts'], 1):
                print(f"    {j}. {text}")
        
        # Validate results
        validation = generator.validate_thumbnail_texts(enhanced_ideas)
        
        print(f"\n✅ VALIDATION REPORT:")
        print(f"Valid Texts: {validation['valid_texts']}/{validation['total_ideas']} ({validation.get('valid_texts_percent', 0):.1f}%)")
        print(f"Power Word Coverage: {validation['power_word_coverage']}/{validation['total_ideas']} ({validation.get('power_word_percent', 0):.1f}%)")
        print(f"Length Compliance: {validation['length_compliance']}/{validation['total_ideas']} ({validation.get('length_compliance_percent', 0):.1f}%)")
        
        if validation.get('issues'):
            print(f"\n⚠️  Issues Found:")
            for issue in validation['issues'][:3]:  # Show first 3 issues
                print(f"  - {issue}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()
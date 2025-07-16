"""
Emotion Optimizer Module for YouTube Content Optimization.

This module enhances SEO metadata with psychological triggers and emotional hooks
to maximize engagement, click-through rates, and conversion based on marketing psychology.

Features:
1. Psychological trigger integration (curiosity, FOMO, authority, scarcity, relatability)
2. Strategy-based optimization for different goals (views, subscribers, leads, sales)
3. Gemini AI-powered content enhancement with fallback mechanisms
4. Emotional classification and trigger labeling
5. CTA optimization based on audience and goals

Psychological Triggers Used:
- 🔥 Curiosity: "You won't believe...", "What happens when..."
- ⏳ FOMO: "Before it's gone", "Don't miss out"
- 👑 Authority: "Expert reveals...", "Doctor explains..."
- 💔 Emotional Relatability: "If you've ever felt...", "We've all been there..."
- 🎯 Scarcity: "Only today", "Limited time", "Exclusive access"
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmotionOptimizer:
    """
    Optimizes YouTube metadata using psychological triggers and emotional hooks.
    
    Enhances titles, descriptions, and thumbnail text with proven marketing psychology
    techniques to increase engagement, CTR, and conversions based on specific goals.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Emotion Optimizer.
        
        Args:
            api_key (str, optional): Gemini API key. Uses GEMINI_API_KEY env var if not provided.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning(
                "Gemini API key not found. Will use fallback optimization methods. "
                "Set GEMINI_API_KEY environment variable for full AI enhancement."
            )
        
        # Configure Gemini if API key available
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
        
        # Psychological trigger patterns and templates
        self.psychology_triggers = {
            'curiosity': {
                'emoji': '🔥',
                'patterns': [
                    "You won't believe what happens when...",
                    "What happens if you...",
                    "The secret behind...",
                    "What nobody tells you about...",
                    "The truth about...",
                    "What I discovered when...",
                    "The surprising reason why...",
                    "This will change how you think about...",
                    "What experts don't want you to know...",
                    "The hidden truth behind..."
                ],
                'keywords': ['secret', 'hidden', 'truth', 'discover', 'reveal', 'surprising', 'shocking']
            },
            'fomo': {
                'emoji': '⏳',
                'patterns': [
                    "Before it's too late...",
                    "Don't miss out on...",
                    "Last chance to...",
                    "Everyone is talking about...",
                    "While you still can...",
                    "Before everyone else finds out...",
                    "Time is running out for...",
                    "Don't let this opportunity pass...",
                    "Act now before...",
                    "This won't last long..."
                ],
                'keywords': ['limited', 'last chance', 'running out', 'before', 'miss out', 'opportunity']
            },
            'authority': {
                'emoji': '👑',
                'patterns': [
                    "Expert reveals...",
                    "Doctor explains...",
                    "Professional guide to...",
                    "Master class in...",
                    "Proven method for...",
                    "Scientific approach to...",
                    "Industry insider shares...",
                    "Years of experience show...",
                    "Research proves...",
                    "Certified expert teaches..."
                ],
                'keywords': ['expert', 'doctor', 'professional', 'proven', 'scientific', 'certified', 'master']
            },
            'emotional': {
                'emoji': '💔',
                'patterns': [
                    "If you've ever felt...",
                    "We've all been there...",
                    "For anyone who has ever...",
                    "Every [audience] needs to know...",
                    "The struggle is real...",
                    "What every [audience] wishes they knew...",
                    "If you're like me...",
                    "The pain of...",
                    "Finally, someone understands...",
                    "You're not alone in..."
                ],
                'keywords': ['struggle', 'pain', 'feel', 'understand', 'relate', 'experience', 'emotion']
            },
            'scarcity': {
                'emoji': '🎯',
                'patterns': [
                    "Only today...",
                    "Limited time offer...",
                    "Exclusive access to...",
                    "Never before revealed...",
                    "One-time opportunity...",
                    "While supplies last...",
                    "Secret method (limited)...",
                    "Rare opportunity to...",
                    "First time ever...",
                    "Exclusive behind-the-scenes..."
                ],
                'keywords': ['exclusive', 'limited', 'rare', 'first time', 'only', 'secret', 'special']
            }
        }
        
        # Goal-specific optimization strategies
        self.goal_strategies = {
            'views': {
                'primary_triggers': ['curiosity', 'fomo', 'emotional'],
                'cta_style': 'viral_engagement',
                'tone': 'exciting',
                'focus': 'broad appeal and shareability'
            },
            'subscribers': {
                'primary_triggers': ['authority', 'emotional', 'scarcity'],
                'cta_style': 'community_building',
                'tone': 'trustworthy',
                'focus': 'long-term value and consistency'
            },
            'engagement': {
                'primary_triggers': ['emotional', 'curiosity', 'fomo'],
                'cta_style': 'interaction_focused',
                'tone': 'conversational',
                'focus': 'comments, likes, and discussion'
            },
            'leads': {
                'primary_triggers': ['authority', 'scarcity', 'fomo'],
                'cta_style': 'conversion_oriented',
                'tone': 'professional',
                'focus': 'value proposition and trust building'
            },
            'sales': {
                'primary_triggers': ['scarcity', 'authority', 'fomo'],
                'cta_style': 'direct_conversion',
                'tone': 'persuasive',
                'focus': 'benefits and urgency'
            }
        }
        
        logger.info("Emotion Optimizer initialized successfully")
    
    def optimize_metadata(self, metadata: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize metadata with psychological triggers and emotional hooks.
        
        Args:
            metadata (dict): Output from generate_seo_metadata() with titles, description, etc.
            strategy (dict): User preferences with goal, audience, country
            
        Returns:
            dict: Enhanced metadata with psychological triggers and CTAs
        """
        try:
            logger.info(f"Optimizing metadata for goal: {strategy.get('goal', 'views')}")
            
            # Validate inputs
            if not isinstance(metadata, dict):
                raise ValueError("Metadata must be a dictionary")
            if not isinstance(strategy, dict):
                raise ValueError("Strategy must be a dictionary")
            
            # Get goal strategy
            goal = strategy.get('goal', 'views')
            goal_strategy = self.goal_strategies.get(goal, self.goal_strategies['views'])
            
            # Initialize optimized metadata
            optimized = {
                'titles': [],
                'description': '',
                'thumbnail_text': [],
                'tags': metadata.get('tags', []),
                'cta_suggestions': [],
                'psychology_labels': {}
            }
            
            # Optimize titles with AI or fallback
            if self.model and self.api_key:
                try:
                    optimized['titles'] = self._optimize_titles_with_ai(
                        metadata.get('titles', []), strategy, goal_strategy
                    )
                except Exception as e:
                    logger.warning(f"AI title optimization failed: {e}, using fallback")
                    optimized['titles'] = self._optimize_titles_fallback(
                        metadata.get('titles', []), goal_strategy
                    )
            else:
                optimized['titles'] = self._optimize_titles_fallback(
                    metadata.get('titles', []), goal_strategy
                )
            
            # Optimize thumbnail text
            if self.model and self.api_key:
                try:
                    optimized['thumbnail_text'] = self._optimize_thumbnail_text_with_ai(
                        metadata.get('thumbnail_text', []), strategy, goal_strategy
                    )
                except Exception as e:
                    logger.warning(f"AI thumbnail optimization failed: {e}, using fallback")
                    optimized['thumbnail_text'] = self._optimize_thumbnail_text_fallback(
                        metadata.get('thumbnail_text', []), goal_strategy
                    )
            else:
                optimized['thumbnail_text'] = self._optimize_thumbnail_text_fallback(
                    metadata.get('thumbnail_text', []), goal_strategy
                )
            
            # Optimize description
            optimized['description'] = self._optimize_description(
                metadata.get('description', ''), strategy, goal_strategy
            )
            
            # Generate CTA suggestions
            optimized['cta_suggestions'] = self._generate_cta_suggestions(strategy, goal_strategy)
            
            # Label psychology triggers
            optimized['psychology_labels'] = self.label_psychology(optimized)
            
            logger.info("Successfully optimized metadata with psychological triggers")
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing metadata: {e}")
            # Return original metadata with basic enhancements
            return self._create_fallback_optimization(metadata, strategy)
    
    def _optimize_titles_with_ai(self, titles: List[str], strategy: Dict[str, Any], 
                                goal_strategy: Dict[str, Any]) -> List[str]:
        """Optimize titles using Gemini AI with psychological triggers."""
        if not titles:
            return []
        
        # Build prompt for title optimization
        triggers = goal_strategy['primary_triggers']
        trigger_descriptions = []
        for trigger in triggers:
            emoji = self.psychology_triggers[trigger]['emoji']
            patterns = self.psychology_triggers[trigger]['patterns'][:3]
            trigger_descriptions.append(f"{emoji} {trigger.title()}: {', '.join(patterns)}")
        
        prompt = f"""You are a YouTube title optimization expert specializing in psychological marketing triggers.

GOAL: {strategy.get('goal', 'views')} optimization
AUDIENCE: {strategy.get('audience', 'general')} in {strategy.get('country', 'Global')}
AGE RANGE: {strategy.get('age_range', '18-35')}

PSYCHOLOGICAL TRIGGERS TO USE:
{chr(10).join(trigger_descriptions)}

ORIGINAL TITLES:
{chr(10).join([f"{i+1}. {title}" for i, title in enumerate(titles)])}

REQUIREMENTS:
1. Rewrite each title with enhanced psychological hooks
2. Each title should use a different primary trigger
3. Keep titles under 60 characters
4. Make them compelling but not clickbait
5. Maintain the core topic while adding emotional appeal
6. Consider the {strategy.get('country', 'Global')} audience

OUTPUT FORMAT:
1. [Enhanced Title 1]
2. [Enhanced Title 2]
3. [Enhanced Title 3]

Generate 3 psychologically optimized titles:"""
        
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                # Parse the response
                lines = response.text.strip().split('\n')
                optimized_titles = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith(('1.', '2.', '3.')) or line.startswith('-')):
                        # Extract title after number/bullet
                        title = re.sub(r'^[\d\-\.\s]+', '', line).strip()
                        if title and len(title) <= 70:  # Allow slight flexibility
                            optimized_titles.append(title)
                
                if len(optimized_titles) >= 2:
                    return optimized_titles[:3]  # Return up to 3 titles
            
            # If parsing failed, use fallback
            return self._optimize_titles_fallback(titles, goal_strategy)
            
        except Exception as e:
            logger.error(f"AI title optimization error: {e}")
            return self._optimize_titles_fallback(titles, goal_strategy)
    
    def _optimize_titles_fallback(self, titles: List[str], goal_strategy: Dict[str, Any]) -> List[str]:
        """Fallback title optimization using pattern matching."""
        if not titles:
            return []
        
        optimized = []
        triggers = goal_strategy['primary_triggers']
        
        for i, title in enumerate(titles[:3]):
            trigger = triggers[i % len(triggers)]
            trigger_data = self.psychology_triggers[trigger]
            
            # Apply trigger pattern
            if trigger == 'curiosity':
                if not any(word in title.lower() for word in ['secret', 'truth', 'discover']):
                    optimized.append(f"The Secret Behind {title}")
                else:
                    optimized.append(title)
            elif trigger == 'fomo':
                if not any(word in title.lower() for word in ['before', 'limited', 'last']):
                    optimized.append(f"{title} - Before It's Too Late!")
                else:
                    optimized.append(title)
            elif trigger == 'authority':
                if not any(word in title.lower() for word in ['expert', 'proven', 'professional']):
                    optimized.append(f"Expert Guide: {title}")
                else:
                    optimized.append(title)
            elif trigger == 'emotional':
                if not any(word in title.lower() for word in ['you', 'your', 'feel']):
                    optimized.append(f"If You've Ever Wondered About {title}")
                else:
                    optimized.append(title)
            elif trigger == 'scarcity':
                if not any(word in title.lower() for word in ['exclusive', 'limited', 'only']):
                    optimized.append(f"Exclusive: {title}")
                else:
                    optimized.append(title)
            else:
                optimized.append(title)
        
        return optimized
    
    def _optimize_thumbnail_text_with_ai(self, thumbnail_texts: List[str], strategy: Dict[str, Any],
                                        goal_strategy: Dict[str, Any]) -> List[str]:
        """Optimize thumbnail text using Gemini AI."""
        if not thumbnail_texts:
            return []
        
        triggers = goal_strategy['primary_triggers']
        
        prompt = f"""You are a YouTube thumbnail text optimization expert.

GOAL: {strategy.get('goal', 'views')} optimization
AUDIENCE: {strategy.get('audience', 'general')}

ORIGINAL THUMBNAIL TEXTS:
{chr(10).join([f"{i+1}. {text}" for i, text in enumerate(thumbnail_texts)])}

REQUIREMENTS:
1. Rewrite each text with psychological hooks
2. Maximum 3-5 words per text
3. Use power words and emotional triggers
4. Make them readable at small sizes
5. Create urgency and curiosity
6. Use these triggers: {', '.join(triggers)}

POWER WORDS TO CONSIDER:
- Curiosity: SECRET, TRUTH, HIDDEN, REVEALED
- FOMO: LIMITED, LAST, BEFORE, NOW
- Authority: EXPERT, PROVEN, OFFICIAL
- Emotional: SHOCKING, AMAZING, INCREDIBLE
- Scarcity: EXCLUSIVE, RARE, ONLY

OUTPUT FORMAT:
1. [Enhanced Text 1]
2. [Enhanced Text 2]
3. [Enhanced Text 3]

Generate 3 optimized thumbnail texts:"""
        
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                lines = response.text.strip().split('\n')
                optimized_texts = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith(('1.', '2.', '3.')) or line.startswith('-')):
                        text = re.sub(r'^[\d\-\.\s]+', '', line).strip()
                        if text and len(text.split()) <= 5:
                            optimized_texts.append(text.upper())
                
                if len(optimized_texts) >= 2:
                    return optimized_texts[:3]
            
            return self._optimize_thumbnail_text_fallback(thumbnail_texts, goal_strategy)
            
        except Exception as e:
            logger.error(f"AI thumbnail optimization error: {e}")
            return self._optimize_thumbnail_text_fallback(thumbnail_texts, goal_strategy)
    
    def _optimize_thumbnail_text_fallback(self, thumbnail_texts: List[str], 
                                         goal_strategy: Dict[str, Any]) -> List[str]:
        """Fallback thumbnail text optimization."""
        if not thumbnail_texts:
            return ["SECRET REVEALED", "SHOCKING TRUTH", "EXCLUSIVE TIPS"]
        
        power_words = {
            'curiosity': ['SECRET', 'HIDDEN', 'TRUTH', 'REVEALED'],
            'fomo': ['LIMITED', 'LAST CHANCE', 'NOW', 'URGENT'],
            'authority': ['EXPERT', 'PROVEN', 'OFFICIAL', 'PRO'],
            'emotional': ['SHOCKING', 'AMAZING', 'INCREDIBLE', 'MIND-BLOWN'],
            'scarcity': ['EXCLUSIVE', 'RARE', 'ONLY', 'SPECIAL']
        }
        
        optimized = []
        triggers = goal_strategy['primary_triggers']
        
        for i, text in enumerate(thumbnail_texts[:3]):
            trigger = triggers[i % len(triggers)]
            words = power_words.get(trigger, ['AMAZING'])
            
            # Keep original if it's already good, otherwise enhance
            if len(text.split()) <= 3 and any(word.upper() in text.upper() for word in words):
                optimized.append(text.upper())
            else:
                # Add power word
                power_word = words[0]
                optimized.append(f"{power_word} {text.upper()}"[:20])  # Limit length
        
        return optimized
    
    def _optimize_description(self, description: str, strategy: Dict[str, Any],
                            goal_strategy: Dict[str, Any]) -> str:
        """Optimize description with psychological triggers."""
        if not description:
            return ""
        
        # Add psychological hooks to the beginning
        goal = strategy.get('goal', 'views')
        triggers = goal_strategy['primary_triggers']
        
        # Create compelling opening based on primary trigger
        primary_trigger = triggers[0]
        
        hooks = {
            'curiosity': "You're about to discover something that will change everything...",
            'fomo': "Don't let this opportunity slip away - thousands are already benefiting...",
            'authority': "After years of research and testing, I'm finally sharing...",
            'emotional': "If you've ever felt frustrated or stuck, this is for you...",
            'scarcity': "This exclusive information is only available for a limited time..."
        }
        
        hook = hooks.get(primary_trigger, "Get ready for something amazing...")
        
        # Enhance the description
        enhanced_description = f"{hook}\n\n{description}"
        
        # Add goal-specific CTA at the end
        cta_endings = {
            'views': "\n\n🔥 SHARE this with someone who needs to see it!\n💬 COMMENT below with your thoughts!\n👍 LIKE if this helped you!",
            'subscribers': "\n\n🔔 SUBSCRIBE for more exclusive content like this!\n👥 JOIN our community of learners!\n📺 TURN ON notifications so you never miss out!",
            'engagement': "\n\n💬 What's YOUR experience with this? Comment below!\n🤔 Which tip surprised you most?\n📤 SHARE your own tips in the comments!",
            'leads': "\n\n📧 Want more exclusive tips? Link in description!\n🎯 Ready to take action? Check out our resources!\n💼 Serious about results? Let's connect!",
            'sales': "\n\n🛒 Ready to get started? Link in description!\n⏰ Limited time offer - don't wait!\n💰 Transform your results today!"
        }
        
        enhanced_description += cta_endings.get(goal, cta_endings['views'])
        
        return enhanced_description
    
    def _generate_cta_suggestions(self, strategy: Dict[str, Any], 
                                 goal_strategy: Dict[str, Any]) -> List[str]:
        """Generate CTA suggestions based on goal and strategy."""
        goal = strategy.get('goal', 'views')
        audience = strategy.get('audience', 'general')
        
        cta_templates = {
            'views': [
                f"🔥 If this helped you, SMASH that like button and share with a fellow {audience}!",
                f"💥 Don't keep this to yourself - your {audience} friends need to see this!"
            ],
            'subscribers': [
                f"🔔 Join our community of {audience}s - SUBSCRIBE for weekly insights!",
                f"👥 Become part of our exclusive {audience} family - hit that subscribe button!"
            ],
            'engagement': [
                f"💬 {audience.title()}s - what's YOUR biggest challenge with this? Comment below!",
                f"🤝 Let's discuss - which tip will you try first? Tell us in the comments!"
            ],
            'leads': [
                f"📧 Want the complete {audience} guide? Link in description for exclusive access!",
                f"🎯 Ready to level up as a {audience}? Get our free resources below!"
            ],
            'sales': [
                f"🛒 Transform your {audience} journey today - limited time offer in description!",
                f"⏰ Don't wait - exclusive {audience} program launching soon!"
            ]
        }
        
        return cta_templates.get(goal, cta_templates['views'])
    
    def _create_fallback_optimization(self, metadata: Dict[str, Any], 
                                    strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic fallback optimization when AI fails."""
        goal = strategy.get('goal', 'views')
        
        return {
            'titles': metadata.get('titles', [])[:3],
            'description': metadata.get('description', ''),
            'thumbnail_text': metadata.get('thumbnail_text', [])[:3],
            'tags': metadata.get('tags', []),
            'cta_suggestions': [
                f"🔥 LIKE and SHARE if this helped you!",
                f"🔔 SUBSCRIBE for more {goal}-focused content!"
            ],
            'psychology_labels': {
                'primary_triggers': ['curiosity', 'fomo'],
                'confidence': 'fallback'
            }
        }
    
    def label_psychology(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify which psychological triggers each variant uses.
        
        Args:
            metadata (dict): Optimized metadata with titles, thumbnail_text, etc.
            
        Returns:
            dict: Psychology labels and trigger classifications
        """
        try:
            labels = {
                'title_triggers': [],
                'thumbnail_triggers': [],
                'description_triggers': [],
                'dominant_trigger': None,
                'trigger_distribution': {}
            }
            
            # Analyze titles
            titles = metadata.get('titles', [])
            for title in titles:
                triggers = self._identify_triggers_in_text(title)
                labels['title_triggers'].append(triggers)
            
            # Analyze thumbnail text
            thumbnail_texts = metadata.get('thumbnail_text', [])
            for text in thumbnail_texts:
                triggers = self._identify_triggers_in_text(text)
                labels['thumbnail_triggers'].append(triggers)
            
            # Analyze description
            description = metadata.get('description', '')
            if description:
                labels['description_triggers'] = self._identify_triggers_in_text(description)
            
            # Calculate trigger distribution
            all_triggers = []
            for title_triggers in labels['title_triggers']:
                all_triggers.extend(title_triggers)
            for thumb_triggers in labels['thumbnail_triggers']:
                all_triggers.extend(thumb_triggers)
            if labels['description_triggers']:
                all_triggers.extend(labels['description_triggers'])
            
            # Count trigger frequency
            trigger_counts = {}
            for trigger in all_triggers:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
            
            labels['trigger_distribution'] = trigger_counts
            
            # Find dominant trigger
            if trigger_counts:
                labels['dominant_trigger'] = max(trigger_counts, key=trigger_counts.get)
            
            return labels
            
        except Exception as e:
            logger.error(f"Error labeling psychology triggers: {e}")
            return {'error': str(e)}
    
    def _identify_triggers_in_text(self, text: str) -> List[str]:
        """Identify psychological triggers present in text."""
        if not text:
            return []
        
        text_lower = text.lower()
        identified_triggers = []
        
        for trigger_name, trigger_data in self.psychology_triggers.items():
            keywords = trigger_data['keywords']
            
            # Check if any trigger keywords are present
            if any(keyword in text_lower for keyword in keywords):
                identified_triggers.append(trigger_name)
            
            # Check for specific patterns
            patterns = trigger_data['patterns']
            for pattern in patterns:
                # Extract key phrases from patterns
                key_phrases = pattern.lower().split('...')
                if key_phrases and any(phrase.strip() in text_lower for phrase in key_phrases if phrase.strip()):
                    if trigger_name not in identified_triggers:
                        identified_triggers.append(trigger_name)
        
        return identified_triggers

# Utility functions for easy integration

def optimize_metadata(metadata: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to optimize metadata with psychological triggers.
    
    Args:
        metadata (dict): Output from generate_seo_metadata()
        strategy (dict): User strategy configuration
        
    Returns:
        dict: Optimized metadata with psychological enhancements
    """
    optimizer = EmotionOptimizer()
    return optimizer.optimize_metadata(metadata, strategy)

def label_psychology(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to label psychological triggers in metadata.
    
    Args:
        metadata (dict): Metadata to analyze
        
    Returns:
        dict: Psychology trigger labels and classifications
    """
    optimizer = EmotionOptimizer()
    return optimizer.label_psychology(metadata)

def main():
    """
    Example usage of the Emotion Optimizer.
    """
    try:
        # Example metadata from SEO writer
        sample_metadata = {
            'titles': [
                'How to Cook Perfect Rice Every Time',
                'Bengali Rice Cooking Tutorial for Beginners',
                'Traditional Rice Cooking Methods Explained'
            ],
            'description': '''Learn the traditional Bengali method of cooking perfect rice every time. This comprehensive guide covers everything from selecting the right rice to achieving the perfect texture. Whether you're a beginner or looking to improve your technique, this tutorial will help you master this essential skill.

Perfect for home cooks who want to create authentic Bengali meals. Follow along as we explore time-tested techniques passed down through generations.''',
            'thumbnail_text': [
                'PERFECT RICE',
                'EASY METHOD',
                'BENGALI STYLE'
            ],
            'tags': ['rice cooking', 'bengali food', 'cooking tutorial', 'traditional cooking']
        }
        
        # Example strategy
        sample_strategy = {
            'goal': 'subscribers',
            'country': 'Bangladesh',
            'audience': 'home cooks',
            'age_range': '25-45'
        }
        
        print("Emotion Optimizer Example")
        print("=" * 40)
        
        # Initialize optimizer
        optimizer = EmotionOptimizer()
        
        # Optimize metadata
        optimized = optimizer.optimize_metadata(sample_metadata, sample_strategy)
        
        # Display results
        print(f"\n🎯 OPTIMIZED METADATA for '{sample_strategy['goal']}' goal:")
        print(f"Target: {sample_strategy['audience']} in {sample_strategy['country']}")
        
        print(f"\n📝 ENHANCED TITLES:")
        for i, title in enumerate(optimized['titles'], 1):
            print(f"  {i}. {title}")
        
        print(f"\n🖼️  ENHANCED THUMBNAIL TEXT:")
        for i, text in enumerate(optimized['thumbnail_text'], 1):
            print(f"  {i}. {text}")
        
        print(f"\n📄 ENHANCED DESCRIPTION:")
        print(f"  {optimized['description'][:200]}...")
        
        print(f"\n💡 CTA SUGGESTIONS:")
        for i, cta in enumerate(optimized['cta_suggestions'], 1):
            print(f"  {i}. {cta}")
        
        # Label psychology triggers
        labels = optimizer.label_psychology(optimized)
        
        print(f"\n🧠 PSYCHOLOGY ANALYSIS:")
        print(f"  Dominant Trigger: {labels.get('dominant_trigger', 'None')}")
        print(f"  Trigger Distribution: {labels.get('trigger_distribution', {})}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()
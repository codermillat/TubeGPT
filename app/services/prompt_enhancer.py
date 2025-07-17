"""
Auto-Prompt Enhancer for YouTube SEO Assistant.

This module enhances raw keyword-based prompts with psychological triggers,
tone adjustments, and audience-specific language to maximize AI response quality.

Features:
- Tone injection (persuasive, curiosity, fear, authority, engaging)
- Psychological trigger integration
- Audience-specific language adaptation
- Context enhancement for better AI responses
- Fallback prompt templates
"""

import logging
import re
from typing import Dict, List, Optional, Any
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)


class ContentTone(Enum):
    """Supported content tones for prompt enhancement."""
    CURIOSITY = "curiosity"
    AUTHORITY = "authority"
    FEAR = "fear"
    PERSUASIVE = "persuasive"
    ENGAGING = "engaging"


class PromptEnhancer:
    """
    Enhances raw prompts with psychological triggers and tone adjustments.
    
    Transforms basic keyword-based prompts into compelling, psychologically-optimized
    prompts that generate better AI responses for YouTube content creation.
    """
    
    def __init__(self):
        """Initialize the Prompt Enhancer with psychological trigger templates."""
        
        # Psychological trigger templates by tone
        self.tone_templates = {
            ContentTone.CURIOSITY: {
                "hooks": [
                    "What if I told you that",
                    "You won't believe what happens when",
                    "The secret that nobody talks about",
                    "What [expert] doesn't want you to know",
                    "The hidden truth behind"
                ],
                "modifiers": [
                    "mysterious", "hidden", "secret", "unknown", "surprising",
                    "shocking", "unexpected", "mind-blowing", "incredible"
                ],
                "endings": [
                    "You'll never guess what happens next",
                    "The results will shock you",
                    "This changes everything",
                    "Wait until you see this",
                    "You won't believe your eyes"
                ]
            },
            
            ContentTone.AUTHORITY: {
                "hooks": [
                    "As an expert with [X] years of experience",
                    "Industry professionals use this method",
                    "The proven strategy that",
                    "According to the latest research",
                    "Professional insights reveal"
                ],
                "modifiers": [
                    "proven", "expert-level", "professional", "advanced",
                    "research-backed", "industry-standard", "certified", "authoritative"
                ],
                "endings": [
                    "backed by scientific research",
                    "used by top professionals",
                    "proven in real-world scenarios",
                    "recommended by experts",
                    "validated by industry leaders"
                ]
            },
            
            ContentTone.FEAR: {
                "hooks": [
                    "Don't make the mistake of",
                    "Avoid this costly error",
                    "Warning: This could ruin",
                    "The dangerous truth about",
                    "Before you lose everything"
                ],
                "modifiers": [
                    "dangerous", "risky", "costly", "harmful", "damaging",
                    "destructive", "threatening", "critical", "urgent"
                ],
                "endings": [
                    "before it's too late",
                    "or face the consequences",
                    "don't let this happen to you",
                    "protect yourself now",
                    "act before you lose everything"
                ]
            },
            
            ContentTone.PERSUASIVE: {
                "hooks": [
                    "Join thousands who have already",
                    "The ultimate solution for",
                    "Transform your life with",
                    "Discover the complete system",
                    "Get instant results with"
                ],
                "modifiers": [
                    "ultimate", "complete", "revolutionary", "game-changing",
                    "life-changing", "instant", "guaranteed", "exclusive", "limited"
                ],
                "endings": [
                    "join the success stories",
                    "limited time opportunity",
                    "exclusive access available now",
                    "guaranteed results or money back",
                    "transform your results today"
                ]
            },
            
            ContentTone.ENGAGING: {
                "hooks": [
                    "Let's dive into",
                    "Get ready to explore",
                    "Join me as we discover",
                    "Together, we'll uncover",
                    "Come along on this journey"
                ],
                "modifiers": [
                    "amazing", "incredible", "fantastic", "awesome", "brilliant",
                    "fascinating", "exciting", "inspiring", "uplifting", "fun"
                ],
                "endings": [
                    "let's make it happen together",
                    "you're going to love this",
                    "this will inspire you",
                    "perfect for anyone looking to grow",
                    "let's create something amazing"
                ]
            }
        }
        
        # Audience-specific language patterns
        self.audience_patterns = {
            "genz": {
                "language": ["no cap", "periodt", "slay", "iconic", "main character energy"],
                "style": "casual, trendy, social media native",
                "references": "trending topics, social media culture, viral content"
            },
            "millennial": {
                "language": ["honestly", "literally", "adulting", "mood", "relatable"],
                "style": "conversational, nostalgic, work-life balance focused",
                "references": "90s/2000s nostalgia, career growth, life transitions"
            },
            "tech": {
                "language": ["optimize", "leverage", "scale", "innovation", "cutting-edge"],
                "style": "technical but accessible, data-driven, solution-focused",
                "references": "latest tech trends, productivity tools, automation"
            },
            "creative": {
                "language": ["inspire", "vision", "aesthetic", "authentic", "storytelling"],
                "style": "artistic, expressive, narrative-driven",
                "references": "creative process, artistic techniques, inspiration sources"
            },
            "business": {
                "language": ["ROI", "strategy", "growth", "efficiency", "results"],
                "style": "professional, goal-oriented, metrics-focused",
                "references": "business metrics, leadership, entrepreneurship"
            }
        }
    
    def enhance_prompt(
        self,
        base_prompt: str,
        tone: str = "engaging",
        audience: Optional[str] = None,
        goal: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> str:
        """
        Enhance a basic prompt with psychological triggers and tone adjustments.
        
        Args:
            base_prompt: The original prompt to enhance
            tone: Content tone (curiosity, authority, fear, persuasive, engaging)
            audience: Target audience description
            goal: Specific goal or objective
            keywords: List of keywords to emphasize
            
        Returns:
            Enhanced prompt with psychological triggers and tone optimization
        """
        
        logger.debug(f"Enhancing prompt with tone: {tone}, audience: {audience}")
        
        try:
            # Convert tone to enum
            tone_enum = ContentTone(tone.lower())
        except ValueError:
            logger.warning(f"Unknown tone '{tone}', defaulting to 'engaging'")
            tone_enum = ContentTone.ENGAGING
        
        # Start with the base prompt
        enhanced_prompt = base_prompt
        
        # Add tone-specific hooks and modifiers
        enhanced_prompt = self._inject_tone_elements(enhanced_prompt, tone_enum)
        
        # Add audience-specific language
        if audience:
            enhanced_prompt = self._inject_audience_language(enhanced_prompt, audience)
        
        # Enhance with goal-specific context
        if goal:
            enhanced_prompt = self._inject_goal_context(enhanced_prompt, goal, tone_enum)
        
        # Emphasize keywords
        if keywords:
            enhanced_prompt = self._emphasize_keywords(enhanced_prompt, keywords)
        
        # Add psychological structure
        enhanced_prompt = self._add_psychological_structure(enhanced_prompt, tone_enum)
        
        # Add output format instructions
        enhanced_prompt = self._add_output_format_instructions(enhanced_prompt)
        
        logger.debug("Prompt enhancement completed")
        return enhanced_prompt
    
    def _inject_tone_elements(self, prompt: str, tone: ContentTone) -> str:
        """Inject tone-specific hooks and modifiers into the prompt."""
        
        tone_data = self.tone_templates[tone]
        
        # Add a compelling hook at the beginning
        hook = tone_data["hooks"][0]  # Use first hook for consistency
        
        # Enhance the prompt with tone-specific language
        enhanced = f"""
{hook}, here's what we need to create:

{prompt}

Please ensure the content embodies a {tone.value} tone throughout, using language that is {', '.join(tone_data['modifiers'][:3])}.
        """.strip()
        
        return enhanced
    
    def _inject_audience_language(self, prompt: str, audience: str) -> str:
        """Inject audience-specific language patterns."""
        
        # Detect audience type
        audience_lower = audience.lower()
        audience_type = None
        
        for aud_type, patterns in self.audience_patterns.items():
            if aud_type in audience_lower:
                audience_type = aud_type
                break
        
        # Default to general audience if no specific type detected
        if not audience_type:
            if "tech" in audience_lower or "developer" in audience_lower:
                audience_type = "tech"
            elif "business" in audience_lower or "entrepreneur" in audience_lower:
                audience_type = "business"
            elif "creative" in audience_lower or "artist" in audience_lower:
                audience_type = "creative"
            elif "genz" in audience_lower or "gen z" in audience_lower:
                audience_type = "genz"
            else:
                audience_type = "millennial"  # Default
        
        audience_data = self.audience_patterns[audience_type]
        
        # Add audience-specific instructions
        audience_instruction = f"""
Target Audience: {audience}
Communication Style: {audience_data['style']}
Reference Points: {audience_data['references']}

Please tailor the language and examples to resonate with this specific audience.
        """
        
        return prompt + "\n\n" + audience_instruction
    
    def _inject_goal_context(self, prompt: str, goal: str, tone: ContentTone) -> str:
        """Inject goal-specific context and urgency."""
        
        tone_data = self.tone_templates[tone]
        ending = tone_data["endings"][0]  # Use first ending for consistency
        
        goal_context = f"""
Primary Goal: {goal}

Success Criteria: Content should directly address this goal while maintaining {tone.value} tone.
Expected Outcome: {ending}
        """
        
        return prompt + "\n\n" + goal_context
    
    def _emphasize_keywords(self, prompt: str, keywords: List[str]) -> str:
        """Emphasize important keywords in the prompt."""
        
        if not keywords:
            return prompt
        
        keyword_instruction = f"""
Priority Keywords: {', '.join(keywords[:5])}

Please ensure these keywords are naturally integrated throughout the content while maintaining readability and flow.
        """
        
        return prompt + "\n\n" + keyword_instruction
    
    def _add_psychological_structure(self, prompt: str, tone: ContentTone) -> str:
        """Add psychological structure based on tone."""
        
        psychological_frameworks = {
            ContentTone.CURIOSITY: "Hook → Question → Discovery → Revelation → Satisfaction",
            ContentTone.AUTHORITY: "Credentials → Problem → Solution → Proof → Implementation",
            ContentTone.FEAR: "Warning → Consequences → Urgency → Solution → Relief",
            ContentTone.PERSUASIVE: "Problem → Agitation → Solution → Benefits → Action",
            ContentTone.ENGAGING: "Connection → Story → Value → Inspiration → Community"
        }
        
        framework = psychological_frameworks[tone]
        
        structure_instruction = f"""
Psychological Structure: {framework}

Please structure the content following this psychological flow to maximize engagement and effectiveness.
        """
        
        return prompt + "\n\n" + structure_instruction
    
    def _add_output_format_instructions(self, prompt: str) -> str:
        """Add specific output format instructions."""
        
        format_instruction = """
Output Format Requirements:
1. Titles: 5 variations, each 60-70 characters, optimized for CTR
2. Descriptions: 3 versions, 150-200 words each, with clear CTAs
3. Tags: 15-20 relevant tags, mix of broad and specific terms
4. Thumbnail Text: 3-5 short phrases, 1-3 words each, high impact

Please ensure all content is original, engaging, and optimized for YouTube's algorithm.
        """
        
        return prompt + "\n\n" + format_instruction
    
    def create_enhanced_system_prompt(
        self,
        role: str = "YouTube SEO Specialist",
        expertise: List[str] = None,
        tone: str = "engaging"
    ) -> str:
        """Create an enhanced system prompt for AI interactions."""
        
        if expertise is None:
            expertise = ["YouTube Algorithm", "Content Strategy", "SEO Optimization", "Audience Psychology"]
        
        system_prompt = f"""
You are an expert {role} with deep knowledge in {', '.join(expertise)}.

Your expertise includes:
- Advanced YouTube algorithm understanding
- Psychological triggers and engagement optimization
- Audience behavior analysis and targeting
- SEO best practices and keyword optimization
- Content strategy and viral mechanics

Communication Style: {tone.title()} and data-driven
Approach: Provide actionable, specific recommendations
Focus: Maximum engagement and discoverability

Always consider:
1. YouTube's current algorithm preferences
2. Audience psychology and behavior patterns
3. SEO optimization opportunities
4. Competitive landscape analysis
5. Measurable performance indicators

Provide concrete, implementable strategies backed by best practices.
        """
        
        return system_prompt
    
    def enhance_for_local_context(
        self,
        prompt: str,
        location: Optional[str] = None,
        language: str = "English",
        cultural_context: Optional[str] = None
    ) -> str:
        """Enhance prompt with local context and cultural considerations."""
        
        if not location and not cultural_context:
            return prompt
        
        local_context = """
Localization Requirements:
        """
        
        if location:
            local_context += f"\nGeographic Context: {location}"
            local_context += "\nPlease consider local trends, preferences, and cultural nuances."
        
        if language != "English":
            local_context += f"\nLanguage: {language}"
            local_context += "\nEnsure content is culturally appropriate and linguistically natural."
        
        if cultural_context:
            local_context += f"\nCultural Context: {cultural_context}"
            local_context += "\nAdapt messaging to align with cultural values and communication styles."
        
        return prompt + "\n\n" + local_context
    
    def get_tone_examples(self, tone: str) -> Dict[str, List[str]]:
        """Get example phrases and approaches for a specific tone."""
        
        try:
            tone_enum = ContentTone(tone.lower())
            return self.tone_templates[tone_enum]
        except ValueError:
            return self.tone_templates[ContentTone.ENGAGING]
    
    def validate_enhanced_prompt(self, prompt: str) -> Dict[str, Any]:
        """Validate that the enhanced prompt contains necessary elements."""
        
        validation_results = {
            "has_tone_elements": False,
            "has_audience_context": False,
            "has_goal_context": False,
            "has_output_format": False,
            "estimated_quality": "low",
            "suggestions": []
        }
        
        # Check for tone elements
        tone_indicators = ["tone", "style", "approach", "psychological"]
        if any(indicator in prompt.lower() for indicator in tone_indicators):
            validation_results["has_tone_elements"] = True
        
        # Check for audience context
        audience_indicators = ["audience", "target", "demographic", "communication style"]
        if any(indicator in prompt.lower() for indicator in audience_indicators):
            validation_results["has_audience_context"] = True
        
        # Check for goal context
        goal_indicators = ["goal", "objective", "outcome", "success criteria"]
        if any(indicator in prompt.lower() for indicator in goal_indicators):
            validation_results["has_goal_context"] = True
        
        # Check for output format
        format_indicators = ["format", "output", "structure", "titles", "descriptions"]
        if any(indicator in prompt.lower() for indicator in format_indicators):
            validation_results["has_output_format"] = True
        
        # Calculate quality score
        quality_score = sum([
            validation_results["has_tone_elements"],
            validation_results["has_audience_context"],
            validation_results["has_goal_context"],
            validation_results["has_output_format"]
        ])
        
        if quality_score >= 3:
            validation_results["estimated_quality"] = "high"
        elif quality_score >= 2:
            validation_results["estimated_quality"] = "medium"
        else:
            validation_results["estimated_quality"] = "low"
        
        # Generate suggestions
        if not validation_results["has_tone_elements"]:
            validation_results["suggestions"].append("Add specific tone and style requirements")
        if not validation_results["has_audience_context"]:
            validation_results["suggestions"].append("Include target audience characteristics")
        if not validation_results["has_goal_context"]:
            validation_results["suggestions"].append("Define clear goals and success criteria")
        if not validation_results["has_output_format"]:
            validation_results["suggestions"].append("Specify desired output format and structure")
        
        return validation_results

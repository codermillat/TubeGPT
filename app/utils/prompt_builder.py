"""
Prompt Builder Module for YouTube Analytics AI Assistant.
Handles prompt construction, language detection, and system prompt loading.
"""

import os
import logging
import re
import unicodedata
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# FIXED: Set up logging first before any usage
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# FIXED: Safe import with proper error handling
try:
    from prompt_templates import get_contextual_prompt
    PROMPT_TEMPLATES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Prompt templates not available: {e}")
    PROMPT_TEMPLATES_AVAILABLE = False

def detect_language(text: str) -> str:
    """
    Detect if the input text is in Bengali (bn) or English (en).
    FIXED: Added division-by-zero protection and better error handling.
    
    Args:
        text (str): Input text to analyze
        
    Returns:
        str: 'bn' for Bengali, 'en' for English
    """
    if not text or not text.strip():
        return 'en'  # Default to English for empty text
    
    # Clean the text
    text = text.strip().lower()
    
    # Count Bengali characters (Unicode range for Bengali script)
    bengali_chars = 0
    english_chars = 0
    total_chars = 0
    
    for char in text:
        if char.isspace() or char in '.,!?;:()[]{}"\'-':
            continue  # Skip whitespace and punctuation
            
        total_chars += 1
        
        # Check if character is in Bengali Unicode range
        if '\u0980' <= char <= '\u09FF':  # Bengali Unicode block
            bengali_chars += 1
        elif char.isalpha() and ord(char) < 128:  # ASCII letters (English)
            english_chars += 1
    
    # FIXED: Prevent division by zero
    if total_chars == 0:
        logger.debug("No meaningful characters found in text, defaulting to English")
        return 'en'
    
    # Calculate percentages
    bengali_percentage = bengali_chars / total_chars
    english_percentage = english_chars / total_chars
    
    # Decision logic
    if bengali_percentage > 0.3:  # If more than 30% Bengali characters
        return 'bn'
    elif english_percentage > 0.5:  # If more than 50% English characters
        return 'en'
    else:
        # Additional heuristics for mixed or unclear text
        bengali_words = [
            'আমি', 'তুমি', 'সে', 'আমরা', 'তোমরা', 'তারা',
            'কি', 'কীভাবে', 'কেন', 'কোথায়', 'কখন', 'কোন',
            'ভিডিও', 'চ্যানেল', 'ভিউ', 'সাবস্ক্রাইব', 'কন্টেন্ট'
        ]
        
        english_words = [
            'video', 'channel', 'views', 'subscribers', 'content',
            'performance', 'analytics', 'what', 'how', 'why', 'when', 'where'
        ]
        
        # Count word matches
        bengali_word_count = sum(1 for word in bengali_words if word in text)
        english_word_count = sum(1 for word in english_words if word in text)
        
        if bengali_word_count > english_word_count:
            return 'bn'
        else:
            return 'en'

def load_system_prompt(language: str) -> str:
    """
    Load system prompt based on detected language.
    FIXED: Added better error handling and fallback mechanisms.
    
    Args:
        language (str): Language code ('bn' or 'en')
        
    Returns:
        str: System prompt text
    """
    try:
        prompt_file = f"prompts/system_prompt_{language}.txt"
        
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
                if prompt:  # FIXED: Check if prompt is not empty
                    return prompt
                else:
                    logger.warning(f"System prompt file {prompt_file} is empty")
        else:
            logger.warning(f"System prompt file not found: {prompt_file}")
        
        # Fallback to English prompt
        fallback_file = "prompts/system_prompt_en.txt"
        if os.path.exists(fallback_file):
            with open(fallback_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
                if prompt:
                    return prompt
                else:
                    logger.warning(f"Fallback prompt file {fallback_file} is empty")
        
        # FIXED: Hard-coded fallback if no files exist
        logger.warning("No system prompt files found, using hard-coded fallback")
        return """You are a YouTube analytics expert. Analyze the following YouTube channel data and answer the user's question with data-driven insights and actionable recommendations."""
                
    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        return """You are a YouTube analytics expert. Analyze the following YouTube channel data and answer the user's question with data-driven insights and actionable recommendations."""

class PromptBuilder:
    """
    Builds prompts for YouTube analytics analysis with contextual information.
    """
    
    def __init__(self):
        """Initialize the prompt builder."""
        self.system_prompts = {}
        logger.info("Prompt builder initialized")
    
    def build_analysis_prompt(self, user_question: str, data_summary: Dict[str, Any], 
                            session_context: str = "") -> str:
        """
        Build a comprehensive prompt for YouTube analytics analysis.
        
        Args:
            user_question (str): The user's question about the YouTube data
            data_summary (dict): Statistical summary of the CSV data
            session_context (str): Previous conversation context
            
        Returns:
            str: Formatted prompt for AI analysis
        """
        # FIXED: Input validation
        if not user_question or not user_question.strip():
            user_question = "Please analyze the YouTube analytics data and provide insights."
        
        if not isinstance(data_summary, dict):
            data_summary = {}
        
        # Detect language and load appropriate system prompt
        detected_language = detect_language(user_question)
        logger.info(f"Detected language: {detected_language}")
        
        # Load system prompt with caching
        if detected_language not in self.system_prompts:
            self.system_prompts[detected_language] = load_system_prompt(detected_language)
        
        system_prompt = self.system_prompts[detected_language]
        
        # Build data summary for prompt
        data_summary_text = self._format_data_summary(data_summary)
        
        # Build the complete prompt
        prompt_parts = [
            system_prompt,
            "\n\nDATA SUMMARY:",
            data_summary_text
        ]
        
        # Add session context if available
        if session_context and session_context.strip():
            prompt_parts.extend([
                "\n\nPREVIOUS CONVERSATION CONTEXT:",
                session_context.strip()
            ])
        
        # Add user question
        prompt_parts.extend([
            "\n\nUSER QUESTION:",
            user_question.strip(),
            "\n\nPlease provide a comprehensive analysis with specific insights and actionable recommendations."
        ])
        
        return "\n".join(prompt_parts)
    
    def _format_data_summary(self, summary: Dict[str, Any]) -> str:
        """
        Format data summary for inclusion in prompt.
        
        Args:
            summary (dict): Data summary dictionary
            
        Returns:
            str: Formatted data summary text
        """
        if not summary:
            return "No data summary available."
        
        # FIXED: Safe data extraction with fallbacks
        formatted_parts = []
        
        # Basic info
        total_videos = summary.get('total_videos', 0)
        date_range = summary.get('date_range', {})
        formatted_parts.append(f"Total Videos: {total_videos}")
        
        if date_range:
            earliest = date_range.get('earliest', 'Unknown')
            latest = date_range.get('latest', 'Unknown')
            formatted_parts.append(f"Date Range: {earliest} to {latest}")
        
        # Performance metrics
        if 'views_stats' in summary:
            views = summary['views_stats']
            formatted_parts.append(f"Views Analysis:")
            formatted_parts.append(f"  - Total Views: {views.get('total', 0):,}")
            formatted_parts.append(f"  - Average Views per Video: {views.get('average', 0):,.0f}")
            formatted_parts.append(f"  - Median Views: {views.get('median', 0):,}")
            formatted_parts.append(f"  - Highest Views: {views.get('max', 0):,}")
        
        if 'ctr_stats' in summary:
            ctr = summary['ctr_stats']
            formatted_parts.append(f"Click-Through Rate (CTR) Analysis:")
            formatted_parts.append(f"  - Average CTR: {ctr.get('average', 0):.2f}%")
            formatted_parts.append(f"  - Median CTR: {ctr.get('median', 0):.2f}%")
            formatted_parts.append(f"  - Highest CTR: {ctr.get('max', 0):.2f}%")
        
        if 'duration_stats' in summary:
            duration = summary['duration_stats']
            formatted_parts.append(f"Average View Duration Analysis:")
            formatted_parts.append(f"  - Average Duration: {duration.get('average', 0):.1f} seconds")
            formatted_parts.append(f"  - Median Duration: {duration.get('median', 0):.1f} seconds")
        
        # Top countries
        if 'top_countries' in summary:
            countries = summary['top_countries']
            formatted_parts.append(f"Top Countries: {', '.join(list(countries.keys())[:3])}")
        
        return "\n".join(formatted_parts) if formatted_parts else "No detailed metrics available."
    
    def build_comparison_prompt(self, user_question: str, comparison_data: Dict[str, Any]) -> str:
        """
        Build prompt for CSV comparison analysis.
        
        Args:
            user_question (str): User's comparison question
            comparison_data (dict): Comparison results
            
        Returns:
            str: Formatted comparison prompt
        """
        # FIXED: Input validation
        if not user_question or not user_question.strip():
            user_question = "Please compare the YouTube analytics data."
        
        if not isinstance(comparison_data, dict):
            comparison_data = {}
        
        detected_language = detect_language(user_question)
        system_prompt = load_system_prompt(detected_language)
        
        # Format comparison data
        comparison_text = self._format_comparison_data(comparison_data)
        
        prompt_parts = [
            system_prompt,
            "\n\nCOMPARISON ANALYSIS:",
            comparison_text,
            "\n\nUSER QUESTION:",
            user_question.strip(),
            "\n\nPlease provide insights about the differences and trends shown in the comparison."
        ]
        
        return "\n".join(prompt_parts)
    
    def _format_comparison_data(self, comparison_data: Dict[str, Any]) -> str:
        """
        Format comparison data for prompt inclusion.
        
        Args:
            comparison_data (dict): Comparison results
            
        Returns:
            str: Formatted comparison text
        """
        if not comparison_data:
            return "No comparison data available."
        
        # FIXED: Safe formatting with error handling
        try:
            formatted_parts = []
            
            if 'summary' in comparison_data:
                formatted_parts.append(comparison_data['summary'])
            
            if 'top_changes' in comparison_data:
                changes = comparison_data['top_changes']
                formatted_parts.append("Top Changes:")
                for change in changes[:5]:  # Show top 5 changes
                    formatted_parts.append(f"  - {change}")
            
            return "\n".join(formatted_parts) if formatted_parts else "No comparison details available."
        
        except Exception as e:
            logger.error(f"Error formatting comparison data: {e}")
            return "Error formatting comparison data." 
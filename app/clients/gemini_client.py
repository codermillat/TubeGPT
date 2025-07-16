"""
Gemini API Client with retry logic and fallback mechanisms.
Handles all communication with Google's Gemini Pro model.
"""

import os
import time
import logging
import google.generativeai as genai
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import random

# FIXED: Set up logging first before any usage
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors."""
    pass

class GeminiClient:
    """
    Gemini API client with retry logic and fallback mechanisms.
    """
    
    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3):
        """
        Initialize the Gemini client.
        
        Args:
            api_key (str, optional): Gemini API key. Uses env var if not provided.
            max_retries (int): Maximum number of retry attempts
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.max_retries = max_retries
        self.model = None
        
        if not self.api_key:
            logger.warning(
                "Gemini API key not found. Client will be in fallback mode. "
                "Set GEMINI_API_KEY environment variable for full functionality."
            )
            return
        
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        return self.model is not None
    
    def generate_with_retry(self, prompt: str, fallback_response: str = None) -> str:
        """
        Generate content with retry logic and fallback.
        
        Args:
            prompt (str): The prompt to send to Gemini
            fallback_response (str): Response to return if API fails
            
        Returns:
            str: Generated content or fallback response
        """
        if not self.is_available():
            logger.warning("Gemini API not available, using fallback")
            return fallback_response or "I'm sorry, I cannot process this request right now. Please try again later."
        
        # FIXED: Added exponential backoff retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to Gemini (attempt {attempt + 1}/{self.max_retries})")
                response = self.model.generate_content(prompt)
                
                # FIXED: Validate response before returning
                if response and response.text and response.text.strip():
                    logger.info("Received valid response from Gemini")
                    return response.text.strip()
                else:
                    logger.warning("Received empty or invalid response from Gemini")
                    if attempt == self.max_retries - 1:
                        break
                    continue
                    
            except Exception as e:
                logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                
                # FIXED: Check for specific error types
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    logger.error("API quota or rate limit exceeded")
                    if attempt < self.max_retries - 1:
                        # FIXED: Exponential backoff with jitter
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    break
                elif "authentication" in str(e).lower() or "key" in str(e).lower():
                    logger.error("API authentication failed")
                    break
                else:
                    # FIXED: Generic error with backoff
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.info(f"Retrying in {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                        continue
                    break
        
        # FIXED: Return fallback response when all retries failed
        logger.error("All retry attempts failed, using fallback response")
        return fallback_response or "I encountered an error while processing your request. Please try again later or rephrase your question."
    
    def test_connection(self) -> bool:
        """
        Test connection to Gemini API.
        
        Returns:
            bool: True if connection is successful
        """
        if not self.is_available():
            return False
        
        try:
            test_prompt = "Hello, please respond with 'API_TEST_SUCCESS'"
            response = self.generate_with_retry(test_prompt, fallback_response="")
            return "API_TEST_SUCCESS" in response
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False 
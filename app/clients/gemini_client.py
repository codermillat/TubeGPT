"""
Gemini API Client with retry logic and fallback mechanisms.
Handles all communication with Google's Gemini Pro model.
"""

import os
import time
import logging
import asyncio
import random
import google.generativeai as genai
from typing import Optional, Dict, Any
from dotenv import load_dotenv

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
        
        # Timeout configuration
        self.request_timeout = 60.0  # 60 seconds for Gemini API
        self.max_backoff = 60.0     # Maximum backoff delay
        
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
    
    async def generate_with_retry(self, prompt: str, fallback_response: str = None) -> str:
        """
        Generate content with retry logic, timeout and fallback.
        
        Args:
            prompt (str): The prompt to send to Gemini
            fallback_response (str): Response to return if API fails
            
        Returns:
            str: Generated content or fallback response
        """
        if not self.is_available():
            logger.warning("Gemini API not available, using fallback")
            return fallback_response or "I'm sorry, I cannot process this request right now. Please try again later."
        
        # Import input sanitizer and sanitize prompt
        from app.core.security import input_sanitizer
        sanitized_prompt = input_sanitizer.sanitize_prompt(prompt, "gemini_api")
        
        # FIXED: Added exponential backoff retry logic with timeout
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to Gemini (attempt {attempt + 1}/{self.max_retries})")
                
                # Use asyncio to add timeout to the synchronous call
                def _generate():
                    return self.model.generate_content(sanitized_prompt)
                
                # Run with timeout
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, _generate),
                    timeout=self.request_timeout
                )
                
                # FIXED: Validate response before returning
                if response and response.text and response.text.strip():
                    logger.info("Received valid response from Gemini")
                    return response.text.strip()
                else:
                    logger.warning("Received empty or invalid response from Gemini")
                    if attempt == self.max_retries - 1:
                        break
                    continue
                    
            except asyncio.TimeoutError:
                logger.error(f"Gemini API timeout after {self.request_timeout}s (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    break
                    
            except Exception as e:
                logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                
                # FIXED: Check for specific error types
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    logger.error("API quota or rate limit exceeded")
                    if attempt < self.max_retries - 1:
                        # FIXED: Exponential backoff with jitter
                        delay = min(2 ** attempt + random.uniform(0, 1), self.max_backoff)
                        logger.info(f"Rate limited, waiting {delay:.1f}s before retry...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
                elif "network" in str(e).lower() or "connection" in str(e).lower():
                    logger.error("Network connectivity issue")
                    if attempt < self.max_retries - 1:
                        delay = min(1.5 ** attempt, 10.0)  # Shorter delay for network issues
                        await asyncio.sleep(delay)
                        continue
                else:
                    # Unknown error, retry with exponential backoff
                    if attempt < self.max_retries - 1:
                        delay = min(2 ** attempt, self.max_backoff)
                        await asyncio.sleep(delay)
                        continue
                    break
        
        # All retries failed, use fallback
        logger.error("All Gemini API attempts failed, using fallback")
        return fallback_response or "I apologize, but I'm experiencing technical difficulties. Please try again later."
    
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
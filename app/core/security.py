"""
Input sanitization for AI prompts and user inputs.

Cursor Rules:
- Sanitize all user inputs before passing to AI models
- Remove potentially malicious content and injection attempts
- Validate input length and structure
- Log sanitization events for security monitoring
"""

import html
import re
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitize user inputs for AI model consumption and general security."""
    
    def __init__(self):
        """Initialize sanitizer with security patterns."""
        # Dangerous script patterns
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',           # Script tags
            r'javascript:',                        # JavaScript protocol
            r'vbscript:',                         # VBScript protocol
            r'data:.*base64',                     # Base64 data URLs
            r'data:text/html',                    # HTML data URLs
            r'<iframe[^>]*>.*?</iframe>',        # Iframes
            r'<object[^>]*>.*?</object>',        # Objects
            r'<embed[^>]*>.*?</embed>',          # Embeds
            r'<applet[^>]*>.*?</applet>',        # Applets
            r'<form[^>]*>.*?</form>',            # Forms
            r'<input[^>]*>',                     # Input elements
            r'<link[^>]*>',                      # Link elements
            r'<meta[^>]*>',                      # Meta elements
            r'onload\s*=',                       # Event handlers
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'onerror\s*=',
            r'expression\s*\(',                  # CSS expressions
            r'@import\s+',                       # CSS imports
            r'url\s*\(',                        # CSS URLs
        ]
        
        # Prompt injection patterns
        self.prompt_injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'ignore\s+all\s+previous\s+instructions',
            r'ignore\s+the\s+above',
            r'forget\s+everything',
            r'you\s+are\s+now',
            r'new\s+instructions',
            r'system\s*:',
            r'assistant\s*:',
            r'human\s*:',
            r'</\s*instructions\s*>',
            r'<\s*instructions\s*>',
            r'###\s*instruction',
            r'role\s*:\s*system',
        ]
        
        # Maximum lengths
        self.max_prompt_length = 10000
        self.max_field_length = 5000
        self.max_title_length = 200
        
    def sanitize_prompt(self, text: str, context: str = "general") -> str:
        """
        Sanitize text for AI prompt consumption.
        
        Args:
            text: Input text to sanitize
            context: Context for logging (e.g., 'video_analysis', 'strategy_generation')
            
        Returns:
            Sanitized text safe for AI consumption
        """
        if not text or not isinstance(text, str):
            return ""
        
        original_length = len(text)
        sanitized = text
        
        try:
            # 1. HTML decode first
            sanitized = html.unescape(sanitized)
            
            # 2. URL decode
            sanitized = unquote(sanitized)
            
            # 3. Remove null bytes and control characters
            sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)
            
            # 4. Remove dangerous script patterns
            for pattern in self.dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            # 5. Remove prompt injection attempts
            for pattern in self.prompt_injection_patterns:
                if re.search(pattern, sanitized, re.IGNORECASE):
                    logger.warning(f"Prompt injection attempt detected in {context}: {pattern}")
                    sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE)
            
            # 6. Normalize whitespace
            sanitized = re.sub(r'\s+', ' ', sanitized)
            sanitized = sanitized.strip()
            
            # 7. Enforce length limits
            if len(sanitized) > self.max_prompt_length:
                sanitized = sanitized[:self.max_prompt_length] + "... [TRUNCATED]"
                logger.warning(f"Prompt truncated in {context}: {original_length} -> {len(sanitized)} chars")
            
            # 8. Log if significant changes were made
            if len(sanitized) < original_length * 0.9:
                logger.info(f"Significant sanitization in {context}: {original_length} -> {len(sanitized)} chars")
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing prompt in {context}: {e}")
            # Return a safe fallback
            return text[:100] + "... [SANITIZATION_ERROR]" if len(text) > 100 else text
    
    def sanitize_field(self, text: str, field_name: str = "field") -> str:
        """
        Sanitize individual form fields or data fields.
        
        Args:
            text: Input text to sanitize
            field_name: Name of the field for logging
            
        Returns:
            Sanitized field value
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            sanitized = text.strip()
            
            # HTML decode
            sanitized = html.unescape(sanitized)
            
            # Remove dangerous patterns
            for pattern in self.dangerous_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove control characters but keep newlines for descriptions
            if field_name.lower() in ['description', 'content', 'text']:
                sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)
            else:
                sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
            
            # Enforce field-specific length limits
            max_length = self.max_title_length if 'title' in field_name.lower() else self.max_field_length
            
            if len(sanitized) > max_length:
                sanitized = sanitized[:max_length]
                logger.warning(f"Field '{field_name}' truncated: {len(text)} -> {len(sanitized)} chars")
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing field '{field_name}': {e}")
            return text[:100] if len(text) > 100 else text
    
    def sanitize_dict(self, data: Dict[str, Any], context: str = "data") -> Dict[str, Any]:
        """
        Sanitize all string values in a dictionary recursively.
        
        Args:
            data: Dictionary to sanitize
            context: Context for logging
            
        Returns:
            Dictionary with sanitized string values
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        try:
            for key, value in data.items():
                # Sanitize the key itself
                clean_key = self.sanitize_field(str(key), "dict_key") if isinstance(key, str) else key
                
                # Sanitize the value based on type
                if isinstance(value, str):
                    sanitized[clean_key] = self.sanitize_field(value, f"{context}.{clean_key}")
                elif isinstance(value, dict):
                    sanitized[clean_key] = self.sanitize_dict(value, f"{context}.{clean_key}")
                elif isinstance(value, list):
                    sanitized[clean_key] = self.sanitize_list(value, f"{context}.{clean_key}")
                else:
                    # Keep other types as-is (numbers, booleans, etc.)
                    sanitized[clean_key] = value
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing dictionary in {context}: {e}")
            return data
    
    def sanitize_list(self, data: List[Any], context: str = "list") -> List[Any]:
        """
        Sanitize all string values in a list recursively.
        
        Args:
            data: List to sanitize
            context: Context for logging
            
        Returns:
            List with sanitized string values
        """
        if not isinstance(data, list):
            return data
        
        sanitized = []
        
        try:
            for i, value in enumerate(data):
                if isinstance(value, str):
                    sanitized.append(self.sanitize_field(value, f"{context}[{i}]"))
                elif isinstance(value, dict):
                    sanitized.append(self.sanitize_dict(value, f"{context}[{i}]"))
                elif isinstance(value, list):
                    sanitized.append(self.sanitize_list(value, f"{context}[{i}]"))
                else:
                    sanitized.append(value)
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing list in {context}: {e}")
            return data
    
    def is_safe_prompt(self, text: str) -> bool:
        """
        Check if a prompt is safe without modifying it.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears safe, False otherwise
        """
        if not text or not isinstance(text, str):
            return True
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns + self.prompt_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Check length
        if len(text) > self.max_prompt_length:
            return False
        
        return True


# Global sanitizer instance
input_sanitizer = InputSanitizer()

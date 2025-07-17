"""
AI Service for YouTube SEO Assistant.

Cursor Rules:
- Use dependency injection for all external dependencies
- Implement proper async/await patterns
- Add comprehensive error handling with structured logging
- Write tests for all public methods
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any

from app.core.config import settings
from app.core.exceptions import AIServiceException, GeminiAPIException
from app.core.logging import ServiceLogger
from app.core.security import input_sanitizer
from app.clients.gemini_client import GeminiClient
from app.services.cache_service import CacheService

# Initialize service logger
logger = ServiceLogger("ai_service")


class AIService:
    """Service for AI-powered YouTube SEO analysis."""
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize AI service with dependencies.
        
        Args:
            gemini_client: Gemini AI client for API calls
            cache_service: Optional cache service for response caching
        """
        self.gemini_client = gemini_client
        self.cache_service = cache_service
        self.logger = logger
    
    async def analyze_video(
        self,
        video_data: Dict[str, Any],
        analysis_type: str = "seo"
    ) -> Dict[str, Any]:
        """
        Analyze video with AI insights.
        
        Args:
            video_data: Video data from YouTube API
            analysis_type: Type of analysis to perform
            
        Returns:
            AI analysis results
            
        Raises:
            AIServiceException: If analysis fails
        """
        start_time = time.time()
        video_id = video_data.get("id", "unknown")
        
        bound_logger = self.logger.bind_operation(
            "analyze_video",
            video_id=video_id,
            analysis_type=analysis_type
        )
        
        try:
            bound_logger.info("Starting video analysis")
            
            # Check cache first
            cache_key = f"video_analysis:{video_id}:{analysis_type}"
            if self.cache_service:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    bound_logger.info("Cache hit for video analysis")
                    return cached_result
            
            # Generate analysis prompt with sanitization
            prompt = self._build_analysis_prompt(video_data, analysis_type)
            
            # Call Gemini API with retry and timeout
            response = await self.gemini_client.generate_with_retry(
                prompt,
                fallback_response=f"Unable to analyze video at this time. Analysis type: {analysis_type}"
            )
            
            # Parse and structure response
            analysis_result = self._parse_analysis_response(response, analysis_type)
            
            # Cache result
            if self.cache_service:
                await self.cache_service.set(cache_key, analysis_result)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "analyze_video",
                duration_ms=duration_ms,
                result_summary={"insights_count": len(analysis_result.get("insights", []))},
                video_id=video_id
            )
            
            return analysis_result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "analyze_video",
                error=e,
                duration_ms=duration_ms,
                video_id=video_id
            )
            raise AIServiceException(
                f"Failed to analyze video {video_id}: {str(e)}",
                context={"video_id": video_id, "analysis_type": analysis_type}
            ) from e
    
    async def generate_content_suggestions(
        self,
        channel_data: Dict[str, Any],
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered content suggestions.
        
        Args:
            channel_data: Channel analytics data
            count: Number of suggestions to generate
            
        Returns:
            List of content suggestions
            
        Raises:
            AIServiceException: If generation fails
        """
        start_time = time.time()
        channel_id = channel_data.get("id", "unknown")
        
        bound_logger = self.logger.bind_operation(
            "generate_content_suggestions",
            channel_id=channel_id,
            count=count
        )
        
        try:
            bound_logger.info("Starting content suggestion generation")
            
            # Check cache
            cache_key = f"content_suggestions:{channel_id}:{count}"
            if self.cache_service:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    bound_logger.info("Cache hit for content suggestions")
                    return cached_result
            
            # Generate suggestions
            suggestions = []
            for i in range(count):
                prompt = self._build_suggestion_prompt(channel_data, i)
                response = await self.gemini_client.generate_response(prompt)
                suggestion = self._parse_suggestion_response(response)
                suggestions.append(suggestion)
            
            # Cache result
            if self.cache_service:
                await self.cache_service.set(cache_key, suggestions)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "generate_content_suggestions",
                duration_ms=duration_ms,
                result_summary={"suggestions_count": len(suggestions)},
                channel_id=channel_id
            )
            
            return suggestions
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "generate_content_suggestions",
                error=e,
                duration_ms=duration_ms,
                channel_id=channel_id
            )
            raise AIServiceException(
                f"Failed to generate content suggestions: {str(e)}",
                context={"channel_id": channel_id, "count": count}
            ) from e
    
    async def process_question(
        self,
        question: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user question with AI.
        
        Args:
            question: User question
            context_data: Optional context data
            
        Returns:
            AI response
            
        Raises:
            AIServiceException: If processing fails
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "process_question",
            question_length=len(question),
            has_context=context_data is not None
        )
        
        try:
            bound_logger.info("Starting question processing")
            
            # Check cache
            cache_key = f"question:{hash(question + str(context_data or {}))}"
            if self.cache_service:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    bound_logger.info("Cache hit for question processing")
                    return cached_result
            
            # Build prompt with context
            prompt = self._build_question_prompt(question, context_data)
            
            # Get AI response
            response = await self.gemini_client.generate_response(prompt)
            
            # Structure response
            result = {
                "question": question,
                "response": response,
                "timestamp": time.time(),
                "success": True
            }
            
            # Cache result
            if self.cache_service:
                await self.cache_service.set(cache_key, result)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "process_question",
                duration_ms=duration_ms,
                result_summary={"response_length": len(response)}
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "process_question",
                error=e,
                duration_ms=duration_ms
            )
            raise AIServiceException(
                f"Failed to process question: {str(e)}",
                context={"question": question[:100] + "..."}
            ) from e
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for AI service.
        
        Returns:
            Health check results
        """
        try:
            # Test Gemini client
            test_response = await self.gemini_client.generate_response("Test")
            
            # Test cache if available
            cache_healthy = True
            if self.cache_service:
                try:
                    await self.cache_service.set("health_check", "ok")
                    cache_result = await self.cache_service.get("health_check")
                    cache_healthy = cache_result == "ok"
                except Exception:
                    cache_healthy = False
            
            return {
                "status": "healthy",
                "gemini_client": bool(test_response),
                "cache_service": cache_healthy,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _build_analysis_prompt(
        self,
        video_data: Dict[str, Any],
        analysis_type: str
    ) -> str:
        """Build analysis prompt for video with input sanitization."""
        # Sanitize input data before building prompt
        video_data = input_sanitizer.sanitize_dict(video_data, "video_analysis")
        
        title = video_data.get("snippet", {}).get("title", "")
        description = video_data.get("snippet", {}).get("description", "")
        tags = video_data.get("snippet", {}).get("tags", [])
        statistics = video_data.get("statistics", {})
        
        # Additional sanitization for critical fields
        title = input_sanitizer.sanitize_field(title, "video_title")
        description = input_sanitizer.sanitize_field(description[:500], "video_description") 
        
        prompt = f"""
        Analyze this YouTube video for {analysis_type} optimization:
        
        Title: {title}
        Description: {description}...
        Tags: {', '.join(tags[:10])}
        Views: {statistics.get('viewCount', 0)}
        Likes: {statistics.get('likeCount', 0)}
        Comments: {statistics.get('commentCount', 0)}
        
        Provide specific, actionable recommendations for:
        1. Title optimization
        2. Description improvement
        3. Tag suggestions
        4. Engagement strategies
        5. Content improvements
        
        Format response as structured insights with confidence scores.
        """
        
        return prompt
    
    def _build_suggestion_prompt(
        self,
        channel_data: Dict[str, Any],
        index: int
    ) -> str:
        """Build content suggestion prompt."""
        channel_title = channel_data.get("snippet", {}).get("title", "")
        channel_description = channel_data.get("snippet", {}).get("description", "")
        
        prompt = f"""
        Generate a video content suggestion for this YouTube channel:
        
        Channel: {channel_title}
        Description: {channel_description[:300]}...
        
        Create suggestion #{index + 1} that:
        1. Fits the channel's style and audience
        2. Has high engagement potential
        3. Is timely and relevant
        4. Includes SEO-optimized title and description
        5. Suggests relevant tags
        
        Format as: Title, Description, Tags, Expected Performance
        """
        
        return prompt
    
    def _build_question_prompt(
        self,
        question: str,
        context_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build question processing prompt."""
        context_str = ""
        if context_data:
            context_str = f"Context: {json.dumps(context_data, indent=2)}"
        
        prompt = f"""
        You are an expert YouTube SEO assistant. Answer this question:
        
        Question: {question}
        
        {context_str}
        
        Provide a helpful, specific answer with actionable advice.
        Focus on practical YouTube SEO strategies and best practices.
        """
        
        return prompt
    
    def _parse_analysis_response(
        self,
        response: str,
        analysis_type: str
    ) -> Dict[str, Any]:
        """Parse AI analysis response."""
        try:
            # Try to parse structured response
            if response.startswith("{"):
                return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Fallback to plain text parsing
        return {
            "type": analysis_type,
            "insights": [response],
            "confidence": 0.8,
            "timestamp": time.time()
        }
    
    async def generate_content_async(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI content based on prompt and context.
        
        Args:
            prompt: The prompt for content generation
            context: Optional context dictionary
            
        Returns:
            Generated content string
            
        Raises:
            AIServiceException: If generation fails
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "generate_content_async",
            prompt_length=len(prompt),
            has_context=bool(context)
        )
        
        try:
            bound_logger.info("Starting AI content generation")
            
            # Sanitize inputs
            sanitized_prompt = input_sanitizer.sanitize_text(prompt)
            
            # Check cache if available
            cache_key = f"content_generation:{hash(sanitized_prompt)}"
            if self.cache_service:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    bound_logger.info("Returning cached content generation result")
                    return cached_result["content"]
            
            # Generate content with Gemini
            response = await self.gemini_client.generate_content(
                prompt=sanitized_prompt,
                context=context or {}
            )
            
            # Cache result if available
            if self.cache_service:
                await self.cache_service.set(
                    cache_key,
                    {"content": response, "timestamp": time.time()},
                    ttl=3600  # 1 hour cache
                )
            
            execution_time = time.time() - start_time
            bound_logger.info(
                "Content generation completed",
                execution_time=execution_time,
                response_length=len(response)
            )
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            bound_logger.error(
                "Content generation failed",
                error=str(e),
                execution_time=execution_time
            )
            raise AIServiceException(
                f"Failed to generate content: {e}",
                context={"prompt_length": len(prompt), "has_context": bool(context)}
            ) from e
    
    def _parse_suggestion_response(self, response: str) -> Dict[str, Any]:
        """Parse content suggestion response."""
        lines = response.strip().split('\n')
        
        return {
            "title": lines[0] if lines else "Video Suggestion",
            "description": lines[1] if len(lines) > 1 else "",
            "tags": lines[2].split(', ') if len(lines) > 2 else [],
            "confidence": 0.85,
            "timestamp": time.time()
        } 
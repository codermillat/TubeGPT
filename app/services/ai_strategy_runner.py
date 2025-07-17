"""
AI Strategy Runner - Central coordinator for YouTube SEO analysis pipeline.

This module orchestrates the complete analysis pipeline:
1. Keyword analysis with trends data
2. Content gap detection
3. AI-powered prompt generation
4. Gemini-based content optimization
5. Psychological metadata enhancement

Features:
- Dependency injection pattern
- Async execution with proper error handling
- Correlation ID tracking for logs
- Time measurement per pipeline step
- Clean JSON output with full SEO metadata
- Fallback mechanisms for AI services
"""

import asyncio
import json
import logging
import time
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

from app.core.config import settings
from app.services.keyword_analyzer import KeywordAnalyzer
from app.services.gap_detector import GapDetector
from app.services.emotion_optimizer import EmotionOptimizer
from app.services.prompt_enhancer import PromptEnhancer
from app.utils.prompt_builder import PromptBuilder
from app.utils.csv_validator import validate_csv_file

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIStrategyRunner:
    """
    Central coordinator for the AI-powered YouTube SEO analysis pipeline.
    
    Chains together multiple analysis services to generate comprehensive
    content strategy with keyword insights, gap analysis, and AI optimization.
    """
    
    def __init__(self, correlation_id: Optional[str] = None, verbose: bool = False):
        """
        Initialize the AI Strategy Runner.
        
        Args:
            correlation_id: Optional correlation ID for tracking logs
            verbose: Enable verbose logging for debugging
        """
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]
        self.verbose = verbose
        self.start_time = time.time()
        
        if self.verbose:
            logger.setLevel(logging.DEBUG)
        
        # Initialize services with dependency injection
        self.keyword_analyzer = KeywordAnalyzer()
        self.gap_detector = GapDetector()
        self.emotion_optimizer = EmotionOptimizer()
        self.prompt_enhancer = PromptEnhancer()
        self.prompt_builder = PromptBuilder()
        
        # Initialize Gemini AI
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("GEMINI_API_KEY not found, AI generation will use fallbacks")
            self.gemini_model = None
        
        # Performance tracking
        self.step_times = {}
        
        logger.info(f"[{self.correlation_id}] AI Strategy Runner initialized")
    
    async def run_full_analysis(
        self,
        csv_file: str,
        goal: str,
        audience: Optional[str] = None,
        tone: str = "engaging"
    ) -> Dict[str, Any]:
        """
        Run the complete AI-powered analysis pipeline.
        
        Args:
            csv_file: Path to CSV file with YouTube data
            goal: Analysis goal and requirements
            audience: Target audience description
            tone: Content tone (curiosity, authority, fear, persuasive, engaging)
            
        Returns:
            Dict containing complete analysis results and SEO metadata
        """
        
        logger.info(f"[{self.correlation_id}] Starting full analysis pipeline")
        logger.info(f"[{self.correlation_id}] Goal: {goal}")
        logger.info(f"[{self.correlation_id}] Audience: {audience}")
        logger.info(f"[{self.correlation_id}] Tone: {tone}")
        
        try:
            # Step 1: Load and validate data
            step_start = time.time()
            data = await self._load_csv_data(csv_file)
            self.step_times["data_loading"] = time.time() - step_start
            logger.info(f"[{self.correlation_id}] ✅ Data loaded ({len(data)} rows)")
            
            # Step 2: Keyword analysis
            step_start = time.time()
            keywords_result = await self._run_keyword_analysis(data, goal)
            self.step_times["keyword_analysis"] = time.time() - step_start
            logger.info(f"[{self.correlation_id}] ✅ Keywords analyzed ({len(keywords_result.get('keywords', []))} found)")
            
            # Step 3: Content gap detection
            step_start = time.time()
            gaps_result = await self._run_gap_detection(data, goal, audience)
            self.step_times["gap_detection"] = time.time() - step_start
            logger.info(f"[{self.correlation_id}] ✅ Gaps detected ({len(gaps_result.get('gaps', []))} found)")
            
            # Step 4: Build AI prompts
            step_start = time.time()
            prompt_context = await self._build_prompt_context(
                keywords_result, gaps_result, goal, audience, tone
            )
            self.step_times["prompt_building"] = time.time() - step_start
            logger.info(f"[{self.correlation_id}] ✅ AI prompts built")
            
            # Step 5: Generate AI-optimized content
            step_start = time.time()
            ai_content = await self._generate_ai_content(prompt_context)
            self.step_times["ai_generation"] = time.time() - step_start
            logger.info(f"[{self.correlation_id}] ✅ AI content generated")
            
            # Step 6: Apply psychological optimization
            step_start = time.time()
            optimized_content = await self._apply_psychological_optimization(
                ai_content, tone, audience, goal
            )
            self.step_times["psychological_optimization"] = time.time() - step_start
            logger.info(f"[{self.correlation_id}] ✅ Psychological optimization applied")
            
            # Step 7: Compile final results
            step_start = time.time()
            final_result = await self._compile_final_results(
                keywords_result,
                gaps_result,
                optimized_content,
                goal,
                audience,
                tone
            )
            self.step_times["compilation"] = time.time() - step_start
            
            total_time = time.time() - self.start_time
            logger.info(f"[{self.correlation_id}] ✅ Pipeline completed in {total_time:.2f}s")
            
            return final_result
            
        except Exception as e:
            logger.error(f"[{self.correlation_id}] ❌ Pipeline failed: {e}")
            if self.verbose:
                logger.exception(f"[{self.correlation_id}] Full error details:")
            raise
    
    async def _load_csv_data(self, csv_file: str) -> pd.DataFrame:
        """Load and validate CSV data."""
        logger.debug(f"[{self.correlation_id}] Loading CSV file: {csv_file}")
        
        # Validate file exists and format
        validate_csv_file(csv_file)
        
        # Load data
        data = pd.read_csv(csv_file)
        logger.debug(f"[{self.correlation_id}] Loaded {len(data)} rows from CSV")
        
        return data
    
    async def _run_keyword_analysis(self, data: pd.DataFrame, goal: str) -> Dict[str, Any]:
        """Run keyword analysis on the data."""
        logger.debug(f"[{self.correlation_id}] Starting keyword analysis")
        
        # Extract video titles for keyword analysis
        titles = []
        if 'title' in data.columns:
            titles = data['title'].dropna().tolist()
        elif 'video_title' in data.columns:
            titles = data['video_title'].dropna().tolist()
        elif 'Title' in data.columns:
            titles = data['Title'].dropna().tolist()
        
        if not titles:
            logger.warning(f"[{self.correlation_id}] No titles found in CSV data")
            return {"keywords": [], "trends": {}, "suggestions": []}
        
        # Extract base keywords from titles and goal
        base_keywords = self._extract_keywords_from_titles(titles)
        goal_keywords = self._extract_keywords_from_goal(goal)
        all_keywords = list(set(base_keywords + goal_keywords))
        
        # Run keyword analysis
        try:
            # Get autocomplete suggestions
            suggestions = []
            for keyword in all_keywords[:5]:  # Limit to prevent rate limiting
                try:
                    keyword_suggestions = self.keyword_analyzer.get_autocomplete_suggestions(keyword)
                    suggestions.extend(keyword_suggestions[:3])  # Top 3 per keyword
                except Exception as e:
                    logger.warning(f"[{self.correlation_id}] Failed to get suggestions for '{keyword}': {e}")
            
            # Get trends data (if available)
            trends = {}
            try:
                trends_data = self.keyword_analyzer.get_trends_data(all_keywords[:3])
                trends = trends_data if trends_data else {}
            except Exception as e:
                logger.warning(f"[{self.correlation_id}] Trends data unavailable: {e}")
            
            return {
                "keywords": all_keywords,
                "suggestions": list(set(suggestions)),
                "trends": trends,
                "source_titles_count": len(titles)
            }
            
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Keyword analysis failed: {e}")
            return {
                "keywords": all_keywords,
                "suggestions": [],
                "trends": {},
                "error": str(e)
            }
    
    async def _run_gap_detection(self, data: pd.DataFrame, goal: str, audience: Optional[str]) -> Dict[str, Any]:
        """Run content gap detection analysis."""
        logger.debug(f"[{self.correlation_id}] Starting gap detection")
        
        try:
            # Prepare data for gap analysis
            analysis_data = self._prepare_gap_analysis_data(data)
            
            # Run gap detection
            gaps = self.gap_detector.find_content_gaps(
                your_data=analysis_data,
                competitor_data=[],  # Will be enhanced in future
                goal=goal
            )
            
            # Generate opportunity insights
            opportunities = self._generate_opportunity_insights(gaps, audience, goal)
            
            return {
                "gaps": gaps,
                "opportunities": opportunities,
                "analysis_summary": {
                    "total_content_pieces": len(analysis_data),
                    "identified_gaps": len(gaps),
                    "priority_opportunities": len([o for o in opportunities if o.get("priority") == "high"])
                }
            }
            
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Gap detection failed: {e}")
            return {
                "gaps": [],
                "opportunities": [],
                "error": str(e)
            }
    
    async def _build_prompt_context(
        self,
        keywords_result: Dict[str, Any],
        gaps_result: Dict[str, Any],
        goal: str,
        audience: Optional[str],
        tone: str
    ) -> Dict[str, Any]:
        """Build comprehensive context for AI prompt generation."""
        logger.debug(f"[{self.correlation_id}] Building prompt context")
        
        # Extract key insights
        top_keywords = keywords_result.get("keywords", [])[:10]
        keyword_suggestions = keywords_result.get("suggestions", [])[:5]
        content_gaps = gaps_result.get("gaps", [])[:5]
        opportunities = gaps_result.get("opportunities", [])[:3]
        
        # Build structured context
        context = {
            "goal": goal,
            "audience": audience or "general YouTube audience",
            "tone": tone,
            "keywords": {
                "primary": top_keywords,
                "suggestions": keyword_suggestions,
                "trends": keywords_result.get("trends", {})
            },
            "content_gaps": content_gaps,
            "opportunities": opportunities,
            "constraints": {
                "platform": "YouTube",
                "language": "English",  # Could be enhanced with language detection
                "format": "video content"
            }
        }
        
        return context
    
    async def _generate_ai_content(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-optimized content using Gemini."""
        logger.debug(f"[{self.correlation_id}] Generating AI content")
        
        try:
            # Build the main prompt
            prompt = self._build_content_generation_prompt(prompt_context)
            
            # Enhance the prompt
            enhanced_prompt = self.prompt_enhancer.enhance_prompt(
                base_prompt=prompt,
                tone=prompt_context.get("tone", "engaging"),
                audience=prompt_context.get("audience"),
                goal=prompt_context.get("goal"),
                keywords=prompt_context.get("keywords", {}).get("primary", [])
            )
            
            # Call Gemini AI if available
            if self.gemini_model:
                try:
                    response = self.gemini_model.generate_content(enhanced_prompt)
                    ai_response = response.text
                except Exception as e:
                    logger.warning(f"[{self.correlation_id}] Gemini API failed: {e}")
                    ai_response = None
            else:
                ai_response = None
            
            # Parse and structure the response
            if ai_response:
                structured_content = self._parse_ai_response(ai_response)
            else:
                # Use fallback generation
                structured_content = self._generate_fallback_content(prompt_context)
            
            return structured_content
            
        except Exception as e:
            logger.error(f"[{self.correlation_id}] AI content generation failed: {e}")
            # Fallback to template-based generation
            return self._generate_fallback_content(prompt_context)
    
    async def _apply_psychological_optimization(
        self,
        ai_content: Dict[str, Any],
        tone: str,
        audience: Optional[str],
        goal: str
    ) -> Dict[str, Any]:
        """Apply psychological triggers and emotional optimization."""
        logger.debug(f"[{self.correlation_id}] Applying psychological optimization")
        
        try:
            # Apply emotion optimization to titles
            optimized_titles = []
            for title in ai_content.get("titles", []):
                optimized_title = self.emotion_optimizer.optimize_title(
                    title=title,
                    goal=goal,
                    audience=audience,
                    tone=tone
                )
                optimized_titles.append(optimized_title)
            
            # Optimize descriptions
            optimized_descriptions = []
            for desc in ai_content.get("descriptions", []):
                optimized_desc = self.emotion_optimizer.optimize_description(
                    description=desc,
                    goal=goal,
                    audience=audience,
                    tone=tone
                )
                optimized_descriptions.append(optimized_desc)
            
            # Enhance tags with psychological keywords
            enhanced_tags = self._enhance_tags_with_psychology(
                ai_content.get("tags", []), tone, audience
            )
            
            return {
                "titles": optimized_titles,
                "descriptions": optimized_descriptions,
                "tags": enhanced_tags,
                "thumbnail_text": ai_content.get("thumbnail_text", []),
                "psychological_triggers": self._get_applied_triggers(tone),
                "optimization_notes": f"Applied {tone} tone optimization for {audience or 'general'} audience"
            }
            
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Psychological optimization failed: {e}")
            return ai_content  # Return original content if optimization fails
    
    async def _compile_final_results(
        self,
        keywords_result: Dict[str, Any],
        gaps_result: Dict[str, Any],
        optimized_content: Dict[str, Any],
        goal: str,
        audience: Optional[str],
        tone: str
    ) -> Dict[str, Any]:
        """Compile all results into final structured output."""
        logger.debug(f"[{self.correlation_id}] Compiling final results")
        
        # Generate insights summary
        insights = self._generate_insights_summary(
            keywords_result, gaps_result, optimized_content, goal
        )
        
        # Calculate performance metrics
        performance_metrics = {
            "pipeline_execution_time": sum(self.step_times.values()),
            "step_times": self.step_times,
            "keywords_found": len(keywords_result.get("keywords", [])),
            "gaps_identified": len(gaps_result.get("gaps", [])),
            "content_pieces_generated": len(optimized_content.get("titles", []))
        }
        
        return {
            "analysis_result": {
                "keywords": keywords_result,
                "gaps": gaps_result,
                "optimized_content": optimized_content,
                "insights": insights
            },
            "metadata": {
                "correlation_id": self.correlation_id,
                "goal": goal,
                "audience": audience,
                "tone": tone,
                "timestamp": datetime.now().isoformat(),
                "performance": performance_metrics
            },
            "success": True
        }
    
    def _extract_keywords_from_titles(self, titles: List[str]) -> List[str]:
        """Extract keywords from video titles."""
        import re
        
        keywords = []
        for title in titles:
            # Simple keyword extraction - could be enhanced
            words = re.findall(r'\b\w{3,}\b', title.lower())
            keywords.extend(words)
        
        # Remove common stop words and return unique keywords
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'don', 'let', 'put', 'say', 'she', 'too', 'use'}
        filtered_keywords = [k for k in set(keywords) if k not in stop_words and len(k) > 3]
        
        return filtered_keywords[:20]  # Return top 20
    
    def _extract_keywords_from_goal(self, goal: str) -> List[str]:
        """Extract keywords from the analysis goal."""
        import re
        
        words = re.findall(r'\b\w{3,}\b', goal.lower())
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who'}
        
        return [w for w in words if w not in stop_words and len(w) > 3]
    
    def _prepare_gap_analysis_data(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Prepare data for gap analysis."""
        analysis_data = []
        
        for _, row in data.iterrows():
            item = {}
            
            # Map common column names
            if 'title' in row:
                item['title'] = row['title']
            elif 'video_title' in row:
                item['title'] = row['video_title']
            elif 'Title' in row:
                item['title'] = row['Title']
            
            if 'views' in row:
                item['views'] = row['views']
            elif 'view_count' in row:
                item['views'] = row['view_count']
            
            if 'published_at' in row:
                item['published_at'] = row['published_at']
            elif 'publish_date' in row:
                item['published_at'] = row['publish_date']
            
            if item:  # Only add if we found some data
                analysis_data.append(item)
        
        return analysis_data
    
    def _generate_opportunity_insights(self, gaps: List[Dict], audience: Optional[str], goal: str) -> List[Dict]:
        """Generate actionable opportunity insights from gaps."""
        opportunities = []
        
        for gap in gaps[:5]:  # Top 5 gaps
            opportunity = {
                "gap": gap,
                "recommendation": f"Create content about {gap.get('topic', 'this topic')} to fill market gap",
                "target_audience": audience or "general audience",
                "priority": "high" if gap.get('score', 0) > 0.7 else "medium",
                "estimated_impact": "High engagement potential based on gap analysis"
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _build_content_generation_prompt(self, context: Dict[str, Any]) -> str:
        """Build the main prompt for AI content generation."""
        prompt = f"""
        Generate optimized YouTube content strategy based on the following analysis:
        
        Goal: {context['goal']}
        Target Audience: {context['audience']}
        Tone: {context['tone']}
        
        Keywords to focus on: {', '.join(context['keywords']['primary'][:5])}
        Suggested keywords: {', '.join(context['keywords']['suggestions'][:3])}
        
        Content gaps identified: {len(context['content_gaps'])} gaps found
        Key opportunities: {len(context['opportunities'])} opportunities
        
        Please generate:
        1. 5 optimized video titles that address the gaps and use the keywords
        2. 3 compelling video descriptions (150-200 words each)
        3. 15-20 relevant tags for YouTube SEO
        4. 3 thumbnail text suggestions (short, punchy phrases)
        
        Focus on {context['tone']} tone and optimize for {context['audience']}.
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        # This is a simplified parser - could be enhanced with better parsing
        lines = ai_response.split('\n')
        
        result = {
            "titles": [],
            "descriptions": [],
            "tags": [],
            "thumbnail_text": []
        }
        
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "title" in line.lower() and (":" in line or "#" in line):
                current_section = "titles"
                continue
            elif "description" in line.lower() and (":" in line or "#" in line):
                current_section = "descriptions"
                continue
            elif "tag" in line.lower() and (":" in line or "#" in line):
                current_section = "tags"
                continue
            elif "thumbnail" in line.lower() and (":" in line or "#" in line):
                current_section = "thumbnail_text"
                continue
            
            if current_section and line:
                # Clean up the line
                cleaned_line = line.lstrip('123456789.-• ').strip()
                if cleaned_line:
                    result[current_section].append(cleaned_line)
        
        # Fallback if parsing fails
        if not any(result.values()):
            result["titles"] = ["Optimized YouTube Title Based on Analysis"]
            result["descriptions"] = ["Optimized description based on keyword and gap analysis."]
            result["tags"] = ["youtube", "seo", "content", "strategy"]
            result["thumbnail_text"] = ["CLICK NOW"]
        
        return result
    
    def _generate_fallback_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback content when AI fails."""
        keywords = context['keywords']['primary'][:3]
        goal = context['goal']
        
        return {
            "titles": [
                f"Ultimate Guide to {keywords[0] if keywords else 'Content Creation'}",
                f"How to Master {keywords[1] if len(keywords) > 1 else 'YouTube Strategy'}",
                f"Secret Tips for {keywords[2] if len(keywords) > 2 else 'Success'}",
                f"Complete Tutorial: {goal[:30]}...",
                f"Pro Strategies for {context['audience']}"
            ],
            "descriptions": [
                f"Learn everything about {goal}. This comprehensive guide covers all aspects.",
                f"Discover proven strategies for {context['audience']}. Step-by-step tutorial included.",
                f"Master the art of {keywords[0] if keywords else 'content creation'} with expert tips."
            ],
            "tags": keywords + ["tutorial", "guide", "tips", "strategy", "youtube"],
            "thumbnail_text": ["ULTIMATE GUIDE", "SECRET TIPS", "PRO STRATEGY"]
        }
    
    def _enhance_tags_with_psychology(self, tags: List[str], tone: str, audience: Optional[str]) -> List[str]:
        """Enhance tags with psychological keywords."""
        psychological_tags = {
            "curiosity": ["secret", "hidden", "unknown", "mystery"],
            "authority": ["expert", "professional", "proven", "advanced"],
            "fear": ["avoid", "mistake", "warning", "danger"],
            "persuasive": ["best", "ultimate", "complete", "perfect"],
            "engaging": ["amazing", "incredible", "awesome", "fantastic"]
        }
        
        tone_tags = psychological_tags.get(tone, psychological_tags["engaging"])
        enhanced_tags = tags + tone_tags[:2]  # Add 2 psychological tags
        
        if audience:
            # Add audience-specific tags
            if "genz" in audience.lower():
                enhanced_tags.extend(["trending", "viral", "latest"])
            elif "tech" in audience.lower():
                enhanced_tags.extend(["technology", "innovation", "digital"])
        
        return list(set(enhanced_tags))  # Remove duplicates
    
    def _get_applied_triggers(self, tone: str) -> List[str]:
        """Get list of psychological triggers applied."""
        triggers = {
            "curiosity": ["Mystery hooks", "Question-based titles", "Suspense elements"],
            "authority": ["Expert positioning", "Credential mentions", "Professional language"],
            "fear": ["Loss aversion", "Mistake avoidance", "Risk warnings"],
            "persuasive": ["Social proof", "Urgency", "Exclusivity"],
            "engaging": ["Emotional appeal", "Relatable content", "Entertainment value"]
        }
        
        return triggers.get(tone, triggers["engaging"])
    
    def _generate_insights_summary(
        self,
        keywords_result: Dict[str, Any],
        gaps_result: Dict[str, Any],
        optimized_content: Dict[str, Any],
        goal: str
    ) -> str:
        """Generate a human-readable insights summary."""
        
        keywords_count = len(keywords_result.get("keywords", []))
        gaps_count = len(gaps_result.get("gaps", []))
        titles_count = len(optimized_content.get("titles", []))
        
        insights = f"""
🎯 Analysis Complete for: {goal}

📊 Key Findings:
• Analyzed {keywords_count} relevant keywords from your content
• Identified {gaps_count} content gaps in your niche
• Generated {titles_count} optimized video concepts

🚀 Top Recommendations:
• Focus on the identified content gaps for maximum impact
• Use the provided psychological triggers to increase engagement
• Implement the suggested tags for better YouTube SEO

💡 Next Steps:
• Create content around the highest-priority gaps
• Test different title variations from the suggestions
• Monitor performance and iterate based on results
        """.strip()
        
        return insights

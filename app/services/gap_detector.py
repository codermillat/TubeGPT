"""
Gap Detector Module for YouTube Content Analysis.

This module analyzes competitor content to identify gaps and opportunities
in your YouTube content strategy by comparing video topics, frequency,
and engagement metrics.

Features:
1. Competitor content comparison and gap analysis
2. Topic frequency analysis and opportunity detection
3. Engagement comparison across similar content
4. Human-readable insights and recommendations
5. Integration with Gemini for natural language queries
"""

import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
from collections import Counter, defaultdict
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GapDetector:
    """
    Analyzes content gaps between your channel and competitors.
    
    Identifies missing topics, frequency differences, and engagement
    opportunities by comparing YouTube analytics data.
    """
    
    def __init__(self):
        """Initialize the Gap Detector."""
        self.topic_keywords = {
            # Common YouTube topic categories for better matching
            'tutorial': ['tutorial', 'how to', 'guide', 'step by step', 'learn'],
            'review': ['review', 'unboxing', 'test', 'comparison', 'vs'],
            'vlog': ['vlog', 'daily', 'day in life', 'routine', 'behind scenes'],
            'cooking': ['recipe', 'cooking', 'food', 'kitchen', 'meal'],
            'tech': ['tech', 'technology', 'gadget', 'phone', 'computer'],
            'travel': ['travel', 'trip', 'vacation', 'destination', 'tour'],
            'education': ['education', 'study', 'exam', 'university', 'school'],
            'entertainment': ['funny', 'comedy', 'entertainment', 'reaction', 'challenge']
        }
        
        logger.info("Gap Detector initialized")
    
    def _load_and_validate_csv(self, csv_path: str, source_name: str = "CSV") -> pd.DataFrame:
        """
        Load and validate CSV file for gap analysis.
        
        Args:
            csv_path (str): Path to CSV file
            source_name (str): Name for logging (e.g., "Your channel", "Competitor A")
            
        Returns:
            pd.DataFrame: Loaded and validated dataframe
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required columns are missing
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"{source_name} CSV file not found: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {source_name} CSV with {len(df)} rows")
            
            # Validate required columns
            required_columns = ['videoTitle']
            optional_columns = ['videoId', 'views', 'CTR', 'averageViewDuration']
            
            missing_required = [col for col in required_columns if col not in df.columns]
            if missing_required:
                raise ValueError(f"Missing required columns in {source_name}: {missing_required}")
            
            # Add missing optional columns with default values
            for col in optional_columns:
                if col not in df.columns:
                    if col == 'videoId':
                        df[col] = df.index.astype(str)  # Use index as fallback ID
                    else:
                        df[col] = 0  # Default numeric value
                    logger.warning(f"Missing column '{col}' in {source_name}, using default values")
            
            # Clean and normalize data
            df['videoTitle'] = df['videoTitle'].astype(str).str.strip()
            df = df[df['videoTitle'] != '']  # Remove empty titles
            
            # Ensure numeric columns are properly typed
            numeric_columns = ['views', 'CTR', 'averageViewDuration']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading {source_name} CSV: {e}")
            raise ValueError(f"Failed to load {source_name} CSV: {e}")
    
    def _extract_topics(self, titles: List[str]) -> Dict[str, List[str]]:
        """
        Extract topics from video titles using keyword matching.
        
        Args:
            titles (List[str]): List of video titles
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping topics to matching titles
        """
        topic_matches = defaultdict(list)
        
        for title in titles:
            title_lower = title.lower()
            
            # Check each topic category
            for topic, keywords in self.topic_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    topic_matches[topic].append(title)
            
            # Also extract specific keywords/phrases
            # Look for common patterns like "X tips", "X guide", "X review"
            patterns = [
                r'(\w+)\s+tips?',
                r'(\w+)\s+guide',
                r'(\w+)\s+review',
                r'(\w+)\s+tutorial',
                r'how\s+to\s+(\w+)',
                r'(\w+)\s+secrets?',
                r'(\w+)\s+hacks?'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, title_lower)
                for match in matches:
                    if len(match) > 2:  # Avoid very short words
                        topic_key = f"{match}_specific"
                        topic_matches[topic_key].append(title)
        
        return dict(topic_matches)
    
    def _calculate_engagement_score(self, row: pd.Series) -> float:
        """
        Calculate a normalized engagement score for a video.
        
        Args:
            row (pd.Series): Video data row
            
        Returns:
            float: Engagement score (0-100)
        """
        try:
            views = float(row.get('views', 0))
            ctr = float(row.get('CTR', 0))
            duration = float(row.get('averageViewDuration', 0))
            
            # Normalize and weight different metrics
            # This is a simplified scoring system - can be enhanced
            view_score = min(views / 10000, 10)  # Cap at 100K views = 10 points
            ctr_score = ctr * 100 * 2  # CTR as percentage * 2
            duration_score = min(duration / 60, 5)  # Cap at 5 minutes = 5 points
            
            total_score = view_score + ctr_score + duration_score
            return min(total_score, 100)  # Cap at 100
            
        except (ValueError, TypeError):
            return 0.0
    
    def compare_with_competitors(self, your_csv_path: str, 
                               competitor_csv_paths: List[str]) -> Dict[str, Any]:
        """
        Compare your content with competitors to identify gaps and opportunities.
        
        Args:
            your_csv_path (str): Path to your YouTube analytics CSV
            competitor_csv_paths (List[str]): List of paths to competitor CSV files
            
        Returns:
            Dict[str, Any]: Comprehensive gap analysis results
            
        Raises:
            FileNotFoundError: If any CSV file doesn't exist
            ValueError: If CSV files are malformed
        """
        try:
            logger.info(f"Starting gap analysis with {len(competitor_csv_paths)} competitors")
            
            # Load your data
            your_df = self._load_and_validate_csv(your_csv_path, "Your channel")
            your_topics = self._extract_topics(your_df['videoTitle'].tolist())
            
            # Load competitor data
            competitor_data = {}
            all_competitor_topics = defaultdict(list)
            
            for i, comp_path in enumerate(competitor_csv_paths):
                comp_name = f"Competitor_{i+1}"
                try:
                    comp_df = self._load_and_validate_csv(comp_path, comp_name)
                    comp_topics = self._extract_topics(comp_df['videoTitle'].tolist())
                    
                    competitor_data[comp_name] = {
                        'df': comp_df,
                        'topics': comp_topics,
                        'total_videos': len(comp_df)
                    }
                    
                    # Aggregate all competitor topics
                    for topic, titles in comp_topics.items():
                        all_competitor_topics[topic].extend([(comp_name, title) for title in titles])
                        
                except Exception as e:
                    logger.error(f"Failed to load {comp_name}: {e}")
                    continue
            
            if not competitor_data:
                raise ValueError("No valid competitor data loaded")
            
            # Analyze gaps and opportunities
            gap_analysis = self._analyze_content_gaps(
                your_topics, 
                all_competitor_topics, 
                your_df, 
                competitor_data
            )
            
            logger.info("Gap analysis completed successfully")
            return gap_analysis
            
        except Exception as e:
            logger.error(f"Error in competitor comparison: {e}")
            raise
    
    def _analyze_content_gaps(self, your_topics: Dict[str, List[str]], 
                            competitor_topics: Dict[str, List[Tuple[str, str]]], 
                            your_df: pd.DataFrame,
                            competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze content gaps between your channel and competitors.
        
        Args:
            your_topics (Dict): Your channel's topics
            competitor_topics (Dict): All competitor topics
            your_df (pd.DataFrame): Your channel data
            competitor_data (Dict): Competitor data
            
        Returns:
            Dict[str, Any]: Gap analysis results
        """
        analysis = {
            'missing_topics': [],
            'underperforming_topics': [],
            'overperforming_topics': [],
            'frequency_gaps': [],
            'engagement_opportunities': [],
            'summary_stats': {},
            'recommendations': []
        }
        
        # Find missing topics (topics competitors cover but you don't)
        for topic, comp_entries in competitor_topics.items():
            if topic not in your_topics:
                competitor_count = len(comp_entries)
                competitors_covering = len(set(entry[0] for entry in comp_entries))
                
                analysis['missing_topics'].append({
                    'topic': topic,
                    'competitor_videos': competitor_count,
                    'competitors_covering': competitors_covering,
                    'your_videos': 0,
                    'opportunity_score': competitor_count * competitors_covering,
                    'sample_titles': [entry[1] for entry in comp_entries[:3]]
                })
        
        # Find frequency gaps (topics you cover less than competitors)
        for topic in your_topics:
            your_count = len(your_topics[topic])
            comp_count = len(competitor_topics.get(topic, []))
            
            if comp_count > your_count * 2:  # Competitors have 2x more content
                analysis['frequency_gaps'].append({
                    'topic': topic,
                    'your_videos': your_count,
                    'competitor_videos': comp_count,
                    'gap_ratio': comp_count / max(your_count, 1),
                    'sample_competitor_titles': [entry[1] for entry in competitor_topics[topic][:3]]
                })
        
        # Find topics you dominate
        for topic in your_topics:
            your_count = len(your_topics[topic])
            comp_count = len(competitor_topics.get(topic, []))
            
            if your_count > comp_count * 1.5:  # You have 1.5x more content
                analysis['overperforming_topics'].append({
                    'topic': topic,
                    'your_videos': your_count,
                    'competitor_videos': comp_count,
                    'advantage_ratio': your_count / max(comp_count, 1)
                })
        
        # Calculate engagement opportunities
        self._analyze_engagement_opportunities(analysis, your_df, competitor_data)
        
        # Generate summary statistics
        analysis['summary_stats'] = {
            'your_total_videos': len(your_df),
            'your_unique_topics': len(your_topics),
            'competitor_total_videos': sum(data['total_videos'] for data in competitor_data.values()),
            'competitor_unique_topics': len(competitor_topics),
            'missing_topic_count': len(analysis['missing_topics']),
            'frequency_gap_count': len(analysis['frequency_gaps'])
        }
        
        # Sort results by opportunity score
        analysis['missing_topics'].sort(key=lambda x: x['opportunity_score'], reverse=True)
        analysis['frequency_gaps'].sort(key=lambda x: x['gap_ratio'], reverse=True)
        
        return analysis
    
    def _analyze_engagement_opportunities(self, analysis: Dict[str, Any], 
                                        your_df: pd.DataFrame,
                                        competitor_data: Dict[str, Any]) -> None:
        """
        Analyze engagement opportunities by comparing performance metrics.
        
        Args:
            analysis (Dict): Analysis results to update
            your_df (pd.DataFrame): Your channel data
            competitor_data (Dict): Competitor data
        """
        try:
            # Calculate your average engagement
            your_df['engagement_score'] = your_df.apply(self._calculate_engagement_score, axis=1)
            your_avg_engagement = your_df['engagement_score'].mean()
            
            # Compare with competitors
            for comp_name, comp_data in competitor_data.items():
                comp_df = comp_data['df']
                comp_df['engagement_score'] = comp_df.apply(self._calculate_engagement_score, axis=1)
                comp_avg_engagement = comp_df['engagement_score'].mean()
                
                if comp_avg_engagement > your_avg_engagement * 1.2:  # 20% better
                    # Find their best performing topics
                    comp_topics = comp_data['topics']
                    topic_performance = {}
                    
                    for topic, titles in comp_topics.items():
                        topic_videos = comp_df[comp_df['videoTitle'].isin(titles)]
                        if len(topic_videos) > 0:
                            topic_performance[topic] = topic_videos['engagement_score'].mean()
                    
                    # Get top performing topics
                    top_topics = sorted(topic_performance.items(), 
                                      key=lambda x: x[1], reverse=True)[:3]
                    
                    analysis['engagement_opportunities'].append({
                        'competitor': comp_name,
                        'their_avg_engagement': comp_avg_engagement,
                        'your_avg_engagement': your_avg_engagement,
                        'performance_gap': comp_avg_engagement - your_avg_engagement,
                        'top_performing_topics': top_topics
                    })
                    
        except Exception as e:
            logger.warning(f"Could not analyze engagement opportunities: {e}")
    
    def summarize_gap_results(self, gap_data: Dict[str, Any]) -> str:
        """
        Generate human-readable insights from gap analysis results.
        
        Args:
            gap_data (Dict[str, Any]): Results from compare_with_competitors()
            
        Returns:
            str: Human-readable summary with actionable insights
        """
        try:
            summary_parts = []
            
            # Header
            stats = gap_data['summary_stats']
            summary_parts.append(f"📊 CONTENT GAP ANALYSIS RESULTS")
            summary_parts.append(f"{'='*50}")
            summary_parts.append(f"Your Channel: {stats['your_total_videos']} videos, {stats['your_unique_topics']} topics")
            summary_parts.append(f"Competitors: {stats['competitor_total_videos']} total videos, {stats['competitor_unique_topics']} unique topics")
            
            # Missing topics (biggest opportunities)
            if gap_data['missing_topics']:
                summary_parts.append(f"\n🎯 MISSING OPPORTUNITIES ({len(gap_data['missing_topics'])} topics):")
                
                for i, topic in enumerate(gap_data['missing_topics'][:5], 1):
                    topic_name = topic['topic'].replace('_specific', '').replace('_', ' ').title()
                    summary_parts.append(
                        f"{i}. {topic_name}: Competitors have {topic['competitor_videos']} videos "
                        f"({topic['competitors_covering']} competitors) - you have {topic['your_videos']}"
                    )
                    if topic['sample_titles']:
                        summary_parts.append(f"   Example: \"{topic['sample_titles'][0]}\"")
            
            # Frequency gaps
            if gap_data['frequency_gaps']:
                summary_parts.append(f"\n📈 FREQUENCY GAPS ({len(gap_data['frequency_gaps'])} topics):")
                
                for i, gap in enumerate(gap_data['frequency_gaps'][:3], 1):
                    topic_name = gap['topic'].replace('_specific', '').replace('_', ' ').title()
                    summary_parts.append(
                        f"{i}. {topic_name}: You have {gap['your_videos']} videos, "
                        f"competitors have {gap['competitor_videos']} ({gap['gap_ratio']:.1f}x more)"
                    )
            
            # Your strengths
            if gap_data['overperforming_topics']:
                summary_parts.append(f"\n💪 YOUR STRENGTHS ({len(gap_data['overperforming_topics'])} topics):")
                
                for i, strength in enumerate(gap_data['overperforming_topics'][:3], 1):
                    topic_name = strength['topic'].replace('_specific', '').replace('_', ' ').title()
                    summary_parts.append(
                        f"{i}. {topic_name}: You lead with {strength['your_videos']} videos "
                        f"vs competitors' {strength['competitor_videos']} ({strength['advantage_ratio']:.1f}x advantage)"
                    )
            
            # Engagement opportunities
            if gap_data['engagement_opportunities']:
                summary_parts.append(f"\n🚀 ENGAGEMENT OPPORTUNITIES:")
                
                for opp in gap_data['engagement_opportunities'][:2]:
                    summary_parts.append(
                        f"• {opp['competitor']} has {opp['performance_gap']:.1f} points higher engagement"
                    )
                    if opp['top_performing_topics']:
                        top_topic = opp['top_performing_topics'][0]
                        topic_name = top_topic[0].replace('_specific', '').replace('_', ' ').title()
                        summary_parts.append(f"  Their best topic: {topic_name} ({top_topic[1]:.1f} engagement)")
            
            # Recommendations
            summary_parts.append(f"\n💡 TOP RECOMMENDATIONS:")
            
            recommendations = []
            
            # Top missing topic recommendation
            if gap_data['missing_topics']:
                top_missing = gap_data['missing_topics'][0]
                topic_name = top_missing['topic'].replace('_specific', '').replace('_', ' ').title()
                recommendations.append(
                    f"1. Create content about {topic_name} - high opportunity with "
                    f"{top_missing['competitor_videos']} competitor videos but none from you"
                )
            
            # Top frequency gap recommendation
            if gap_data['frequency_gaps']:
                top_gap = gap_data['frequency_gaps'][0]
                topic_name = top_gap['topic'].replace('_specific', '').replace('_', ' ').title()
                recommendations.append(
                    f"2. Increase {topic_name} content frequency - competitors produce "
                    f"{top_gap['gap_ratio']:.1f}x more content in this area"
                )
            
            # Engagement recommendation
            if gap_data['engagement_opportunities']:
                top_eng = gap_data['engagement_opportunities'][0]
                if top_eng['top_performing_topics']:
                    topic_name = top_eng['top_performing_topics'][0][0].replace('_specific', '').replace('_', ' ').title()
                    recommendations.append(
                        f"3. Focus on {topic_name} content - {top_eng['competitor']} gets "
                        f"{top_eng['performance_gap']:.1f} points higher engagement in this area"
                    )
            
            # Leverage strengths
            if gap_data['overperforming_topics']:
                top_strength = gap_data['overperforming_topics'][0]
                topic_name = top_strength['topic'].replace('_specific', '').replace('_', ' ').title()
                recommendations.append(
                    f"4. Double down on {topic_name} - you're already leading with "
                    f"{top_strength['advantage_ratio']:.1f}x more content than competitors"
                )
            
            summary_parts.extend(recommendations[:4])  # Limit to top 4 recommendations
            
            return '\n'.join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating gap summary: {e}")
            return f"Error generating summary: {str(e)}"

def detect_content_gaps_from_query(user_question: str, your_csv_path: str, 
                                 competitor_csv_paths: List[str]) -> str:
    """
    Detect content gaps based on user query and return insights.
    
    This function is designed to be called from gemini_chat.py when users
    ask questions like "what am I missing?" or "what should I create next?"
    
    Args:
        user_question (str): User's question about content gaps
        your_csv_path (str): Path to your YouTube analytics CSV
        competitor_csv_paths (List[str]): List of competitor CSV paths
        
    Returns:
        str: Human-readable gap analysis and recommendations
    """
    try:
        logger.info(f"Detecting content gaps for query: '{user_question}'")
        
        if not competitor_csv_paths:
            return "No competitor data available for gap analysis. Please provide competitor CSV files to identify content opportunities."
        
        # Initialize gap detector
        detector = GapDetector()
        
        # Perform gap analysis
        gap_results = detector.compare_with_competitors(your_csv_path, competitor_csv_paths)
        
        # Generate human-readable summary
        summary = detector.summarize_gap_results(gap_results)
        
        # Add context based on user question
        question_lower = user_question.lower()
        
        if 'missing' in question_lower or 'gap' in question_lower:
            context = "\nBased on your question about missing content, here's what your competitors are covering that you're not:\n\n"
        elif 'opportunity' in question_lower or 'next' in question_lower:
            context = "\nHere are the biggest content opportunities I found by analyzing your competitors:\n\n"
        elif 'improve' in question_lower or 'better' in question_lower:
            context = "\nHere's how you can improve your content strategy based on competitor analysis:\n\n"
        else:
            context = "\nHere's your comprehensive content gap analysis:\n\n"
        
        return context + summary
        
    except Exception as e:
        logger.error(f"Error in gap detection: {e}")
        return f"I encountered an error while analyzing content gaps: {str(e)}. Please check that your CSV files are properly formatted and accessible."

def main():
    """
    Example usage of the Gap Detector.
    """
    try:
        # Example usage
        your_csv = "yt_analytics.csv"
        competitor_csvs = [
            "competitor_a_analytics.csv",
            "competitor_b_analytics.csv"
        ]
        
        print("YouTube Content Gap Analysis")
        print("=" * 40)
        
        # Check if files exist
        if not os.path.exists(your_csv):
            print(f"Your CSV file '{your_csv}' not found.")
            print("Please ensure you have your YouTube analytics data.")
            return
        
        available_competitors = [csv for csv in competitor_csvs if os.path.exists(csv)]
        
        if not available_competitors:
            print("No competitor CSV files found.")
            print("Please add competitor analytics data to perform gap analysis.")
            return
        
        print(f"Analyzing against {len(available_competitors)} competitors...")
        
        # Initialize detector
        detector = GapDetector()
        
        # Perform analysis
        results = detector.compare_with_competitors(your_csv, available_competitors)
        
        # Generate summary
        summary = detector.summarize_gap_results(results)
        
        print("\n" + summary)
        
        # Example of query-based detection
        print(f"\n{'='*60}")
        print("QUERY-BASED ANALYSIS EXAMPLE:")
        print(f"{'='*60}")
        
        query_result = detect_content_gaps_from_query(
            "What content am I missing compared to competitors?",
            your_csv,
            available_competitors
        )
        
        print(query_result)
        
    except Exception as e:
        print(f"Error during gap analysis: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()
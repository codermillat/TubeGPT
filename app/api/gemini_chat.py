# FIXED: Updated to use refactored modules - gemini_client.py, prompt_builder.py, data_analyzer.py
"""
YouTube Analytics with Gemini Integration.
This module has been refactored for better maintainability and error handling.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# FIXED: Import from new refactored modules
from gemini_client import GeminiClient
from prompt_builder import PromptBuilder, detect_language, load_system_prompt
from data_analyzer import DataAnalyzer

# FIXED: Set up logging first before any usage
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# FIXED: Safe imports with proper error handling
try:
    from multi_csv import compare_csvs, compare_multiple_metrics, generate_comparison_summary, get_top_changes
    MULTI_CSV_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Multi-CSV comparison not available: {e}")
    MULTI_CSV_AVAILABLE = False

try:
    from gap_detector import detect_content_gaps_from_query
    GAP_DETECTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Gap detection not available: {e}")
    GAP_DETECTION_AVAILABLE = False

class GeminiYouTubeAnalyzer:
    """
    A class to analyze YouTube analytics CSV data using Google's Gemini Pro model.
    FIXED: Refactored to use separate modules for better maintainability.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini YouTube Analyzer.
        
        Args:
            api_key (str, optional): Gemini API key. If not provided, will look for GEMINI_API_KEY env var.
        """
        # FIXED: Use new modular components
        self.gemini_client = GeminiClient(api_key=api_key)
        self.prompt_builder = PromptBuilder()
        self.data_analyzer = DataAnalyzer()
        
        logger.info("Gemini YouTube Analyzer initialized with refactored modules")
    
    def load_and_summarize_csv(self, csv_path: str) -> Dict[str, Any]:
        """
        Load CSV file and create a statistical summary.
        FIXED: Delegated to DataAnalyzer for better separation of concerns.
        
        Args:
            csv_path (str): Path to the YouTube analytics CSV file
            
        Returns:
            dict: Summary statistics and key insights from the data
        """
        return self.data_analyzer.load_and_summarize_csv(csv_path)
    
    def analyze_youtube_data(self, user_question: str, csv_path: str, csv2_path: Optional[str] = None) -> str:
        """
        Main method to analyze YouTube data and answer user questions.
        FIXED: Enhanced with better error handling and fallback mechanisms.
        
        Args:
            user_question (str): The user's question about their YouTube analytics
            csv_path (str): Path to the YouTube analytics CSV file
            csv2_path (str, optional): Path to second CSV file for comparison
            
        Returns:
            str: Plain-text response from Gemini with analysis and insights
        """
        try:
            logger.info(f"Starting analysis for question: {user_question}")
            
            # FIXED: Input validation
            if not user_question or not user_question.strip():
                return "Please provide a specific question about your YouTube analytics data."
            
            if not os.path.exists(csv_path):
                return f"CSV file not found: {csv_path}. Please ensure the file exists and try again."
            
            # Check if this is a comparison request
            if csv2_path or self.data_analyzer.detect_comparison_request(user_question):
                return self._perform_csv_comparison(user_question, csv_path, csv2_path)
            
            # Check if this is a gap analysis request
            if self.data_analyzer.detect_gap_analysis_request(user_question):
                return self._perform_gap_analysis(user_question, csv_path)
            
            # Load and summarize the CSV data
            summary = self.data_analyzer.load_and_summarize_csv(csv_path)
            
            # Generate charts if requested
            charts = self.data_analyzer.generate_charts_if_requested(user_question, csv_path)
            
            # Build the analysis prompt
            prompt = self.prompt_builder.build_analysis_prompt(user_question, summary)
            
            # Add chart information to prompt if charts were generated
            if charts:
                chart_info = "\n\nVISUAL CHARTS GENERATED:\n"
                for chart_name, chart_path in charts.items():
                    chart_info += f"- {chart_name}: {chart_path}\n"
                chart_info += "\nPlease reference these charts in your response."
                prompt += chart_info
            
            # FIXED: Use new GeminiClient with retry logic
            fallback_response = self._create_fallback_response(summary, user_question)
            response = self.gemini_client.generate_with_retry(prompt, fallback_response)
            
            logger.info("Analysis completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return f"I encountered an error while analyzing your data: {str(e)}. Please try again or contact support if the issue persists."
    
    def _perform_csv_comparison(self, user_question: str, csv_path: str, csv2_path: Optional[str] = None) -> str:
        """
        Perform comparison between two CSV files.
        FIXED: Enhanced error handling and fallback mechanisms.
        
        Args:
            user_question (str): User's comparison question
            csv_path (str): Path to first CSV file
            csv2_path (str, optional): Path to second CSV file
            
        Returns:
            str: Comparison analysis response
        """
        try:
            if not MULTI_CSV_AVAILABLE:
                return "CSV comparison functionality is not available. Please ensure multi_csv.py is properly installed."
            
            # Try to extract CSV paths from the question if csv2_path not provided
            if not csv2_path:
                csv2_path = self._extract_csv_paths_from_question(user_question, csv_path)
            
            if not csv2_path or not os.path.exists(csv2_path):
                return "I detected you want to compare data, but I need a second CSV file. Please specify the path to the second file."
            
            # Perform comparison
            comparison_summary = generate_comparison_summary(csv_path, csv2_path)
            
            # Build comparison prompt
            prompt = self.prompt_builder.build_comparison_prompt(user_question, {'summary': comparison_summary})
            
            # FIXED: Use Gemini client with fallback
            fallback_response = f"Comparison summary: {comparison_summary}"
            response = self.gemini_client.generate_with_retry(prompt, fallback_response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in CSV comparison: {e}")
            return f"I encountered an error while comparing the CSV files: {str(e)}. Please ensure both files are properly formatted and try again."
    
    def _perform_gap_analysis(self, user_question: str, csv_path: str) -> str:
        """
        Perform gap analysis against competitor data.
        FIXED: Enhanced error handling and fallback mechanisms.
        
        Args:
            user_question (str): User's gap analysis question
            csv_path (str): Path to user's CSV file
            
        Returns:
            str: Gap analysis response
        """
        try:
            if not GAP_DETECTION_AVAILABLE:
                return "Gap detection functionality is not available. Please ensure gap_detector.py is properly installed."
            
            # Try to find competitor CSV files
            competitor_csvs = self._find_competitor_csvs()
            
            if not competitor_csvs:
                return """I can help you identify content gaps, but I need competitor data to compare against. 

To perform gap analysis, please:
1. Add competitor CSV files to your directory (name them like 'competitor_a.csv', 'comp_channel_b.csv', etc.)
2. Ensure they have the same format as your analytics CSV
3. Ask me again about content gaps or opportunities

I'll automatically analyze up to 5 competitor files to show you topics and opportunities you're missing."""
            
            # Perform gap analysis
            gap_analysis = detect_content_gaps_from_query(user_question, csv_path, competitor_csvs)
            return gap_analysis
            
        except Exception as e:
            logger.error(f"Error in gap analysis: {e}")
            return f"I encountered an error while analyzing content gaps: {str(e)}. Please ensure your competitor CSV files are properly formatted."
    
    def _create_fallback_response(self, summary: Dict[str, Any], user_question: str) -> str:
        """
        Create a fallback response when Gemini API is not available.
        FIXED: Provides meaningful fallback analysis.
        
        Args:
            summary (dict): Data summary
            user_question (str): User's question
            
        Returns:
            str: Fallback response
        """
        try:
            fallback_parts = ["Based on your YouTube analytics data:\n"]
            
            # Basic stats
            if 'total_videos' in summary:
                fallback_parts.append(f"• Total videos analyzed: {summary['total_videos']}")
            
            # Views analysis
            if 'views_stats' in summary:
                views = summary['views_stats']
                fallback_parts.append(f"• Total views: {views.get('total', 0):,}")
                fallback_parts.append(f"• Average views per video: {views.get('average', 0):,.0f}")
            
            # CTR analysis
            if 'ctr_stats' in summary:
                ctr = summary['ctr_stats']
                fallback_parts.append(f"• Average CTR: {ctr.get('average', 0):.2f}%")
            
            # Top performers
            if 'top_performers' in summary and summary['top_performers']:
                fallback_parts.append("\nTop performing videos:")
                for i, performer in enumerate(summary['top_performers'][:3], 1):
                    fallback_parts.append(f"{i}. {performer.get('title', 'Unknown')} - {performer.get('views', 0):,} views")
            
            fallback_parts.append("\nFor more detailed analysis, please ensure your Gemini API key is properly configured.")
            
            return "\n".join(fallback_parts)
            
        except Exception as e:
            logger.error(f"Error creating fallback response: {e}")
            return "I apologize, but I'm unable to process your request at the moment. Please try again later or check your configuration."
    
    def _find_competitor_csvs(self) -> List[str]:
        """
        Find competitor CSV files in the current directory.
        FIXED: Enhanced file discovery with better pattern matching.
        
        Returns:
            list: List of competitor CSV file paths
        """
        try:
            competitor_patterns = [
                'competitor*.csv',
                'comp*.csv',
                '*competitor*.csv',
                'rival*.csv',
                'competition*.csv'
            ]
            
            competitor_csvs = []
            current_dir = os.getcwd()
            
            for pattern in competitor_patterns:
                import glob
                matches = glob.glob(os.path.join(current_dir, pattern))
                competitor_csvs.extend(matches)
            
            # Also check data/competitors directory
            competitors_dir = os.path.join(current_dir, 'data', 'competitors')
            if os.path.exists(competitors_dir):
                csv_files = glob.glob(os.path.join(competitors_dir, '*.csv'))
                competitor_csvs.extend(csv_files)
            
            # Remove duplicates and limit to 5 files
            competitor_csvs = list(set(competitor_csvs))[:5]
            
            if competitor_csvs:
                logger.info(f"Found {len(competitor_csvs)} competitor CSV files")
            
            return competitor_csvs
                
        except Exception as e:
            logger.error(f"Error finding competitor CSVs: {e}")
            return []
    
    def _extract_csv_paths_from_question(self, user_question: str, default_csv: str) -> Optional[str]:
        """
        Extract CSV file paths from user question for comparison.
        FIXED: Enhanced path extraction with fallback logic.
        
        Args:
            user_question (str): User's question
            default_csv (str): Default CSV file path
            
        Returns:
            str: Path to second CSV file, or None if not found
        """
        try:
            # Look for common time-based CSV patterns
            import re
            
            # Check for month patterns
            month_patterns = [
                r'last month', r'previous month', r'this month',
                r'january', r'february', r'march', r'april', r'may', r'june',
                r'july', r'august', r'september', r'october', r'november', r'december'
            ]
            
            for pattern in month_patterns:
                if re.search(pattern, user_question.lower()):
                    # Try to find a CSV file with the month name
                    import glob
                    potential_files = glob.glob(f"*{pattern}*.csv")
                    if potential_files:
                        return potential_files[0]
            
            # Look for weekly patterns
            week_patterns = ['weekly', 'week', 'last week', 'this week']
            for pattern in week_patterns:
                if pattern in user_question.lower():
                    potential_files = glob.glob(f"*{pattern}*.csv")
                    if potential_files:
                        return potential_files[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting CSV paths: {e}")
            return None

# FIXED: Maintain backward compatibility with existing code
def main():
    """
    Example usage of the refactored Gemini YouTube Analyzer.
    """
    try:
        # Check for API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Please set GEMINI_API_KEY environment variable")
            return
        
        # Check for CSV file
        csv_path = "yt_analytics.csv"
        if not os.path.exists(csv_path):
            print(f"Please run yt_fetch.py first to generate {csv_path}")
            return
        
        # Initialize analyzer
        analyzer = GeminiYouTubeAnalyzer(api_key=api_key)
        
        # Example questions
        example_questions = [
            "What are my top 3 performing videos and what makes them successful?",
            "How can I improve my click-through rate based on my current data?",
            "Which videos have the best audience retention and why?",
            "What patterns do you see in my video performance over time?"
        ]
        
        print("YouTube Analytics AI Analysis Examples")
        print("=" * 50)
        
        for i, question in enumerate(example_questions, 1):
            print(f"\n{i}. QUESTION: {question}")
            print("-" * 50)
            
            response = analyzer.analyze_youtube_data(question, csv_path)
            print(response)
            print("\n" + "=" * 50)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
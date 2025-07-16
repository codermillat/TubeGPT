"""
Data Analyzer Module for YouTube Analytics.
Handles CSV loading, processing, and statistical analysis with memory management.
"""

import os
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import numpy as np

# FIXED: Set up logging first before any usage
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

try:
    from charts import generate_all_charts, plot_ctr_trend, plot_views_by_country, plot_avg_duration_distribution
    CHARTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Charts module not available: {e}")
    CHARTS_AVAILABLE = False

class DataAnalyzer:
    """
    Analyzes YouTube analytics CSV data with memory management and error handling.
    """
    
    def __init__(self, chunk_size: int = 10000):
        """
        Initialize the data analyzer.
        
        Args:
            chunk_size (int): Size of chunks for processing large files
        """
        self.chunk_size = chunk_size
        logger.info("Data analyzer initialized")
    
    def load_and_summarize_csv(self, csv_path: str) -> Dict[str, Any]:
        """
        Load CSV file and create a statistical summary with memory management.
        FIXED: Added chunked processing for large files and proper memory cleanup.
        
        Args:
            csv_path (str): Path to the YouTube analytics CSV file
            
        Returns:
            dict: Summary statistics and key insights from the data
        """
        try:
            # FIXED: Validate file exists and is readable
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
            if not os.access(csv_path, os.R_OK):
                raise PermissionError(f"Cannot read CSV file: {csv_path}")
            
            # FIXED: Check file size before loading
            file_size = os.path.getsize(csv_path)
            if file_size == 0:
                raise ValueError(f"CSV file is empty: {csv_path}")
            
            # FIXED: Use chunked loading for large files
            if file_size > 50 * 1024 * 1024:  # 50MB threshold
                logger.info(f"Large file detected ({file_size / 1024 / 1024:.1f}MB), using chunked processing")
                return self._load_and_summarize_chunked(csv_path)
            
            # Load entire file for smaller datasets
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            
            # Process and get summary
            summary = self._process_dataframe(df)
            
            # FIXED: Explicit memory cleanup
            del df
            
            return summary
            
        except Exception as e:
            logger.error(f"Error loading and summarizing CSV: {e}")
            raise
    
    def _load_and_summarize_chunked(self, csv_path: str) -> Dict[str, Any]:
        """
        Load and process large CSV files in chunks.
        
        Args:
            csv_path (str): Path to CSV file
            
        Returns:
            dict: Summary statistics
        """
        summary = {
            'total_videos': 0,
            'date_range': {'earliest': None, 'latest': None},
            'columns': [],
            'views_stats': {'total': 0, 'max': 0, 'min': float('inf'), 'values': []},
            'ctr_stats': {'values': []},
            'duration_stats': {'values': []},
            'impressions_stats': {'total': 0, 'max': 0, 'min': float('inf')},
            'top_countries': {},
            'top_performers': [],
            'bottom_performers': []
        }
        
        try:
            # Process in chunks
            for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=self.chunk_size)):
                logger.info(f"Processing chunk {chunk_num + 1}")
                
                # Update summary with chunk data
                self._update_summary_with_chunk(summary, chunk)
                
                # Explicit cleanup of chunk
                del chunk
            
            # Finalize statistics
            self._finalize_chunked_summary(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in chunked processing: {e}")
            raise
    
    def _update_summary_with_chunk(self, summary: Dict[str, Any], chunk: pd.DataFrame):
        """
        Update summary statistics with data from a chunk.
        
        Args:
            summary (dict): Summary dictionary to update
            chunk (pd.DataFrame): Data chunk
        """
        # FIXED: Safe column processing
        if not summary['columns']:
            summary['columns'] = list(chunk.columns)
        
        # Update total videos
        summary['total_videos'] += len(chunk)
        
        # FIXED: Safe numeric processing
        numeric_columns = ['views', 'impressions', 'CTR', 'averageViewDuration']
        for col in numeric_columns:
            if col in chunk.columns:
                # Convert to numeric with error handling
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0)
        
        # Update date range
        if 'date' in chunk.columns:
            chunk_earliest = chunk['date'].min()
            chunk_latest = chunk['date'].max()
            
            if summary['date_range']['earliest'] is None or chunk_earliest < summary['date_range']['earliest']:
                summary['date_range']['earliest'] = chunk_earliest
            if summary['date_range']['latest'] is None or chunk_latest > summary['date_range']['latest']:
                summary['date_range']['latest'] = chunk_latest
        
        # Update views statistics
        if 'views' in chunk.columns:
            views_data = chunk['views'].dropna()
            if len(views_data) > 0:
                summary['views_stats']['total'] += views_data.sum()
                summary['views_stats']['max'] = max(summary['views_stats']['max'], views_data.max())
                summary['views_stats']['min'] = min(summary['views_stats']['min'], views_data.min())
                summary['views_stats']['values'].extend(views_data.tolist()[:100])  # Sample for final calculations
        
        # Update CTR statistics
        if 'CTR' in chunk.columns:
            ctr_data = chunk['CTR'].dropna()
            if len(ctr_data) > 0:
                summary['ctr_stats']['values'].extend(ctr_data.tolist()[:100])
        
        # Update duration statistics
        if 'averageViewDuration' in chunk.columns:
            duration_data = chunk['averageViewDuration'].dropna()
            if len(duration_data) > 0:
                summary['duration_stats']['values'].extend(duration_data.tolist()[:100])
        
        # Update country statistics
        if 'country' in chunk.columns:
            country_counts = chunk['country'].value_counts()
            for country, count in country_counts.items():
                summary['top_countries'][country] = summary['top_countries'].get(country, 0) + count
    
    def _finalize_chunked_summary(self, summary: Dict[str, Any]):
        """
        Finalize summary statistics after processing all chunks.
        
        Args:
            summary (dict): Summary dictionary to finalize
        """
        # FIXED: Safe statistical calculations
        try:
            # Views statistics
            if summary['views_stats']['values']:
                values = summary['views_stats']['values']
                summary['views_stats']['average'] = np.mean(values)
                summary['views_stats']['median'] = np.median(values)
            else:
                summary['views_stats']['average'] = 0
                summary['views_stats']['median'] = 0
            
            # CTR statistics
            if summary['ctr_stats']['values']:
                values = summary['ctr_stats']['values']
                summary['ctr_stats']['average'] = np.mean(values) * 100  # Convert to percentage
                summary['ctr_stats']['median'] = np.median(values) * 100
                summary['ctr_stats']['max'] = np.max(values) * 100
                summary['ctr_stats']['min'] = np.min(values) * 100
            else:
                summary['ctr_stats'].update({'average': 0, 'median': 0, 'max': 0, 'min': 0})
            
            # Duration statistics
            if summary['duration_stats']['values']:
                values = summary['duration_stats']['values']
                summary['duration_stats']['average'] = np.mean(values)
                summary['duration_stats']['median'] = np.median(values)
                summary['duration_stats']['max'] = np.max(values)
                summary['duration_stats']['min'] = np.min(values)
            else:
                summary['duration_stats'].update({'average': 0, 'median': 0, 'max': 0, 'min': 0})
            
            # Sort top countries
            summary['top_countries'] = dict(sorted(summary['top_countries'].items(), 
                                                 key=lambda x: x[1], reverse=True)[:10])
            
            # Clean up temporary values arrays
            for stat_key in ['views_stats', 'ctr_stats', 'duration_stats']:
                if 'values' in summary[stat_key]:
                    del summary[stat_key]['values']
            
        except Exception as e:
            logger.error(f"Error finalizing summary: {e}")
            # Continue with partial summary
    
    def _process_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process a complete dataframe and generate summary statistics.
        
        Args:
            df (pd.DataFrame): The dataframe to process
            
        Returns:
            dict: Summary statistics
        """
        # FIXED: Ensure numeric columns are properly typed
        numeric_columns = ['views', 'impressions', 'CTR', 'averageViewDuration']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Basic dataset info
        summary = {
            'total_videos': len(df),
            'date_range': {
                'earliest': df['date'].min() if 'date' in df.columns else 'Unknown',
                'latest': df['date'].max() if 'date' in df.columns else 'Unknown'
            },
            'columns': list(df.columns)
        }
        
        # FIXED: Safe statistical calculations with error handling
        try:
            # Performance metrics summary
            if 'views' in df.columns:
                views_data = df['views'].dropna()
                if len(views_data) > 0:
                    summary['views_stats'] = {
                        'total': int(views_data.sum()),
                        'average': round(views_data.mean(), 2),
                        'median': int(views_data.median()),
                        'max': int(views_data.max()),
                        'min': int(views_data.min())
                    }
                else:
                    summary['views_stats'] = {'total': 0, 'average': 0, 'median': 0, 'max': 0, 'min': 0}
            
            if 'impressions' in df.columns:
                impressions_data = df['impressions'].dropna()
                if len(impressions_data) > 0:
                    summary['impressions_stats'] = {
                        'total': int(impressions_data.sum()),
                        'average': round(impressions_data.mean(), 2),
                        'max': int(impressions_data.max()),
                        'min': int(impressions_data.min())
                    }
                else:
                    summary['impressions_stats'] = {'total': 0, 'average': 0, 'max': 0, 'min': 0}
            
            if 'CTR' in df.columns:
                ctr_data = df['CTR'].dropna()
                if len(ctr_data) > 0:
                    summary['ctr_stats'] = {
                        'average': round(ctr_data.mean() * 100, 2),  # Convert to percentage
                        'median': round(ctr_data.median() * 100, 2),
                        'max': round(ctr_data.max() * 100, 2),
                        'min': round(ctr_data.min() * 100, 2)
                    }
                else:
                    summary['ctr_stats'] = {'average': 0, 'median': 0, 'max': 0, 'min': 0}
            
            if 'averageViewDuration' in df.columns:
                duration_data = df['averageViewDuration'].dropna()
                if len(duration_data) > 0:
                    summary['duration_stats'] = {
                        'average': round(duration_data.mean(), 2),
                        'median': round(duration_data.median(), 2),
                        'max': round(duration_data.max(), 2),
                        'min': round(duration_data.min(), 2)
                    }
                else:
                    summary['duration_stats'] = {'average': 0, 'median': 0, 'max': 0, 'min': 0}
            
            # Top and bottom performers
            summary['top_performers'] = self._get_top_performers(df)
            summary['bottom_performers'] = self._get_bottom_performers(df)
            
            # Country analysis if available
            if 'country' in df.columns:
                country_counts = df['country'].value_counts().head(10)
                summary['top_countries'] = country_counts.to_dict()
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            # Continue with partial summary
        
        return summary
    
    def _get_top_performers(self, df: pd.DataFrame, n: int = 3) -> List[Dict[str, Any]]:
        """
        Get top performing videos based on various metrics.
        
        Args:
            df (pd.DataFrame): The dataframe to analyze
            n (int): Number of top performers to return
            
        Returns:
            list: List of top performing videos
        """
        try:
            top_performers = []
            
            # FIXED: Safe data access with validation
            if 'views' in df.columns and 'videoTitle' in df.columns:
                top_views = df.nlargest(n, 'views')
                for _, row in top_views.iterrows():
                    performer = {
                        'title': str(row.get('videoTitle', 'Unknown')),
                        'views': int(row.get('views', 0)),
                        'metric': 'views'
                    }
                    if 'CTR' in df.columns:
                        performer['ctr'] = round(row.get('CTR', 0) * 100, 2)
                    if 'averageViewDuration' in df.columns:
                        performer['duration'] = round(row.get('averageViewDuration', 0), 1)
                    top_performers.append(performer)
            
            return top_performers
            
        except Exception as e:
            logger.error(f"Error getting top performers: {e}")
            return []
    
    def _get_bottom_performers(self, df: pd.DataFrame, n: int = 3) -> List[Dict[str, Any]]:
        """
        Get bottom performing videos based on various metrics.
        
        Args:
            df (pd.DataFrame): The dataframe to analyze
            n (int): Number of bottom performers to return
            
        Returns:
            list: List of bottom performing videos
        """
        try:
            bottom_performers = []
            
            # FIXED: Safe data access with validation
            if 'views' in df.columns and 'videoTitle' in df.columns:
                bottom_views = df.nsmallest(n, 'views')
                for _, row in bottom_views.iterrows():
                    performer = {
                        'title': str(row.get('videoTitle', 'Unknown')),
                        'views': int(row.get('views', 0)),
                        'metric': 'views'
                    }
                    if 'CTR' in df.columns:
                        performer['ctr'] = round(row.get('CTR', 0) * 100, 2)
                    if 'averageViewDuration' in df.columns:
                        performer['duration'] = round(row.get('averageViewDuration', 0), 1)
                    bottom_performers.append(performer)
            
            return bottom_performers
            
        except Exception as e:
            logger.error(f"Error getting bottom performers: {e}")
            return []
    
    def generate_charts_if_requested(self, user_question: str, csv_path: str) -> Optional[Dict[str, str]]:
        """
        Generate charts if requested by user and charts module is available.
        
        Args:
            user_question (str): User's question
            csv_path (str): Path to CSV file
            
        Returns:
            dict: Dictionary of chart names to file paths, or None
        """
        if not CHARTS_AVAILABLE:
            logger.warning("Charts module not available")
            return None
        
        # FIXED: Safe chart generation with error handling
        try:
            # Check if user is asking for charts/visualizations
            chart_keywords = ['chart', 'graph', 'plot', 'visual', 'trend', 'distribution']
            if any(keyword in user_question.lower() for keyword in chart_keywords):
                logger.info("User requested charts, generating visualizations...")
                
                charts = generate_all_charts(csv_path)
                if charts:
                    logger.info(f"Generated {len(charts)} charts")
                    return charts
                else:
                    logger.warning("No charts were generated")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
            return None
    
    def detect_comparison_request(self, user_question: str) -> bool:
        """
        Detect if user is asking for a comparison between datasets.
        
        Args:
            user_question (str): User's question
            
        Returns:
            bool: True if comparison is requested
        """
        comparison_keywords = [
            'compare', 'comparison', 'versus', 'vs', 'difference', 
            'between', 'last month', 'previous', 'before', 'after',
            'then vs now', 'trend', 'change'
        ]
        
        return any(keyword in user_question.lower() for keyword in comparison_keywords)
    
    def detect_gap_analysis_request(self, user_question: str) -> bool:
        """
        Detect if user is asking for gap analysis.
        
        Args:
            user_question (str): User's question
            
        Returns:
            bool: True if gap analysis is requested
        """
        gap_keywords = [
            'gap', 'missing', 'opportunity', 'competitor', 'should create',
            'content idea', 'what to make', 'suggestions', 'recommendations',
            'underperforming', 'improve', 'optimize'
        ]
        
        return any(keyword in user_question.lower() for keyword in gap_keywords) 
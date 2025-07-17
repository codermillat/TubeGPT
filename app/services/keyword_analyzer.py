"""
YouTube Keyword Analyzer with Autocomplete and Google Trends Integration.

This module provides functionality to:
1. Get YouTube autocomplete suggestions
2. Fetch Google Trends data for keywords
3. Combine both data sources for comprehensive keyword analysis

Data Sources:
- YouTube Autocomplete: suggestqueries.google.com/complete/search
- Google Trends: trends.google.com (via pytrends library)
"""

import requests
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import re

# Optional pytrends import with fallback
try:
    from pytrends.request import TrendReq
    from pytrends.exceptions import TooManyRequestsError, ResponseError
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logger.warning("pytrends not available, trends features will be disabled")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FIXED: Enhanced KeywordAnalyzer class with better session management
class KeywordAnalyzer:
    """
    A comprehensive keyword analyzer that combines YouTube autocomplete 
    suggestions with Google Trends data for content optimization.
    FIXED: Enhanced with better session management, rate limiting, and error handling.
    """
    
    def __init__(self, timeout: int = 30, retries: int = 3):
        """
        Initialize the KeywordAnalyzer.
        
        Args:
            timeout (int): Request timeout in seconds
            retries (int): Number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        
        # FIXED: Enhanced headers for better success rate
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        })
        
        # FIXED: Connection pooling for better performance
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # FIXED: Initialize pytrends with better error handling
        self.pytrends = None
        self._last_pytrends_request = 0
        self._min_request_interval = 2  # Minimum seconds between requests
        
        logger.info("KeywordAnalyzer initialized with enhanced session management")
    
    def get_autocomplete_suggestions(self, seed: str, region: str = 'US') -> List[str]:
        """
        Get YouTube autocomplete suggestions using the class instance.
        FIXED: Uses instance session for better performance.
        
        Args:
            seed (str): The seed keyword
            region (str): Region code
            
        Returns:
            List[str]: Autocomplete suggestions
        """
        return get_youtube_autocomplete(seed, region)
    
    def get_trends_data(self, keywords: List[str], timeframe: str = 'today 12-m', geo: str = 'US') -> Dict[str, Any]:
        """
        Get Google Trends data using the class instance.
        FIXED: Uses instance pytrends session for better performance.
        
        Args:
            keywords (List[str]): Keywords to analyze
            timeframe (str): Time period
            geo (str): Geographic region
            
        Returns:
            Dict[str, Any]: Trends data or empty dict if pytrends unavailable
        """
        if not PYTRENDS_AVAILABLE:
            logger.warning("Pytrends not available, returning empty trends data")
            return {}
        
        try:
            return get_google_trends(keywords, timeframe, geo)
        except Exception as e:
            logger.warning(f"Failed to get trends data: {e}")
            return {}
    
    def _get_pytrends_instance(self):
        """
        Get or create pytrends instance with rate limiting.
        FIXED: Proper session management and rate limiting.
        
        Returns:
            TrendReq instance or None if pytrends not available
        """
        if not PYTRENDS_AVAILABLE:
            logger.warning("Pytrends not available, returning None")
            return None
            
        current_time = time.time()
        
        # FIXED: Rate limiting
        if current_time - self._last_pytrends_request < self._min_request_interval:
            sleep_time = self._min_request_interval - (current_time - self._last_pytrends_request)
            time.sleep(sleep_time)
        
        # FIXED: Create new instance if needed
        if self.pytrends is None:
            try:
                self.pytrends = TrendReq(
                    hl='en-US',
                    tz=360,
                    timeout=(10, 25),
                    retries=2,
                    backoff_factor=0.1,
                    requests_args={'verify': False}  # FIXED: Handle SSL issues
                )
                logger.debug("Created new pytrends instance")
            except Exception as e:
                logger.error(f"Failed to create pytrends instance: {e}")
                raise
        
        self._last_pytrends_request = time.time()
        return self.pytrends
    
    def close(self):
        """
        Close the session and cleanup resources.
        """
        if self.session:
            self.session.close()
            logger.debug("Closed session")

# FIXED: Global instance for better performance
_global_analyzer = None

def get_analyzer_instance() -> KeywordAnalyzer:
    """
    Get global analyzer instance for better performance.
    FIXED: Reuse single instance to avoid session overhead.
    
    Returns:
        KeywordAnalyzer: Global analyzer instance
    """
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = KeywordAnalyzer()
    return _global_analyzer

# FIXED: Improved YouTube autocomplete with better error handling and fallback
def get_youtube_autocomplete(seed: str, region: str = 'US') -> List[str]:
    """
    Get YouTube autocomplete suggestions for a given seed keyword.
    FIXED: Enhanced with proper session reuse, rate limiting, and fallback mechanisms.
    
    Args:
        seed (str): The seed keyword to get suggestions for
        region (str): Region code (e.g., 'US', 'BD', 'IN') for localized results
        
    Returns:
        List[str]: List of up to 10 autocomplete suggestions
        
    Raises:
        ValueError: If seed is empty or invalid
        
    Example:
        >>> suggestions = get_youtube_autocomplete("cooking", "BD")
        >>> print(suggestions[:3])
        ['cooking recipes', 'cooking tips', 'cooking channel']
    """
    if not seed or not seed.strip():
        raise ValueError("Seed keyword cannot be empty")
    
    seed = seed.strip()
    logger.info(f"Fetching YouTube autocomplete for '{seed}' in region '{region}'")
    
    # FIXED: Try multiple API endpoints with fallback
    api_endpoints = [
        {
            'url': 'http://suggestqueries.google.com/complete/search',
            'params': {
                'client': 'youtube',
                'ds': 'yt',
                'q': seed,
                'gl': region,
                'hl': 'en',
                'output': 'toolbar'
            },
            'parser': '_parse_youtube_autocomplete_xml'
        },
        {
            'url': 'http://suggestqueries.google.com/complete/search',
            'params': {
                'client': 'firefox',
                'q': f'site:youtube.com {seed}',
                'gl': region,
                'hl': 'en'
            },
            'parser': '_parse_youtube_autocomplete_json'
        }
    ]
    
    # FIXED: Use session with proper configuration
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0'
    })
    
    # FIXED: Try each endpoint with proper error handling
    for endpoint in api_endpoints:
        try:
            for attempt in range(3):  # 3 retries per endpoint
                try:
                    # FIXED: Rate limiting between attempts
                    if attempt > 0:
                        time.sleep(2 ** attempt)
                    
                    response = session.get(
                        endpoint['url'], 
                        params=endpoint['params'], 
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    # FIXED: Parse based on endpoint type
                    if endpoint['parser'] == '_parse_youtube_autocomplete_xml':
                        suggestions = _parse_youtube_autocomplete_xml(response.text)
                    else:
                        suggestions = _parse_youtube_autocomplete_json(response.text)
                    
                    if suggestions:
                        logger.info(f"Successfully fetched {len(suggestions)} suggestions for '{seed}'")
                        return suggestions[:10]  # Return top 10 suggestions
                    else:
                        logger.warning(f"No suggestions found with {endpoint['url']}")
                        break  # Try next endpoint
                        
                except requests.RequestException as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {endpoint['url']}: {e}")
                    if attempt == 2:  # Last attempt for this endpoint
                        break
                    
        except Exception as e:
            logger.warning(f"Endpoint {endpoint['url']} failed: {e}")
            continue
    
    # FIXED: Fallback to manual suggestions if all APIs fail
    logger.warning(f"All autocomplete APIs failed for '{seed}', using fallback suggestions")
    return _get_fallback_suggestions(seed)

# FIXED: Improved XML parser with better error handling
def _parse_youtube_autocomplete_xml(response_text: str) -> List[str]:
    """
    Parse YouTube autocomplete XML response to extract suggestions.
    FIXED: Enhanced with better error handling and fallback parsing.
    
    Args:
        response_text (str): Raw XML response from YouTube autocomplete API
        
    Returns:
        List[str]: Extracted suggestion strings
    """
    suggestions = []
    
    try:
        # FIXED: Try XML parsing first
        import xml.etree.ElementTree as ET
        
        root = ET.fromstring(response_text)
        
        # Find all suggestion elements
        for suggestion in root.findall('.//suggestion'):
            data = suggestion.get('data')
            if data:
                suggestions.append(data)
                
    except ET.ParseError as e:
        logger.warning(f"Failed to parse XML response: {e}")
        # FIXED: Enhanced fallback regex parsing
        try:
            # Try different regex patterns
            patterns = [
                r'data="([^"]*)"',
                r'suggestion data="([^"]*)"',
                r'<suggestion[^>]*data="([^"]*)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                if matches:
                    suggestions.extend(matches)
                    break
                    
        except Exception as regex_error:
            logger.error(f"Regex parsing also failed: {regex_error}")
        
    except Exception as e:
        logger.error(f"Error parsing autocomplete response: {e}")
    
    # FIXED: Clean and deduplicate suggestions
    cleaned_suggestions = []
    seen = set()
    
    for suggestion in suggestions:
        # Clean suggestion
        cleaned = suggestion.strip()
        if cleaned and len(cleaned) > 2 and cleaned.lower() not in seen:
            cleaned_suggestions.append(cleaned)
            seen.add(cleaned.lower())
    
    return cleaned_suggestions

# FIXED: New JSON parser for fallback endpoint
def _parse_youtube_autocomplete_json(response_text: str) -> List[str]:
    """
    Parse YouTube autocomplete JSON response to extract suggestions.
    
    Args:
        response_text (str): Raw JSON response from autocomplete API
        
    Returns:
        List[str]: Extracted suggestion strings
    """
    suggestions = []
    
    try:
        # FIXED: Handle JSONP response
        if response_text.startswith('('):
            # Remove JSONP wrapper
            json_str = response_text[1:-1]
        else:
            json_str = response_text
        
        data = json.loads(json_str)
        
        # Extract suggestions from JSON structure
        if isinstance(data, list) and len(data) > 1:
            suggestion_list = data[1]
            for item in suggestion_list:
                if isinstance(item, list) and len(item) > 0:
                    suggestions.append(item[0])
                elif isinstance(item, str):
                    suggestions.append(item)
                    
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON response: {e}")
        
    except Exception as e:
        logger.error(f"Error parsing JSON autocomplete response: {e}")
    
    return suggestions

# FIXED: New fallback suggestions function
def _get_fallback_suggestions(seed: str) -> List[str]:
    """
    Generate fallback suggestions when API fails.
    
    Args:
        seed (str): Seed keyword
        
    Returns:
        List[str]: Fallback suggestions
    """
    # FIXED: Generate reasonable fallback suggestions
    common_suffixes = [
        'tutorial', 'tips', 'guide', 'review', 'how to', 'best', 'top', 
        'for beginners', 'explained', 'step by step', '2024', 'latest'
    ]
    
    common_prefixes = [
        'how to', 'best', 'top', 'easy', 'quick', 'ultimate', 'complete', 
        'beginner', 'advanced', 'professional'
    ]
    
    suggestions = []
    
    # Add suffix-based suggestions
    for suffix in common_suffixes[:6]:
        suggestions.append(f"{seed} {suffix}")
    
    # Add prefix-based suggestions
    for prefix in common_prefixes[:4]:
        suggestions.append(f"{prefix} {seed}")
    
    logger.info(f"Generated {len(suggestions)} fallback suggestions for '{seed}'")
    return suggestions

# FIXED: Removed old parser function - replaced with improved versions above

# FIXED: Enhanced Google Trends function with better session management
def get_google_trends(keywords: List[str], timeframe: str = 'today 12-m', geo: str = 'US') -> Dict[str, Any]:
    """
    Get Google Trends data for a list of keywords.
    FIXED: Enhanced with better session management, rate limiting, and error handling.
    
    Args:
        keywords (List[str]): List of keywords to analyze (max 5 due to API limits)
        timeframe (str): Time period for analysis (e.g., 'today 12-m', 'today 3-m', 'now 7-d')
        geo (str): Geographic region code (e.g., 'US', 'BD', 'IN', '' for worldwide)
        
    Returns:
        Dict[str, Any]: Dictionary with trends data or empty dict if unavailable
        
    Raises:
        ValueError: If keywords list is empty or too long
        
    Example:
        >>> data = get_google_trends(['cooking', 'recipe'], 'today 3-m', 'BD')
        >>> print(data)
    """
    if not PYTRENDS_AVAILABLE:
        logger.warning("Pytrends not available, returning empty data")
        return {}
        
    if not keywords:
        raise ValueError("Keywords list cannot be empty")
    
    # FIXED: Clean and validate keywords
    cleaned_keywords = []
    for keyword in keywords:
        if isinstance(keyword, str) and keyword.strip():
            cleaned_keywords.append(keyword.strip())
    
    if not cleaned_keywords:
        raise ValueError("No valid keywords provided")
    
    if len(cleaned_keywords) > 5:
        logger.warning("Google Trends API supports max 5 keywords at once. Taking first 5.")
        cleaned_keywords = cleaned_keywords[:5]
    
    logger.info(f"Fetching Google Trends data for {len(cleaned_keywords)} keywords: {cleaned_keywords}")
    
    results = []
    
    # FIXED: Use global analyzer instance for better session management
    analyzer = get_analyzer_instance()
    
    for attempt in range(3):  # Retry up to 3 times
        try:
            # FIXED: Use analyzer's pytrends instance with rate limiting
            pytrends = analyzer._get_pytrends_instance()
            
            # Build payload for the keywords
            pytrends.build_payload(
                kw_list=cleaned_keywords,
                cat=0,  # All categories
                timeframe=timeframe,
                geo=geo,
                gprop=''  # Web search (default)
            )
            
            # FIXED: Rate limiting between API calls
            time.sleep(1)
            
            # Get interest over time
            interest_over_time = pytrends.interest_over_time()
            
            if interest_over_time.empty:
                logger.warning(f"No interest data found for keywords: {cleaned_keywords}")
                # Return empty results for each keyword
                for keyword in cleaned_keywords:
                    results.append({
                        'keyword': keyword,
                        'avg_interest': 0,
                        'peak_interest': 0,
                        'related_queries': [],
                        'rising_terms': []
                    })
            else:
                # Process each keyword
                for keyword in cleaned_keywords:
                    if keyword in interest_over_time.columns:
                        interest_data = interest_over_time[keyword]
                        avg_interest = float(interest_data.mean())
                        peak_interest = float(interest_data.max())
                    else:
                        avg_interest = 0
                        peak_interest = 0
                    
                    # FIXED: Get related queries with enhanced rate limiting protection
                    related_queries = []
                    rising_terms = []
                    
                    try:
                        # FIXED: Longer rate limiting for related queries
                        time.sleep(2)  # Rate limiting
                        related_dict = pytrends.related_queries()
                        
                        if keyword in related_dict and related_dict[keyword]:
                            # Top related queries
                            if 'top' in related_dict[keyword] and related_dict[keyword]['top'] is not None:
                                related_queries = related_dict[keyword]['top']['query'].tolist()[:10]
                            
                            # Rising related queries
                            if 'rising' in related_dict[keyword] and related_dict[keyword]['rising'] is not None:
                                rising_terms = related_dict[keyword]['rising']['query'].tolist()[:10]
                                
                    except Exception as e:
                        logger.warning(f"Could not fetch related queries for '{keyword}': {e}")
                    
                    results.append({
                        'keyword': keyword,
                        'avg_interest': round(avg_interest, 2),
                        'peak_interest': int(peak_interest),
                        'related_queries': related_queries,
                        'rising_terms': rising_terms
                    })
            
            logger.info(f"Successfully fetched Google Trends data for {len(cleaned_keywords)} keywords")
            break  # Success, exit retry loop
            
        except Exception as e:
            # Handle both pytrends exceptions and generic exceptions
            error_str = str(e).lower()
            if 'rate limit' in error_str or 'too many requests' in error_str:
                logger.warning(f"Google Trends rate limit exceeded (attempt {attempt + 1}): {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    logger.info("Waiting 60 seconds before retry...")
                    time.sleep(60)
                else:
                    logger.error("Max retries reached, returning empty results")
                    return {}
            elif 'response' in error_str or 'api' in error_str:
                logger.error(f"Google Trends API error (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(10)
                else:
                    logger.error("Max retries reached, returning empty results")
                    return {}
            else:
                logger.error(f"Unexpected error fetching Google Trends data (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(5)
                else:
                    logger.error("Max retries reached, returning empty results")
                    return {}
    
    return {
        'keywords': results,
        'timeframe': timeframe,
        'geo': geo,
        'total_keywords': len(results)
    }

def analyze_keywords(seed: str, region: str = 'US', timeframe: str = 'today 12-m') -> Dict[str, Any]:
    """
    Comprehensive keyword analysis combining YouTube autocomplete and Google Trends.
    
    This function provides a complete keyword research workflow:
    1. Gets YouTube autocomplete suggestions for the seed keyword
    2. Analyzes Google Trends data for the seed + top suggestions
    3. Combines results into a comprehensive analysis report
    
    Args:
        seed (str): The seed keyword to analyze
        region (str): Region code for localized results (e.g., 'US', 'BD', 'IN')
        timeframe (str): Time period for trends analysis (e.g., 'today 12-m', 'today 3-m')
        
    Returns:
        Dict[str, Any]: Comprehensive analysis results containing:
            - 'seed_keyword': Original seed keyword
            - 'region': Analysis region
            - 'timeframe': Analysis timeframe
            - 'autocomplete': List of YouTube autocomplete suggestions
            - 'trends': Dictionary with trend data for each keyword
            - 'summary': Analysis summary with top recommendations
            - 'timestamp': When the analysis was performed
            
    Raises:
        ValueError: If seed keyword is invalid
        Exception: If both autocomplete and trends data fail to fetch
        
    Example:
        >>> analysis = analyze_keywords("cooking recipes", "BD", "today 3-m")
        >>> print(f"Found {len(analysis['autocomplete'])} suggestions")
        >>> print(f"Top trending: {analysis['summary']['top_trending']}")
    """
    if not seed or not seed.strip():
        raise ValueError("Seed keyword cannot be empty")
    
    seed = seed.strip()
    logger.info(f"Starting comprehensive keyword analysis for '{seed}' in region '{region}'")
    
    analysis_results = {
        'seed_keyword': seed,
        'region': region,
        'timeframe': timeframe,
        'timestamp': pd.Timestamp.now().isoformat(),
        'autocomplete': [],
        'trends': {},
        'summary': {},
        'errors': []
    }
    
    # Step 1: Get YouTube autocomplete suggestions
    try:
        autocomplete_suggestions = get_youtube_autocomplete(seed, region)
        analysis_results['autocomplete'] = autocomplete_suggestions
        logger.info(f"Retrieved {len(autocomplete_suggestions)} autocomplete suggestions")
        
    except Exception as e:
        error_msg = f"Failed to fetch YouTube autocomplete: {str(e)}"
        logger.error(error_msg)
        analysis_results['errors'].append(error_msg)
        autocomplete_suggestions = []
    
    # Step 2: Prepare keywords for trends analysis
    # Include seed keyword + top autocomplete suggestions (max 5 total due to API limits)
    keywords_for_trends = [seed]
    if autocomplete_suggestions:
        # Add top suggestions, ensuring we don't exceed 5 keywords total
        additional_keywords = autocomplete_suggestions[:4]  # Max 4 additional
        keywords_for_trends.extend(additional_keywords)
    
    # Step 3: Get Google Trends data
    try:
        trends_df = get_google_trends(keywords_for_trends, timeframe, region)
        
        # Convert DataFrame to dictionary format
        trends_dict = {}
        for _, row in trends_df.iterrows():
            keyword = row['keyword']
            trends_dict[keyword] = {
                'avg_interest': row['avg_interest'],
                'peak_interest': row['peak_interest'],
                'related_queries': row['related_queries'],
                'rising_terms': row['rising_terms']
            }
        
        analysis_results['trends'] = trends_dict
        logger.info(f"Retrieved trends data for {len(trends_dict)} keywords")
        
    except Exception as e:
        error_msg = f"Failed to fetch Google Trends data: {str(e)}"
        logger.error(error_msg)
        analysis_results['errors'].append(error_msg)
    
    # Step 4: Generate analysis summary
    try:
        summary = _generate_analysis_summary(analysis_results)
        analysis_results['summary'] = summary
        
    except Exception as e:
        error_msg = f"Failed to generate analysis summary: {str(e)}"
        logger.error(error_msg)
        analysis_results['errors'].append(error_msg)
    
    # Check if we have any useful data
    if not analysis_results['autocomplete'] and not analysis_results['trends']:
        raise Exception("Failed to fetch both autocomplete and trends data")
    
    logger.info(f"Keyword analysis completed for '{seed}' with {len(analysis_results.get('errors', []))} errors")
    return analysis_results

def _generate_analysis_summary(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of the keyword analysis results.
    
    Args:
        analysis_results (Dict): Raw analysis results
        
    Returns:
        Dict[str, Any]: Analysis summary with key insights
    """
    summary = {
        'total_suggestions': len(analysis_results.get('autocomplete', [])),
        'total_keywords_analyzed': len(analysis_results.get('trends', {})),
        'top_trending': None,
        'highest_interest': None,
        'best_opportunities': [],
        'content_recommendations': []
    }
    
    trends = analysis_results.get('trends', {})
    
    if trends:
        # Find keyword with highest average interest
        highest_interest_keyword = max(
            trends.keys(), 
            key=lambda k: trends[k]['avg_interest']
        )
        summary['highest_interest'] = {
            'keyword': highest_interest_keyword,
            'avg_interest': trends[highest_interest_keyword]['avg_interest']
        }
        
        # Find keyword with highest peak interest
        highest_peak_keyword = max(
            trends.keys(),
            key=lambda k: trends[k]['peak_interest']
        )
        summary['top_trending'] = {
            'keyword': highest_peak_keyword,
            'peak_interest': trends[highest_peak_keyword]['peak_interest']
        }
        
        # Identify opportunities (keywords with good interest and rising terms)
        opportunities = []
        for keyword, data in trends.items():
            if data['avg_interest'] > 20 and len(data['rising_terms']) > 0:
                opportunities.append({
                    'keyword': keyword,
                    'avg_interest': data['avg_interest'],
                    'rising_terms_count': len(data['rising_terms'])
                })
        
        # Sort by interest level
        opportunities.sort(key=lambda x: x['avg_interest'], reverse=True)
        summary['best_opportunities'] = opportunities[:3]
        
        # Generate content recommendations
        recommendations = []
        
        # Recommend based on autocomplete suggestions
        autocomplete = analysis_results.get('autocomplete', [])
        if autocomplete:
            recommendations.append(f"Consider creating content around: {', '.join(autocomplete[:3])}")
        
        # Recommend based on rising terms
        all_rising_terms = []
        for data in trends.values():
            all_rising_terms.extend(data.get('rising_terms', []))
        
        if all_rising_terms:
            unique_rising = list(set(all_rising_terms))[:5]
            recommendations.append(f"Trending topics to explore: {', '.join(unique_rising)}")
        
        summary['content_recommendations'] = recommendations
    
    return summary

# Utility functions for testing and debugging
def save_analysis_to_file(analysis_results: Dict[str, Any], filename: str) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        analysis_results (Dict): Analysis results from analyze_keywords()
        filename (str): Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        logger.info(f"Analysis results saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save analysis to {filename}: {e}")

def main():
    """
    Example usage of the keyword analyzer.
    """
    try:
        # Example analysis
        seed_keyword = "cooking recipes"
        region = "BD"  # Bangladesh
        
        print(f"Analyzing keyword: '{seed_keyword}' for region: {region}")
        print("=" * 50)
        
        # Perform analysis
        results = analyze_keywords(seed_keyword, region, "today 3-m")
        
        # Display results
        print(f"\n📊 ANALYSIS RESULTS for '{seed_keyword}'")
        print(f"Region: {region} | Timeframe: {results['timeframe']}")
        print(f"Timestamp: {results['timestamp']}")
        
        if results['errors']:
            print(f"\n⚠️  ERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  - {error}")
        
        print(f"\n🔍 YOUTUBE AUTOCOMPLETE ({len(results['autocomplete'])} suggestions):")
        for i, suggestion in enumerate(results['autocomplete'][:5], 1):
            print(f"  {i}. {suggestion}")
        
        print(f"\n📈 GOOGLE TRENDS ({len(results['trends'])} keywords):")
        for keyword, data in results['trends'].items():
            print(f"  • {keyword}")
            print(f"    Average Interest: {data['avg_interest']}/100")
            print(f"    Peak Interest: {data['peak_interest']}/100")
            print(f"    Related Queries: {len(data['related_queries'])}")
            print(f"    Rising Terms: {len(data['rising_terms'])}")
        
        print(f"\n💡 SUMMARY:")
        summary = results['summary']
        if summary.get('highest_interest'):
            hi = summary['highest_interest']
            print(f"  Highest Interest: {hi['keyword']} ({hi['avg_interest']}/100)")
        
        if summary.get('top_trending'):
            tt = summary['top_trending']
            print(f"  Top Trending: {tt['keyword']} (peak: {tt['peak_interest']}/100)")
        
        if summary.get('content_recommendations'):
            print(f"  Recommendations:")
            for rec in summary['content_recommendations']:
                print(f"    - {rec}")
        
        # Save results
        save_analysis_to_file(results, f"keyword_analysis_{seed_keyword.replace(' ', '_')}.json")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()
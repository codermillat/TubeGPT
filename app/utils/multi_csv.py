import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _load_and_validate_csv(csv_path: str) -> pd.DataFrame:
    """
    Load and validate CSV file for comparison.
    
    Args:
        csv_path (str): Path to CSV file
        
    Returns:
        pd.DataFrame: Loaded and validated dataframe
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV {csv_path} with {len(df)} rows and {len(df.columns)} columns")
        
        # Ensure we have at least one identifier column
        required_id_columns = ['videoId', 'videoTitle']
        if not any(col in df.columns for col in required_id_columns):
            raise ValueError(f"CSV must contain at least one of: {required_id_columns}")
        
        return df
    except Exception as e:
        logger.error(f"Error loading CSV {csv_path}: {e}")
        raise ValueError(f"Failed to load CSV file {csv_path}: {e}")

def _ensure_numeric_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Ensure a column is numeric, converting if necessary.
    
    Args:
        df (pd.DataFrame): Input dataframe
        column (str): Column name to convert
        
    Returns:
        pd.DataFrame: Dataframe with numeric column
    """
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0)
    return df

def _match_videos(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    Match videos between two dataframes using videoId or videoTitle.
    
    Args:
        df1 (pd.DataFrame): First dataframe
        df2 (pd.DataFrame): Second dataframe
        
    Returns:
        pd.DataFrame: Merged dataframe with matched videos
    """
    # Prepare merge keys
    merge_key = None
    
    # Try to merge by videoId first (most reliable)
    if 'videoId' in df1.columns and 'videoId' in df2.columns:
        merge_key = 'videoId'
        logger.info("Matching videos by videoId")
    # Fallback to videoTitle
    elif 'videoTitle' in df1.columns and 'videoTitle' in df2.columns:
        merge_key = 'videoTitle'
        logger.info("Matching videos by videoTitle")
    else:
        raise ValueError("Cannot match videos: no common identifier column found")
    
    # Perform inner join to get only matching videos
    merged_df = pd.merge(
        df1, df2, 
        on=merge_key, 
        how='inner', 
        suffixes=('_csv1', '_csv2')
    )
    
    logger.info(f"Matched {len(merged_df)} videos out of {len(df1)} and {len(df2)} total videos")
    
    if len(merged_df) == 0:
        logger.warning("No matching videos found between the two CSV files")
    
    return merged_df

def compare_csvs(csv1_path: str, csv2_path: str, metric: str = 'views') -> List[Dict[str, Any]]:
    """
    Compare a specific metric between two YouTube analytics CSV files.
    
    Args:
        csv1_path (str): Path to first CSV file (baseline)
        csv2_path (str): Path to second CSV file (comparison)
        metric (str): Metric to compare (views, CTR, impressions, averageViewDuration)
        
    Returns:
        List[Dict]: List of comparison results with video info and metric changes
        
    Raises:
        FileNotFoundError: If either CSV file doesn't exist
        ValueError: If metric column is missing or no videos match
    """
    try:
        logger.info(f"Comparing metric '{metric}' between {csv1_path} and {csv2_path}")
        
        # Load both CSV files
        df1 = _load_and_validate_csv(csv1_path)
        df2 = _load_and_validate_csv(csv2_path)
        
        # Validate metric exists in both files
        if metric not in df1.columns:
            raise ValueError(f"Metric '{metric}' not found in {csv1_path}. Available columns: {list(df1.columns)}")
        if metric not in df2.columns:
            raise ValueError(f"Metric '{metric}' not found in {csv2_path}. Available columns: {list(df2.columns)}")
        
        # Ensure metric columns are numeric
        df1 = _ensure_numeric_column(df1, metric)
        df2 = _ensure_numeric_column(df2, metric)
        
        # Match videos between the two dataframes
        merged_df = _match_videos(df1, df2)
        
        if len(merged_df) == 0:
            return []
        
        # Calculate metric changes
        metric_col1 = f"{metric}_csv1"
        metric_col2 = f"{metric}_csv2"
        
        # Calculate absolute and percentage changes
        merged_df['metric_change'] = merged_df[metric_col2] - merged_df[metric_col1]
        merged_df['metric_change_percent'] = (
            (merged_df[metric_col2] - merged_df[metric_col1]) / 
            merged_df[metric_col1].replace(0, 1)  # Avoid division by zero
        ) * 100
        
        # Prepare results
        results = []
        
        for _, row in merged_df.iterrows():
            # Get video identifier (prefer videoId, fallback to videoTitle)
            video_id = row.get('videoId', row.get('videoTitle', 'Unknown'))
            video_title = row.get('videoTitle_csv1') or row.get('videoTitle_csv2') or row.get('videoTitle', 'Unknown Title')
            
            result = {
                'videoId': video_id,
                'videoTitle': video_title,
                'metric': metric,
                'value_csv1': float(row[metric_col1]),
                'value_csv2': float(row[metric_col2]),
                'metric_change': float(row['metric_change']),
                'metric_change_percent': float(row['metric_change_percent']),
                'csv1_path': csv1_path,
                'csv2_path': csv2_path
            }
            
            results.append(result)
        
        # Sort by absolute change (descending)
        results.sort(key=lambda x: abs(x['metric_change']), reverse=True)
        
        logger.info(f"Successfully compared {len(results)} videos for metric '{metric}'")
        return results
        
    except Exception as e:
        logger.error(f"Error comparing CSVs: {e}")
        raise

def compare_multiple_metrics(csv1_path: str, csv2_path: str, 
                           metrics: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compare multiple metrics between two CSV files.
    
    Args:
        csv1_path (str): Path to first CSV file
        csv2_path (str): Path to second CSV file
        metrics (List[str], optional): List of metrics to compare. 
                                     Defaults to common YouTube metrics.
        
    Returns:
        Dict[str, List[Dict]]: Dictionary with metric names as keys and comparison results as values
    """
    if metrics is None:
        metrics = ['views', 'impressions', 'CTR', 'averageViewDuration']
    
    results = {}
    
    for metric in metrics:
        try:
            comparison = compare_csvs(csv1_path, csv2_path, metric)
            if comparison:  # Only include if we have results
                results[metric] = comparison
                logger.info(f"Successfully compared {len(comparison)} videos for {metric}")
            else:
                logger.warning(f"No comparison results for metric: {metric}")
        except Exception as e:
            logger.error(f"Failed to compare metric {metric}: {e}")
            results[metric] = []
    
    return results

def get_top_changes(comparison_results: List[Dict[str, Any]], 
                   n: int = 5, 
                   change_type: str = 'absolute') -> List[Dict[str, Any]]:
    """
    Get top N videos with the biggest changes.
    
    Args:
        comparison_results (List[Dict]): Results from compare_csvs()
        n (int): Number of top results to return
        change_type (str): 'absolute', 'positive', 'negative', or 'percentage'
        
    Returns:
        List[Dict]: Top N videos with biggest changes
    """
    if not comparison_results:
        return []
    
    if change_type == 'absolute':
        # Sort by absolute change
        sorted_results = sorted(comparison_results, 
                              key=lambda x: abs(x['metric_change']), 
                              reverse=True)
    elif change_type == 'positive':
        # Sort by positive changes only
        positive_results = [r for r in comparison_results if r['metric_change'] > 0]
        sorted_results = sorted(positive_results, 
                              key=lambda x: x['metric_change'], 
                              reverse=True)
    elif change_type == 'negative':
        # Sort by negative changes only
        negative_results = [r for r in comparison_results if r['metric_change'] < 0]
        sorted_results = sorted(negative_results, 
                              key=lambda x: x['metric_change'])
    elif change_type == 'percentage':
        # Sort by percentage change
        sorted_results = sorted(comparison_results, 
                              key=lambda x: abs(x['metric_change_percent']), 
                              reverse=True)
    else:
        raise ValueError(f"Invalid change_type: {change_type}. Use 'absolute', 'positive', 'negative', or 'percentage'")
    
    return sorted_results[:n]

def generate_comparison_summary(comparison_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a statistical summary of comparison results.
    
    Args:
        comparison_results (List[Dict]): Results from compare_csvs()
        
    Returns:
        Dict: Summary statistics
    """
    if not comparison_results:
        return {
            'total_videos': 0,
            'metric': 'unknown',
            'summary': 'No comparison data available'
        }
    
    metric = comparison_results[0]['metric']
    changes = [r['metric_change'] for r in comparison_results]
    percent_changes = [r['metric_change_percent'] for r in comparison_results]
    
    positive_changes = [c for c in changes if c > 0]
    negative_changes = [c for c in changes if c < 0]
    
    summary = {
        'total_videos': len(comparison_results),
        'metric': metric,
        'total_change': sum(changes),
        'average_change': sum(changes) / len(changes),
        'average_percent_change': sum(percent_changes) / len(percent_changes),
        'videos_improved': len(positive_changes),
        'videos_declined': len(negative_changes),
        'videos_unchanged': len(changes) - len(positive_changes) - len(negative_changes),
        'biggest_increase': max(changes) if changes else 0,
        'biggest_decrease': min(changes) if changes else 0,
        'csv1_path': comparison_results[0]['csv1_path'],
        'csv2_path': comparison_results[0]['csv2_path']
    }
    
    return summary

def main():
    """
    Example usage of the multi-CSV comparison module.
    """
    # Example CSV paths (adjust as needed)
    csv1_path = "yt_analytics_may.csv"
    csv2_path = "yt_analytics_june.csv"
    
    print("YouTube Analytics CSV Comparison Tool")
    print("=" * 40)
    
    # Check if example files exist
    if not (os.path.exists(csv1_path) and os.path.exists(csv2_path)):
        print(f"Example CSV files not found:")
        print(f"- {csv1_path}")
        print(f"- {csv2_path}")
        print("\nPlease provide valid CSV file paths or run yt_fetch.py to generate data.")
        return
    
    try:
        # Compare views
        print(f"\nComparing 'views' between {csv1_path} and {csv2_path}")
        print("-" * 50)
        
        views_comparison = compare_csvs(csv1_path, csv2_path, 'views')
        
        if views_comparison:
            # Show top 5 biggest changes
            top_changes = get_top_changes(views_comparison, n=5, change_type='absolute')
            
            print("Top 5 Biggest View Changes:")
            for i, video in enumerate(top_changes, 1):
                change_sign = "+" if video['metric_change'] >= 0 else ""
                print(f"{i}. {video['videoTitle'][:50]}...")
                print(f"   Change: {change_sign}{video['metric_change']:,.0f} views ({video['metric_change_percent']:+.1f}%)")
                print(f"   Before: {video['value_csv1']:,.0f} → After: {video['value_csv2']:,.0f}")
                print()
            
            # Generate summary
            summary = generate_comparison_summary(views_comparison)
            print("Summary:")
            print(f"- Total videos compared: {summary['total_videos']}")
            print(f"- Videos improved: {summary['videos_improved']}")
            print(f"- Videos declined: {summary['videos_declined']}")
            print(f"- Average change: {summary['average_change']:+,.0f} views ({summary['average_percent_change']:+.1f}%)")
            print(f"- Biggest increase: {summary['biggest_increase']:+,.0f} views")
            print(f"- Biggest decrease: {summary['biggest_decrease']:+,.0f} views")
        else:
            print("No matching videos found for comparison.")
        
        # Compare multiple metrics
        print(f"\n" + "="*60)
        print("Multi-Metric Comparison")
        print("="*60)
        
        multi_comparison = compare_multiple_metrics(csv1_path, csv2_path)
        
        for metric, results in multi_comparison.items():
            if results:
                summary = generate_comparison_summary(results)
                print(f"\n{metric.upper()}:")
                print(f"  Average change: {summary['average_change']:+.2f} ({summary['average_percent_change']:+.1f}%)")
                print(f"  Improved: {summary['videos_improved']}, Declined: {summary['videos_declined']}")
        
    except Exception as e:
        print(f"Error during comparison: {e}")

if __name__ == "__main__":
    main()
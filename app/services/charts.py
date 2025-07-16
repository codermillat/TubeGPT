import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
from typing import Optional
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set matplotlib style for better-looking charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Create charts directory if it doesn't exist
CHARTS_DIR = Path("charts")
CHARTS_DIR.mkdir(exist_ok=True)

def _load_and_validate_csv(csv_path: str) -> pd.DataFrame:
    """
    Load and validate CSV file for chart generation.
    
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
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        raise ValueError(f"Failed to load CSV file: {e}")

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

def _save_chart(fig, filename: str) -> str:
    """
    Save matplotlib figure to charts directory.
    
    Args:
        fig: Matplotlib figure object
        filename (str): Filename for the chart
        
    Returns:
        str: Full path to saved chart
    """
    # Add timestamp to filename to avoid conflicts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_with_timestamp = f"{filename}_{timestamp}.png"
    filepath = CHARTS_DIR / filename_with_timestamp
    
    try:
        fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        logger.info(f"Chart saved to: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error saving chart: {e}")
        raise
    finally:
        plt.close(fig)

def plot_ctr_trend(csv_path: str) -> str:
    """
    Create a line graph showing CTR trend over time.
    
    Args:
        csv_path (str): Path to YouTube analytics CSV file
        
    Returns:
        str: Path to saved PNG file
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing
    """
    try:
        df = _load_and_validate_csv(csv_path)
        
        # Validate required columns
        required_columns = ['date', 'CTR']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Prepare data
        df = _ensure_numeric_column(df, 'CTR')
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date', 'CTR'])
        
        if len(df) == 0:
            raise ValueError("No valid data points for CTR trend")
        
        # Sort by date
        df = df.sort_values('date')
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Convert CTR to percentage for better readability
        df['CTR_percent'] = df['CTR'] * 100
        
        # Plot line with markers
        ax.plot(df['date'], df['CTR_percent'], 
               marker='o', linewidth=2, markersize=6, 
               color='#1f77b4', alpha=0.8)
        
        # Customize the plot
        ax.set_title('Click-Through Rate (CTR) Trend Over Time', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('CTR (%)', fontsize=12)
        
        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1f}%'))
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add average line
        avg_ctr = df['CTR_percent'].mean()
        ax.axhline(y=avg_ctr, color='red', linestyle='--', alpha=0.7, 
                  label=f'Average: {avg_ctr:.2f}%')
        ax.legend()
        
        # Add some statistics as text
        max_ctr = df['CTR_percent'].max()
        min_ctr = df['CTR_percent'].min()
        ax.text(0.02, 0.98, f'Max: {max_ctr:.2f}%\nMin: {min_ctr:.2f}%', 
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        return _save_chart(fig, 'ctr_trend')
        
    except Exception as e:
        logger.error(f"Error creating CTR trend chart: {e}")
        raise

def plot_views_by_country(csv_path: str) -> str:
    """
    Create a bar chart showing total views by country.
    
    Args:
        csv_path (str): Path to YouTube analytics CSV file
        
    Returns:
        str: Path to saved PNG file
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing
    """
    try:
        df = _load_and_validate_csv(csv_path)
        
        # Validate required columns
        required_columns = ['country', 'views']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Prepare data
        df = _ensure_numeric_column(df, 'views')
        df = df.dropna(subset=['country', 'views'])
        
        if len(df) == 0:
            raise ValueError("No valid data points for views by country")
        
        # Group by country and sum views
        country_views = df.groupby('country')['views'].sum().sort_values(ascending=False)
        
        # Take top 10 countries to avoid overcrowding
        top_countries = country_views.head(10)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create bar chart
        bars = ax.bar(range(len(top_countries)), top_countries.values, 
                     color=sns.color_palette("viridis", len(top_countries)))
        
        # Customize the plot
        ax.set_title('Total Views by Country (Top 10)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Country', fontsize=12)
        ax.set_ylabel('Total Views', fontsize=12)
        
        # Set x-axis labels
        ax.set_xticks(range(len(top_countries)))
        ax.set_xticklabels(top_countries.index, rotation=45, ha='right')
        
        # Format y-axis with commas for large numbers
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        # Add value labels on top of bars
        for i, (bar, value) in enumerate(zip(bars, top_countries.values)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01,
                   f'{value:,.0f}', ha='center', va='bottom', fontsize=10)
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add total views info
        total_views = country_views.sum()
        ax.text(0.02, 0.98, f'Total Views: {total_views:,.0f}\nCountries: {len(country_views)}', 
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        return _save_chart(fig, 'views_by_country')
        
    except Exception as e:
        logger.error(f"Error creating views by country chart: {e}")
        raise

def plot_avg_duration_distribution(csv_path: str) -> str:
    """
    Create a histogram showing distribution of average view duration.
    
    Args:
        csv_path (str): Path to YouTube analytics CSV file
        
    Returns:
        str: Path to saved PNG file
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing
    """
    try:
        df = _load_and_validate_csv(csv_path)
        
        # Validate required columns
        required_columns = ['averageViewDuration']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Prepare data
        df = _ensure_numeric_column(df, 'averageViewDuration')
        df = df.dropna(subset=['averageViewDuration'])
        
        # Remove outliers (values beyond 3 standard deviations)
        mean_duration = df['averageViewDuration'].mean()
        std_duration = df['averageViewDuration'].std()
        df_filtered = df[
            (df['averageViewDuration'] >= mean_duration - 3*std_duration) & 
            (df['averageViewDuration'] <= mean_duration + 3*std_duration)
        ]
        
        if len(df_filtered) == 0:
            raise ValueError("No valid data points for average view duration")
        
        # Convert seconds to minutes for better readability
        duration_minutes = df_filtered['averageViewDuration'] / 60
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create histogram
        n_bins = min(20, len(df_filtered) // 2)  # Adaptive number of bins
        n, bins, patches = ax.hist(duration_minutes, bins=n_bins, 
                                  color='skyblue', alpha=0.7, edgecolor='black')
        
        # Color bars based on frequency (gradient effect)
        fracs = n / n.max()
        norm = plt.Normalize(fracs.min(), fracs.max())
        for frac, patch in zip(fracs, patches):
            color = plt.cm.viridis(norm(frac))
            patch.set_facecolor(color)
        
        # Customize the plot
        ax.set_title('Distribution of Average View Duration', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Average View Duration (minutes)', fontsize=12)
        ax.set_ylabel('Number of Videos', fontsize=12)
        
        # Add vertical lines for mean and median
        mean_minutes = duration_minutes.mean()
        median_minutes = duration_minutes.median()
        
        ax.axvline(mean_minutes, color='red', linestyle='--', linewidth=2, 
                  label=f'Mean: {mean_minutes:.1f} min')
        ax.axvline(median_minutes, color='orange', linestyle='--', linewidth=2, 
                  label=f'Median: {median_minutes:.1f} min')
        
        # Add legend
        ax.legend()
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3)
        
        # Add statistics box
        stats_text = f'''Statistics:
Mean: {mean_minutes:.1f} min
Median: {median_minutes:.1f} min
Std Dev: {duration_minutes.std():.1f} min
Videos: {len(df_filtered)}'''
        
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        return _save_chart(fig, 'avg_duration_distribution')
        
    except Exception as e:
        logger.error(f"Error creating average duration distribution chart: {e}")
        raise

def generate_all_charts(csv_path: str) -> dict:
    """
    Generate all available charts for the given CSV file.
    
    Args:
        csv_path (str): Path to YouTube analytics CSV file
        
    Returns:
        dict: Dictionary with chart names as keys and file paths as values
    """
    charts = {}
    chart_functions = {
        'ctr_trend': plot_ctr_trend,
        'views_by_country': plot_views_by_country,
        'avg_duration_distribution': plot_avg_duration_distribution
    }
    
    for chart_name, chart_function in chart_functions.items():
        try:
            chart_path = chart_function(csv_path)
            charts[chart_name] = chart_path
            logger.info(f"Successfully generated {chart_name} chart")
        except Exception as e:
            logger.error(f"Failed to generate {chart_name} chart: {e}")
            charts[chart_name] = None
    
    return charts

def main():
    """
    Example usage of the charts module.
    """
    csv_path = "yt_analytics.csv"
    
    if not os.path.exists(csv_path):
        print(f"CSV file '{csv_path}' not found. Please run yt_fetch.py first.")
        return
    
    print("Generating YouTube Analytics Charts...")
    print("=" * 40)
    
    try:
        # Generate all charts
        charts = generate_all_charts(csv_path)
        
        print("\nGenerated Charts:")
        for chart_name, chart_path in charts.items():
            if chart_path:
                print(f"✓ {chart_name}: {chart_path}")
            else:
                print(f"✗ {chart_name}: Failed to generate")
        
        print(f"\nAll charts saved in: {CHARTS_DIR}")
        
    except Exception as e:
        print(f"Error generating charts: {e}")

if __name__ == "__main__":
    main()
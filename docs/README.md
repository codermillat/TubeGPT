# YouTube Analytics Fetcher

A Python module for fetching YouTube channel analytics data using the YouTube Data API v3 and YouTube Analytics API. Authenticates via OAuth2 and exports data to CSV format.

## Features

- OAuth2 authentication with YouTube APIs
- Fetches video metadata (ID, title, publication date, views)
- Retrieves analytics data (impressions, CTR, average view duration)
- Aggregates data by country (shows top country per video)
- Exports to CSV format with timestamped backups
- Designed for daily/weekly scheduled runs
- Comprehensive error handling and logging

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Google Cloud credentials (see [setup_guide.md](setup_guide.md))

3. Run the fetcher:
   ```bash
   python yt_fetch.py
   ```

## Usage

### Basic Usage

```python
from yt_fetch import YouTubeAnalyticsFetcher

fetcher = YouTubeAnalyticsFetcher()
fetcher.authenticate()
fetcher.fetch_and_save_data(days_back=30, max_results=50)
```

### Scheduled Runs

For daily runs:
```bash
python run_daily.py
```

For weekly runs:
```bash
python run_weekly.py
```

## Output

The script generates `yt_analytics.csv` with the following columns:
- videoId
- videoTitle
- date
- views
- impressions
- CTR
- averageViewDuration
- country

## Configuration

Edit `config.py` or modify parameters in the script calls:

```python
fetcher.fetch_and_save_data(
    days_back=7,                    # Number of days to look back
    max_results=100,                # Maximum videos to process
    output_file='custom_output.csv' # Custom output filename
)
```

## Requirements

- Python 3.7+
- Google Cloud project with YouTube APIs enabled
- OAuth 2.0 credentials for desktop application
- YouTube channel with analytics access
- Gemini API key for AI analysis (optional)

## AI Analysis with Gemini

The `gemini_chat.py` module provides AI-powered analysis of your YouTube data:

```python
from gemini_chat import GeminiYouTubeAnalyzer

analyzer = GeminiYouTubeAnalyzer()
response = analyzer.analyze_youtube_data(
    "What are my best performing videos?", 
    "yt_analytics.csv"
)
print(response)
```

### Setup for Gemini Analysis

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set environment variable: `export GEMINI_API_KEY=your_key_here`
3. Run: `python gemini_chat.py` for interactive analysis

## License

MIT License - see LICENSE file for details.

## FastAPI Chat API

The `chat_api.py` module provides a REST API for analyzing YouTube data:

### Running the API

```bash
python main.py
```

Or directly with uvicorn:
```bash
uvicorn chat_api:app --reload
```

### CLI Usage

You can also use the tool from command line:

```bash
# Analyze with automatic CSV detection
python main.py --message "What are my best performing videos?"

# Use specific CSV file
python main.py --message "How can I improve my CTR?" --csv-path custom_analytics.csv

# Run server on custom port
python main.py --port 9000

# Enable debug mode
python main.py --debug
```

### API Endpoints

- `POST /chat`: Analyze YouTube data with AI
- `GET /`: Health check
- `GET /health`: Detailed health status

### Example Usage

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What are my best performing videos?",
       "csv_path": "yt_analytics.csv"
     }'
```

VERY IMPORTANT: NEVER skip RLS setup for any table. Security is non-negotiable!

## Data Visualization

The `charts.py` module provides data visualization capabilities:

### Available Charts

- **CTR Trend**: Line graph showing click-through rate over time
- **Views by Country**: Bar chart of total views by geographic location
- **Duration Distribution**: Histogram of average view duration

### Usage

```python
from charts import plot_ctr_trend, plot_views_by_country, plot_avg_duration_distribution

# Generate individual charts
ctr_chart = plot_ctr_trend("yt_analytics.csv")
country_chart = plot_views_by_country("yt_analytics.csv")
duration_chart = plot_avg_duration_distribution("yt_analytics.csv")

# Generate all charts at once
from charts import generate_all_charts
all_charts = generate_all_charts("yt_analytics.csv")
```

### AI Integration

Charts are automatically generated when users ask for visualizations:

```python
# These queries will trigger chart generation
analyzer.analyze_youtube_data("show me a graph of my CTR trend", "yt_analytics.csv")
analyzer.analyze_youtube_data("plot my views by country", "yt_analytics.csv")
analyzer.analyze_youtube_data("visualize duration distribution", "yt_analytics.csv")
```

Charts are saved in the `charts/` directory with timestamps to avoid conflicts.

## Multi-CSV Comparison

The `multi_csv.py` module enables comparison between different time periods:

### Core Functions

```python
from multi_csv import compare_csvs, compare_multiple_metrics

# Compare specific metric between two CSV files
results = compare_csvs("may_analytics.csv", "june_analytics.csv", "views")

# Compare multiple metrics at once
multi_results = compare_multiple_metrics("old_data.csv", "new_data.csv")
```

### Comparison Features

- **Video Matching**: Automatically matches videos by ID or title
- **Change Calculation**: Computes absolute and percentage changes
- **Top Performers**: Identifies biggest improvements and declines
- **Statistical Summary**: Provides overview of performance changes
- **Multi-Metric Support**: Compare views, CTR, duration, impressions simultaneously

### AI Integration

The Gemini analyzer automatically detects comparison requests:

```python
# These queries trigger comparison analysis
analyzer.analyze_youtube_data("How did views change between May and June?", "may.csv", "june.csv")
analyzer.analyze_youtube_data("Compare my CTR performance over time", "old.csv")
```

### Usage Examples

```bash
# CLI comparison
python main.py --message "Compare performance between Eid and Ramadan videos"

# API comparison
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "How did my videos perform compared to last month?",
       "csv_path": "current_month.csv"
     }'
```

The system intelligently detects time periods mentioned in questions and attempts to find corresponding CSV files for automatic comparison.

The system remembers the context and provides relevant, connected responses!

## Gap Detection and Competitor Analysis

The `gap_detector.py` module provides comprehensive competitor analysis to identify content opportunities:

### Core Functions

```python
from gap_detector import GapDetector, detect_content_gaps_from_query

# Initialize detector
detector = GapDetector()

# Compare with competitors
results = detector.compare_with_competitors(
    "yt_analytics.csv", 
    ["competitor_a.csv", "competitor_b.csv"]
)

# Generate human-readable summary
summary = detector.summarize_gap_results(results)
print(summary)
```

### Gap Analysis Features

- **Missing Topics**: Content areas competitors cover but you don't
- **Frequency Gaps**: Topics where competitors produce more content
- **Engagement Opportunities**: Areas where competitors get better engagement
- **Your Strengths**: Topics where you outperform competitors
- **Actionable Recommendations**: Specific next steps for content strategy

### AI Integration

The Gemini analyzer automatically detects gap analysis requests:

```python
# These queries trigger automatic gap analysis
analyzer.analyze_youtube_data("What content am I missing?", "yt_analytics.csv")
analyzer.analyze_youtube_data("What should I create next?", "yt_analytics.csv")
analyzer.analyze_youtube_data("What opportunities do I have?", "yt_analytics.csv")
```

### Usage Examples

```bash
# CLI gap analysis
python main.py --message "What am I missing compared to competitors?"

# API gap analysis
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What content gaps should I fill?",
       "csv_path": "yt_analytics.csv"
     }'
```

The system automatically finds competitor CSV files (named like `competitor_*.csv`, `comp_*.csv`) and provides detailed analysis with specific recommendations for content strategy improvement.

## Competitor Data Collection

The `competitor_scraper.py` module provides automated competitor data collection:

### Core Functions

```python
from competitor_scraper import CompetitorScraper, fetch_multiple_competitors

# Initialize scraper
scraper = CompetitorScraper()  # Uses YOUTUBE_API_KEY env var

# Fetch single competitor
videos = scraper.fetch_competitor_videos("@MrBeast", max_videos=20)

# Save to CSV for gap analysis
csv_path = scraper.save_competitor_data("@PewDiePie", max_videos=50)

# Process multiple competitors
competitors = ["@channel1", "@channel2", "@channel3"]
results = fetch_multiple_competitors(competitors, max_videos=30)
```

### Features

- **Multiple Input Formats**: Channel URLs, handles (@username), or channel IDs
- **YouTube Data API Integration**: Uses official API for reliable data
- **Rate Limiting**: Respects API quotas and implements proper delays
- **Gap Detector Compatible**: Outputs CSV in the exact format needed for analysis
- **Batch Processing**: Handle multiple competitors efficiently
- **Error Handling**: Graceful failure handling with detailed logging

### Setup

1. Get a YouTube Data API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3 for your project
3. Set environment variable: `export YOUTUBE_API_KEY=your_key_here`
4. Run: `python competitor_scraper.py` for examples

### Usage Examples

```bash
# Scrape competitor data
python competitor_scraper.py

# Use in gap analysis workflow
python competitor_scraper.py  # Generate competitor CSVs
python main.py --message "What content gaps do I have?"  # Analyze gaps
```

The scraper automatically saves data to `data/competitors/` directory in a format compatible with the gap detector, enabling seamless competitive analysis workflow.

## Prompt Templates with Few-Shot Examples

The `prompt_templates.py` module provides contextual prompts with few-shot examples:

### Categories:
- **CTR Analysis**: Low CTR diagnosis and improvement suggestions
- **Title Optimization**: Title suggestions and best practices
- **Performance Trends**: Growth analysis and trend identification
- **Audience Insights**: Demographic and behavioral analysis

### Features:
- **Bilingual Support**: English and Bengali examples
- **Contextual Selection**: Automatically chooses relevant examples based on question
- **Reusable Templates**: Structured system for consistent responses
- **Data Integration**: Incorporates actual channel data into examples

### Usage:

```python
from prompt_templates import get_contextual_prompt

# Get contextual prompt with examples
prompt = get_contextual_prompt(
    user_question="Why is my CTR dropping?",
    language='en',
    data_summary="Channel stats and performance data"
)
```

The system automatically detects question categories and provides relevant few-shot examples to improve AI response quality and consistency.
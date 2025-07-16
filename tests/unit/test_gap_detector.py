"""
Unit tests for gap_detector.py module.

Tests gap detection functionality with mocked CSV data
and validates competitor analysis results.
"""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the module to test
from gap_detector import (
    GapDetector,
    detect_content_gaps_from_query
)

# Mock CSV data for testing
SAMPLE_YOUR_DATA = [
    {
        'videoId': 'abc123',
        'videoTitle': 'How to Cook Perfect Rice - Tutorial',
        'views': 45000,
        'CTR': 0.045,
        'averageViewDuration': 156.5
    },
    {
        'videoId': 'def456',
        'videoTitle': 'Bengali Cooking Tips for Beginners',
        'views': 32000,
        'CTR': 0.032,
        'averageViewDuration': 142.3
    },
    {
        'videoId': 'ghi789',
        'videoTitle': 'Travel Vlog: Cox\'s Bazar Adventure',
        'views': 67000,
        'CTR': 0.058,
        'averageViewDuration': 203.4
    }
]

SAMPLE_COMPETITOR_A_DATA = [
    {
        'videoId': 'comp_a_1',
        'videoTitle': 'Ultimate Visa Interview Tips and Tricks',
        'views': 89000,
        'CTR': 0.062,
        'averageViewDuration': 245.8
    },
    {
        'videoId': 'comp_a_2',
        'videoTitle': 'Visa Interview Questions You Must Know',
        'views': 76000,
        'CTR': 0.055,
        'averageViewDuration': 198.2
    },
    {
        'videoId': 'comp_a_3',
        'videoTitle': 'How to Cook Biryani - Step by Step Guide',
        'views': 54000,
        'CTR': 0.041,
        'averageViewDuration': 167.9
    },
    {
        'videoId': 'comp_a_4',
        'videoTitle': 'Travel Guide: Best Places in Thailand',
        'views': 43000,
        'CTR': 0.038,
        'averageViewDuration': 189.1
    }
]

SAMPLE_COMPETITOR_B_DATA = [
    {
        'videoId': 'comp_b_1',
        'videoTitle': 'Visa Application Process - Complete Guide',
        'views': 65000,
        'CTR': 0.048,
        'averageViewDuration': 178.5
    },
    {
        'videoId': 'comp_b_2',
        'videoTitle': 'Tech Review: Latest Smartphone Comparison',
        'views': 91000,
        'CTR': 0.067,
        'averageViewDuration': 234.7
    },
    {
        'videoId': 'comp_b_3',
        'videoTitle': 'Cooking Hacks Every Student Should Know',
        'views': 38000,
        'CTR': 0.035,
        'averageViewDuration': 145.3
    }
]

class TestGapDetector:
    """Test suite for GapDetector class."""
    
    @pytest.fixture
    def gap_detector(self):
        """Create GapDetector instance for testing."""
        return GapDetector()
    
    @pytest.fixture
    def temp_csv_files(self):
        """Create temporary CSV files for testing."""
        temp_files = {}
        
        # Create your CSV
        your_df = pd.DataFrame(SAMPLE_YOUR_DATA)
        your_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        your_df.to_csv(your_file.name, index=False)
        temp_files['your_csv'] = your_file.name
        
        # Create competitor A CSV
        comp_a_df = pd.DataFrame(SAMPLE_COMPETITOR_A_DATA)
        comp_a_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        comp_a_df.to_csv(comp_a_file.name, index=False)
        temp_files['comp_a_csv'] = comp_a_file.name
        
        # Create competitor B CSV
        comp_b_df = pd.DataFrame(SAMPLE_COMPETITOR_B_DATA)
        comp_b_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        comp_b_df.to_csv(comp_b_file.name, index=False)
        temp_files['comp_b_csv'] = comp_b_file.name
        
        yield temp_files
        
        # Cleanup
        for file_path in temp_files.values():
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    @pytest.fixture
    def malformed_csv(self):
        """Create malformed CSV for error testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write("invalid,csv,data\nno,proper,headers\n")
        temp_file.close()
        
        yield temp_file.name
        
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_gap_detector_initialization(self, gap_detector):
        """Test GapDetector initialization."""
        assert gap_detector is not None
        assert 'tutorial' in gap_detector.topic_keywords
        assert 'cooking' in gap_detector.topic_keywords
        assert isinstance(gap_detector.topic_keywords['tutorial'], list)
    
    def test_load_and_validate_csv_success(self, gap_detector, temp_csv_files):
        """Test successful CSV loading and validation."""
        df = gap_detector._load_and_validate_csv(temp_csv_files['your_csv'], "Test CSV")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'videoTitle' in df.columns
        assert 'videoId' in df.columns
        assert 'views' in df.columns
        
        # Check data types
        assert df['views'].dtype in ['int64', 'float64']
        assert df['CTR'].dtype in ['float64']
    
    def test_load_and_validate_csv_missing_file(self, gap_detector):
        """Test CSV loading with missing file."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            gap_detector._load_and_validate_csv("nonexistent.csv", "Missing CSV")
    
    def test_load_and_validate_csv_malformed(self, gap_detector, malformed_csv):
        """Test CSV loading with malformed data."""
        with pytest.raises(ValueError, match="Missing required columns"):
            gap_detector._load_and_validate_csv(malformed_csv, "Malformed CSV")
    
    def test_extract_topics(self, gap_detector):
        """Test topic extraction from video titles."""
        titles = [
            "How to Cook Perfect Rice - Tutorial",
            "Bengali Cooking Tips for Beginners",
            "Tech Review: Latest Smartphone",
            "Travel Vlog: Cox's Bazar Adventure",
            "Visa Interview Tips and Tricks"
        ]
        
        topics = gap_detector._extract_topics(titles)
        
        # Check that topics were extracted
        assert 'tutorial' in topics
        assert 'cooking' in topics
        assert 'tech' in topics
        assert 'travel' in topics
        
        # Check specific matches
        assert "How to Cook Perfect Rice - Tutorial" in topics['tutorial']
        assert "Bengali Cooking Tips for Beginners" in topics['cooking']
        assert "Tech Review: Latest Smartphone" in topics['tech']
        
        # Check specific keyword extraction
        specific_topics = [key for key in topics.keys() if '_specific' in key]
        assert len(specific_topics) > 0  # Should find some specific patterns
    
    def test_calculate_engagement_score(self, gap_detector):
        """Test engagement score calculation."""
        # Test with good metrics
        good_row = pd.Series({
            'views': 50000,
            'CTR': 0.05,
            'averageViewDuration': 180
        })
        
        score = gap_detector._calculate_engagement_score(good_row)
        assert 0 <= score <= 100
        assert score > 0
        
        # Test with poor metrics
        poor_row = pd.Series({
            'views': 100,
            'CTR': 0.001,
            'averageViewDuration': 30
        })
        
        poor_score = gap_detector._calculate_engagement_score(poor_row)
        assert poor_score < score
        
        # Test with missing data
        empty_row = pd.Series({})
        empty_score = gap_detector._calculate_engagement_score(empty_row)
        assert empty_score == 0.0
    
    def test_compare_with_competitors_success(self, gap_detector, temp_csv_files):
        """Test successful competitor comparison."""
        competitor_paths = [temp_csv_files['comp_a_csv'], temp_csv_files['comp_b_csv']]
        
        results = gap_detector.compare_with_competitors(
            temp_csv_files['your_csv'],
            competitor_paths
        )
        
        # Validate result structure
        assert isinstance(results, dict)
        required_keys = [
            'missing_topics', 'underperforming_topics', 'overperforming_topics',
            'frequency_gaps', 'engagement_opportunities', 'summary_stats'
        ]
        
        for key in required_keys:
            assert key in results
        
        # Check summary stats
        stats = results['summary_stats']
        assert stats['your_total_videos'] == 3
        assert stats['competitor_total_videos'] == 7  # 4 + 3
        assert stats['your_unique_topics'] > 0
        
        # Should find missing topics (visa content)
        assert len(results['missing_topics']) > 0
        
        # Check missing topics structure
        if results['missing_topics']:
            missing_topic = results['missing_topics'][0]
            assert 'topic' in missing_topic
            assert 'competitor_videos' in missing_topic
            assert 'your_videos' in missing_topic
            assert 'opportunity_score' in missing_topic
            assert 'sample_titles' in missing_topic
    
    def test_compare_with_competitors_no_competitors(self, gap_detector, temp_csv_files):
        """Test competitor comparison with no valid competitor files."""
        with pytest.raises(ValueError, match="No valid competitor data loaded"):
            gap_detector.compare_with_competitors(
                temp_csv_files['your_csv'],
                ["nonexistent1.csv", "nonexistent2.csv"]
            )
    
    def test_compare_with_competitors_missing_your_file(self, gap_detector, temp_csv_files):
        """Test competitor comparison with missing your file."""
        with pytest.raises(FileNotFoundError):
            gap_detector.compare_with_competitors(
                "nonexistent_your.csv",
                [temp_csv_files['comp_a_csv']]
            )
    
    def test_summarize_gap_results(self, gap_detector, temp_csv_files):
        """Test gap results summarization."""
        competitor_paths = [temp_csv_files['comp_a_csv'], temp_csv_files['comp_b_csv']]
        
        results = gap_detector.compare_with_competitors(
            temp_csv_files['your_csv'],
            competitor_paths
        )
        
        summary = gap_detector.summarize_gap_results(results)
        
        assert isinstance(summary, str)
        assert len(summary) > 100  # Should be substantial
        assert "CONTENT GAP ANALYSIS RESULTS" in summary
        assert "MISSING OPPORTUNITIES" in summary or "FREQUENCY GAPS" in summary
        assert "RECOMMENDATIONS" in summary
        
        # Should mention specific numbers
        assert "videos" in summary.lower()
        assert "competitors" in summary.lower()
    
    def test_summarize_gap_results_empty_data(self, gap_detector):
        """Test summarization with empty gap data."""
        empty_data = {
            'missing_topics': [],
            'underperforming_topics': [],
            'overperforming_topics': [],
            'frequency_gaps': [],
            'engagement_opportunities': [],
            'summary_stats': {
                'your_total_videos': 0,
                'your_unique_topics': 0,
                'competitor_total_videos': 0,
                'competitor_unique_topics': 0,
                'missing_topic_count': 0,
                'frequency_gap_count': 0
            },
            'recommendations': []
        }
        
        summary = gap_detector.summarize_gap_results(empty_data)
        
        assert isinstance(summary, str)
        assert "CONTENT GAP ANALYSIS RESULTS" in summary
        assert "0 videos" in summary
    
    def test_summarize_gap_results_error_handling(self, gap_detector):
        """Test summarization error handling."""
        invalid_data = {"invalid": "structure"}
        
        summary = gap_detector.summarize_gap_results(invalid_data)
        
        assert isinstance(summary, str)
        assert "Error generating summary" in summary


class TestDetectContentGapsFromQuery:
    """Test the query-based gap detection function."""
    
    @pytest.fixture
    def temp_csv_files(self):
        """Create temporary CSV files for testing."""
        temp_files = {}
        
        # Create your CSV
        your_df = pd.DataFrame(SAMPLE_YOUR_DATA)
        your_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        your_df.to_csv(your_file.name, index=False)
        temp_files['your_csv'] = your_file.name
        
        # Create competitor CSV
        comp_df = pd.DataFrame(SAMPLE_COMPETITOR_A_DATA)
        comp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        comp_df.to_csv(comp_file.name, index=False)
        temp_files['comp_csv'] = comp_file.name
        
        yield temp_files
        
        # Cleanup
        for file_path in temp_files.values():
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_detect_content_gaps_missing_query(self, temp_csv_files):
        """Test gap detection with 'missing' query."""
        result = detect_content_gaps_from_query(
            "What content am I missing?",
            temp_csv_files['your_csv'],
            [temp_csv_files['comp_csv']]
        )
        
        assert isinstance(result, str)
        assert len(result) > 100
        assert "missing content" in result.lower()
        assert "competitors are covering" in result.lower()
    
    def test_detect_content_gaps_opportunity_query(self, temp_csv_files):
        """Test gap detection with 'opportunity' query."""
        result = detect_content_gaps_from_query(
            "What are my biggest content opportunities?",
            temp_csv_files['your_csv'],
            [temp_csv_files['comp_csv']]
        )
        
        assert isinstance(result, str)
        assert "content opportunities" in result.lower()
        assert "competitor analysis" in result.lower()
    
    def test_detect_content_gaps_no_competitors(self, temp_csv_files):
        """Test gap detection with no competitor data."""
        result = detect_content_gaps_from_query(
            "What am I missing?",
            temp_csv_files['your_csv'],
            []
        )
        
        assert isinstance(result, str)
        assert "No competitor data available" in result
    
    def test_detect_content_gaps_error_handling(self):
        """Test gap detection error handling."""
        result = detect_content_gaps_from_query(
            "What am I missing?",
            "nonexistent.csv",
            ["also_nonexistent.csv"]
        )
        
        assert isinstance(result, str)
        assert "error" in result.lower()


class TestIntegration:
    """Integration tests for gap detection workflow."""
    
    def test_full_gap_analysis_workflow(self):
        """Test complete gap analysis workflow with realistic data."""
        # Create realistic test data
        your_data = [
            {'videoId': '1', 'videoTitle': 'Cooking Rice Tutorial', 'views': 1000, 'CTR': 0.03, 'averageViewDuration': 120},
            {'videoId': '2', 'videoTitle': 'Travel Vlog Bangladesh', 'views': 2000, 'CTR': 0.04, 'averageViewDuration': 180},
        ]
        
        competitor_data = [
            {'videoId': 'c1', 'videoTitle': 'Visa Interview Tips', 'views': 5000, 'CTR': 0.06, 'averageViewDuration': 200},
            {'videoId': 'c2', 'videoTitle': 'Study Abroad Guide', 'views': 4000, 'CTR': 0.05, 'averageViewDuration': 190},
            {'videoId': 'c3', 'videoTitle': 'Cooking Pasta Tutorial', 'views': 3000, 'CTR': 0.04, 'averageViewDuration': 150},
        ]
        
        # Create temporary files
        your_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        comp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        try:
            pd.DataFrame(your_data).to_csv(your_file.name, index=False)
            pd.DataFrame(competitor_data).to_csv(comp_file.name, index=False)
            
            # Run analysis
            detector = GapDetector()
            results = detector.compare_with_competitors(your_file.name, [comp_file.name])
            summary = detector.summarize_gap_results(results)
            
            # Validate results
            assert len(results['missing_topics']) > 0  # Should find visa/study topics
            assert isinstance(summary, str)
            assert len(summary) > 200
            
            # Test query-based detection
            query_result = detect_content_gaps_from_query(
                "What should I create next?",
                your_file.name,
                [comp_file.name]
            )
            
            assert isinstance(query_result, str)
            assert "opportunities" in query_result.lower()
            
        finally:
            # Cleanup
            os.unlink(your_file.name)
            os.unlink(comp_file.name)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
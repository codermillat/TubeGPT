"""
Test suite for CSV validator security features.
"""

import pytest
import tempfile
import os
import pandas as pd
from pathlib import Path

from app.utils.csv_validator import CSVValidator, CSVValidationError


class TestCSVValidatorSecurity:
    """Test CSV validator security functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = CSVValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_csv(self, data, filename="test.csv"):
        """Helper to create test CSV files."""
        file_path = os.path.join(self.temp_dir, filename)
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        return file_path
    
    def test_formula_injection_detection(self):
        """Test detection of Excel formula injection attempts."""
        # Create CSV with formula injection attempts
        malicious_data = {
            'videoId': ['vid1', 'vid2', 'vid3'],
            'videoTitle': [
                'Normal Title',
                '=SUM(A1:A10)',  # Excel formula
                '+cmd|"/c calc"!A0'  # Command injection via Excel
            ],
            'views': [1000, 2000, 3000]
        }
        
        file_path = self.create_test_csv(malicious_data)
        
        # Should detect formula injection
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "injection" in str(exc_info.value).lower()
    
    def test_script_injection_detection(self):
        """Test detection of script injection in CSV cells."""
        malicious_data = {
            'videoId': ['vid1', 'vid2'],
            'videoTitle': [
                'Normal Title',
                '<script>alert("xss")</script>'
            ],
            'views': [1000, 2000]
        }
        
        file_path = self.create_test_csv(malicious_data)
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "injection" in str(exc_info.value).lower()
    
    def test_javascript_url_detection(self):
        """Test detection of JavaScript URL injection."""
        malicious_data = {
            'videoId': ['vid1', 'vid2'],
            'videoTitle': [
                'Normal Title',
                'javascript:alert(1)'
            ],
            'views': [1000, 2000]
        }
        
        file_path = self.create_test_csv(malicious_data)
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "injection" in str(exc_info.value).lower()
    
    def test_at_symbol_formula_detection(self):
        """Test detection of @ symbol formulas."""
        malicious_data = {
            'videoId': ['vid1', 'vid2'],
            'videoTitle': [
                'Normal Title',
                '@SUM(1+1)*cmd|"/c calc"!A0'
            ],
            'views': [1000, 2000]
        }
        
        file_path = self.create_test_csv(malicious_data)
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "injection" in str(exc_info.value).lower()
    
    def test_safe_negative_numbers_allowed(self):
        """Test that safe negative numbers are allowed."""
        safe_data = {
            'videoId': ['vid1', 'vid2', 'vid3'],
            'videoTitle': ['Title 1', 'Title 2', 'Title 3'],
            'views': [1000, -500, 3000]  # Negative numbers should be OK
        }
        
        file_path = self.create_test_csv(safe_data)
        
        # Should not raise an exception
        result = self.validator.validate_csv_file(file_path, 'youtube_analytics')
        assert result['row_count'] == 3
    
    def test_file_size_limit(self):
        """Test file size validation."""
        # Create a large CSV that exceeds size limit
        large_data = {
            'videoId': [f'vid_{i}' for i in range(10000)],
            'videoTitle': [f'Very long title with lots of text to make it big' * 100 for i in range(10000)],
            'views': list(range(10000))
        }
        
        file_path = self.create_test_csv(large_data, 'large.csv')
        
        # Should detect file too large
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "too large" in str(exc_info.value).lower()
    
    def test_row_limit(self):
        """Test row count validation."""
        # Create CSV with too many rows
        many_rows_data = {
            'videoId': [f'vid_{i}' for i in range(150000)],  # Exceeds max_rows
            'videoTitle': [f'Title {i}' for i in range(150000)],
            'views': list(range(150000))
        }
        
        file_path = self.create_test_csv(many_rows_data, 'many_rows.csv')
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "too many rows" in str(exc_info.value).lower()
    
    def test_cell_length_limit(self):
        """Test individual cell length validation."""
        # Create CSV with very long cell content
        long_cell_data = {
            'videoId': ['vid1'],
            'videoTitle': ['X' * 15000],  # Exceeds max_cell_length
            'views': [1000]
        }
        
        file_path = self.create_test_csv(long_cell_data)
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "too long" in str(exc_info.value).lower()
    
    def test_empty_file_detection(self):
        """Test detection of empty files."""
        empty_file = os.path.join(self.temp_dir, 'empty.csv')
        Path(empty_file).touch()  # Create empty file
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(empty_file, 'youtube_analytics')
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_invalid_column_names(self):
        """Test validation of column names."""
        invalid_data = {
            '<script>alert(1)</script>': ['val1'],  # Malicious column name
            'normal_column': ['val2'],
            '': ['val3']  # Empty column name
        }
        
        file_path = self.create_test_csv(invalid_data)
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "column" in str(exc_info.value).lower()
    
    def test_safe_csv_validation(self):
        """Test that safe CSV files pass validation."""
        safe_data = {
            'videoId': ['abc123', 'def456', 'ghi789'],
            'videoTitle': [
                'How to Cook Pasta',
                'Best Travel Destinations 2024',
                'Tech Review: Latest Smartphone'
            ],
            'views': [15000, 8500, 32000],
            'likes': [150, 85, 320],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03']
        }
        
        file_path = self.create_test_csv(safe_data)
        
        # Should pass validation without exceptions
        result = self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert result['row_count'] == 3
        assert result['column_count'] == 5
        assert 'videoId' in result['columns']
        assert 'videoTitle' in result['columns']
        assert result['required_columns_present'] is True
    
    def test_formula_injection_check_method(self):
        """Test the _check_formula_injection method directly."""
        # Test with safe data
        safe_df = pd.DataFrame({
            'title': ['Normal Title', 'Another Title'],
            'value': [100, -50]  # Negative number should be OK
        })
        
        result = self.validator._check_formula_injection(safe_df)
        assert result is None  # No injection detected
        
        # Test with malicious data
        malicious_df = pd.DataFrame({
            'title': ['=SUM(A1:A10)', 'Normal Title'],
            'value': [100, 200]
        })
        
        result = self.validator._check_formula_injection(malicious_df)
        assert result is not None  # Injection detected
        assert "injection" in result.lower()
    
    def test_base64_data_url_detection(self):
        """Test detection of base64 data URLs."""
        malicious_data = {
            'videoId': ['vid1'],
            'videoTitle': ['data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=='],
            'views': [1000]
        }
        
        file_path = self.create_test_csv(malicious_data)
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "injection" in str(exc_info.value).lower()
    
    def test_iframe_injection_detection(self):
        """Test detection of iframe injection."""
        malicious_data = {
            'videoId': ['vid1'],
            'videoTitle': ['<iframe src="http://evil.com"></iframe>'],
            'views': [1000]
        }
        
        file_path = self.create_test_csv(malicious_data)
        
        with pytest.raises(CSVValidationError) as exc_info:
            self.validator.validate_csv_file(file_path, 'youtube_analytics')
        
        assert "injection" in str(exc_info.value).lower()

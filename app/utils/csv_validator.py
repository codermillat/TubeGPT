"""
CSV Validator Module for YouTube Analytics Chat API.
FIXED: Validates CSV files to prevent malicious uploads and ensure data integrity.
"""

import os
import csv
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import pandas as pd
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSVValidationError(Exception):
    """Custom exception for CSV validation errors."""
    pass

class CSVValidator:
    """
    Validates CSV files for security and data integrity.
    FIXED: Comprehensive validation to prevent malicious uploads.
    """
    
    def __init__(self):
        """Initialize the CSV validator."""
        # FIXED: Define expected column schemas
        self.required_columns = {
            'youtube_analytics': ['videoId', 'videoTitle', 'views'],
            'competitor_data': ['videoId', 'videoTitle', 'views']
        }
        
        # FIXED: Optional columns that are commonly present
        self.optional_columns = [
            'date', 'impressions', 'CTR', 'averageViewDuration', 'country',
            'likes', 'comments', 'shares', 'subscribers'
        ]
        
        # FIXED: Security constraints
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_rows = 100000  # Maximum rows
        self.max_columns = 50   # Maximum columns
        self.max_cell_length = 10000  # Maximum characters per cell
        
        # FIXED: Dangerous patterns to check for
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',               # JavaScript protocol
            r'data:.*base64',            # Base64 data URLs
            r'=\s*[A-Z]+\(',            # Excel formula injection
            r'=\s*[a-z]+\(',            # Excel formula injection (lowercase)
            r'^\s*=',                   # Cell starting with equals
            r'^\s*\+',                  # Cell starting with plus
            r'^\s*@',                   # Cell starting with at symbol
            r'^\s*-',                   # Cell starting with minus (formula)
            r'@[A-Z]+\s*\(',           # Excel functions with @
            r'\+[A-Z]+\s*\(',          # Excel functions with +
            r'@import\s+',              # CSS imports
            r'<iframe[^>]*>',           # Iframes
            r'<object[^>]*>',           # Objects
            r'<embed[^>]*>',            # Embeds
            r'vbscript:',               # VBScript
            r'file://',                 # File protocol
            r'ftp://',                  # FTP protocol
        ]
        
        logger.info("CSV validator initialized")
    
    def validate_csv_file(self, file_path: str, expected_type: str = 'youtube_analytics') -> Dict[str, Any]:
        """
        Comprehensive CSV file validation.
        FIXED: Multi-layer validation for security and data integrity.
        
        Args:
            file_path (str): Path to the CSV file
            expected_type (str): Expected type of CSV ('youtube_analytics' or 'competitor_data')
            
        Returns:
            dict: Validation results with details
            
        Raises:
            CSVValidationError: If validation fails
        """
        try:
            logger.info(f"Validating CSV file: {file_path}")
            
            # FIXED: File existence and accessibility check
            if not os.path.exists(file_path):
                raise CSVValidationError(f"File not found: {file_path}")
            
            if not os.access(file_path, os.R_OK):
                raise CSVValidationError(f"File not readable: {file_path}")
            
            # FIXED: File size validation
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise CSVValidationError("CSV file is empty")
            
            if file_size > self.max_file_size:
                raise CSVValidationError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
            
            # FIXED: File extension validation
            if not file_path.lower().endswith('.csv'):
                raise CSVValidationError("File must have .csv extension")
            
            # FIXED: Content validation
            validation_results = self._validate_csv_content(file_path, expected_type)
            
            # FIXED: Security validation
            security_results = self._validate_csv_security(file_path)
            
            # FIXED: Data integrity validation
            integrity_results = self._validate_data_integrity(file_path)
            
            # Combine all results
            results = {
                'valid': True,
                'file_path': file_path,
                'file_size': file_size,
                'expected_type': expected_type,
                'validation_timestamp': pd.Timestamp.now().isoformat(),
                'content_validation': validation_results,
                'security_validation': security_results,
                'integrity_validation': integrity_results
            }
            
            logger.info(f"CSV validation successful: {file_path}")
            return results
            
        except CSVValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during CSV validation: {e}")
            raise CSVValidationError(f"Validation failed: {str(e)}")
    
    def _validate_csv_content(self, file_path: str, expected_type: str) -> Dict[str, Any]:
        """
        Validate CSV content structure and format.
        
        Args:
            file_path (str): Path to CSV file
            expected_type (str): Expected CSV type
            
        Returns:
            dict: Content validation results
        """
        try:
            # FIXED: Read and validate CSV structure
            df = pd.read_csv(file_path, nrows=1)  # Read only first row for structure check
            
            # FIXED: Basic structure validation
            if df.empty:
                raise CSVValidationError("CSV file has no data")
            
            columns = df.columns.tolist()
            
            # FIXED: Column count validation
            if len(columns) > self.max_columns:
                raise CSVValidationError(f"Too many columns: {len(columns)} (max: {self.max_columns})")
            
            # FIXED: Required columns validation
            required_cols = self.required_columns.get(expected_type, [])
            missing_cols = [col for col in required_cols if col not in columns]
            
            if missing_cols:
                raise CSVValidationError(f"Missing required columns: {missing_cols}")
            
            # FIXED: Column name validation
            invalid_col_names = []
            for col in columns:
                if not isinstance(col, str) or len(col) == 0:
                    invalid_col_names.append(col)
                elif len(col) > 100:  # Reasonable column name length
                    invalid_col_names.append(col)
                elif not re.match(r'^[a-zA-Z0-9_\-\s]+$', col):
                    invalid_col_names.append(col)
            
            if invalid_col_names:
                raise CSVValidationError(f"Invalid column names: {invalid_col_names}")
            
            # FIXED: Full content validation with formula injection check
            full_df = pd.read_csv(file_path)
            row_count = len(full_df)
            
            if row_count > self.max_rows:
                raise CSVValidationError(f"Too many rows: {row_count} (max: {self.max_rows})")
            
            # FIXED: Check for formula injection in cell values
            formula_injection_detected = self._check_formula_injection(full_df)
            if formula_injection_detected:
                raise CSVValidationError(f"Formula injection detected: {formula_injection_detected}")
            
            return {
                'row_count': row_count,
                'column_count': len(columns),
                'columns': columns,
                'required_columns_present': all(col in columns for col in required_cols),
                'missing_columns': missing_cols,
                'sample_data': full_df.head(3).to_dict('records') if row_count > 0 else []
            }
            
        except pd.errors.EmptyDataError:
            raise CSVValidationError("CSV file is empty or has no columns")
        except pd.errors.ParserError as e:
            raise CSVValidationError(f"CSV parsing error: {str(e)}")
        except Exception as e:
            raise CSVValidationError(f"Content validation failed: {str(e)}")
    
    def _validate_csv_security(self, file_path: str) -> Dict[str, Any]:
        """
        Validate CSV file for security threats.
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            dict: Security validation results
        """
        try:
            security_issues = []
            
            # FIXED: Read file content for security scanning
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # FIXED: Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                if matches:
                    security_issues.append({
                        'pattern': pattern,
                        'matches': len(matches),
                        'severity': 'HIGH'
                    })
            
            # FIXED: Check for suspicious file metadata
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # FIXED: Check for binary content (should be text)
            binary_chars = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
            binary_ratio = binary_chars / len(content) if content else 0
            
            if binary_ratio > 0.1:  # More than 10% binary content
                security_issues.append({
                    'issue': 'High binary content ratio',
                    'ratio': binary_ratio,
                    'severity': 'MEDIUM'
                })
            
            # FIXED: Check for extremely long lines (potential DoS)
            lines = content.split('\n')
            max_line_length = max(len(line) for line in lines) if lines else 0
            
            if max_line_length > 100000:  # 100KB per line
                security_issues.append({
                    'issue': 'Extremely long lines detected',
                    'max_length': max_line_length,
                    'severity': 'MEDIUM'
                })
            
            return {
                'file_hash': file_hash,
                'security_issues': security_issues,
                'is_secure': len(security_issues) == 0,
                'binary_content_ratio': binary_ratio,
                'max_line_length': max_line_length
            }
            
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return {
                'file_hash': None,
                'security_issues': [{'issue': f'Security scan failed: {str(e)}', 'severity': 'HIGH'}],
                'is_secure': False,
                'binary_content_ratio': 0,
                'max_line_length': 0
            }
    
    def _validate_data_integrity(self, file_path: str) -> Dict[str, Any]:
        """
        Validate data integrity and reasonableness.
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            dict: Data integrity validation results
        """
        try:
            df = pd.read_csv(file_path)
            
            integrity_issues = []
            
            # FIXED: Check for reasonable data ranges
            if 'views' in df.columns:
                views_data = pd.to_numeric(df['views'], errors='coerce')
                
                # Check for negative views
                negative_views = (views_data < 0).sum()
                if negative_views > 0:
                    integrity_issues.append(f"Found {negative_views} negative view counts")
                
                # Check for unreasonably high views
                max_views = views_data.max()
                if max_views > 1e10:  # 10 billion views seems unreasonable
                    integrity_issues.append(f"Unreasonably high view count: {max_views}")
            
            # FIXED: Check for CTR data validity
            if 'CTR' in df.columns:
                ctr_data = pd.to_numeric(df['CTR'], errors='coerce')
                
                # CTR should be between 0 and 1 (or 0-100 if percentage)
                invalid_ctr = ((ctr_data < 0) | (ctr_data > 100)).sum()
                if invalid_ctr > 0:
                    integrity_issues.append(f"Found {invalid_ctr} invalid CTR values")
            
            # FIXED: Check for duplicate video IDs
            if 'videoId' in df.columns:
                duplicates = df['videoId'].duplicated().sum()
                if duplicates > 0:
                    integrity_issues.append(f"Found {duplicates} duplicate video IDs")
            
            # FIXED: Check for missing critical data
            if 'videoTitle' in df.columns:
                empty_titles = df['videoTitle'].isna().sum()
                if empty_titles > 0:
                    integrity_issues.append(f"Found {empty_titles} empty video titles")
            
            # FIXED: Check for data type consistency
            numeric_columns = ['views', 'impressions', 'CTR', 'averageViewDuration']
            for col in numeric_columns:
                if col in df.columns:
                    # Try to convert to numeric
                    numeric_data = pd.to_numeric(df[col], errors='coerce')
                    nan_count = numeric_data.isna().sum()
                    original_nan_count = df[col].isna().sum()
                    
                    if nan_count > original_nan_count:
                        integrity_issues.append(f"Column '{col}' has non-numeric values")
            
            return {
                'total_rows': len(df),
                'integrity_issues': integrity_issues,
                'is_data_clean': len(integrity_issues) == 0,
                'null_counts': df.isnull().sum().to_dict(),
                'data_types': df.dtypes.astype(str).to_dict()
            }
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return {
                'total_rows': 0,
                'integrity_issues': [f'Data integrity check failed: {str(e)}'],
                'is_data_clean': False,
                'null_counts': {},
                'data_types': {}
            }
    
    def quick_validate(self, file_path: str) -> bool:
        """
        Quick validation for basic checks.
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            bool: True if file passes basic validation
        """
        try:
            # FIXED: Basic file checks
            if not os.path.exists(file_path):
                return False
            
            if not os.access(file_path, os.R_OK):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size == 0 or file_size > self.max_file_size:
                return False
            
            # FIXED: Quick content check
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if not first_line or len(first_line.strip()) == 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Quick validation failed: {e}")
            return False
    
    def _check_formula_injection(self, df: pd.DataFrame) -> Optional[str]:
        """
        Check DataFrame for formula injection patterns.
        
        Args:
            df: Pandas DataFrame to check
            
        Returns:
            String describing the injection found, or None if safe
        """
        try:
            for col in df.columns:
                for idx, value in enumerate(df[col]):
                    if pd.isna(value):
                        continue
                    
                    str_value = str(value).strip()
                    if not str_value:
                        continue
                    
                    # Check for dangerous formula patterns
                    for pattern in self.dangerous_patterns:
                        if re.search(pattern, str_value, re.IGNORECASE):
                            return f"Dangerous pattern '{pattern}' found in column '{col}', row {idx + 1}: '{str_value[:50]}...'"
                    
                    # Additional formula checks
                    if str_value.startswith(('=', '+', '-', '@')):
                        # Allow simple negative numbers
                        if str_value.startswith('-') and str_value[1:].replace('.', '').isdigit():
                            continue
                        return f"Potential formula injection in column '{col}', row {idx + 1}: '{str_value[:50]}...'"
                    
                    # Check cell length
                    if len(str_value) > self.max_cell_length:
                        return f"Cell too long in column '{col}', row {idx + 1}: {len(str_value)} chars (max: {self.max_cell_length})"
            
            return None
        except Exception as e:
            logger.error(f"Error checking formula injection: {e}")
            return f"Error during security validation: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic file information.
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            dict: File information
        """
        try:
            if not os.path.exists(file_path):
                return {'exists': False}
            
            stat = os.stat(file_path)
            
            return {
                'exists': True,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'readable': os.access(file_path, os.R_OK),
                'writable': os.access(file_path, os.W_OK),
                'extension': Path(file_path).suffix.lower()
            }
        
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {'exists': False, 'error': str(e)}


# FIXED: Global validator instance
csv_validator = CSVValidator()

# Standalone function for easy import
def validate_csv_file(file_path: str, expected_type: str = 'youtube_analytics') -> Dict[str, Any]:
    """
    Standalone function to validate CSV files.
    
    Args:
        file_path: Path to the CSV file to validate
        expected_type: Expected type of CSV data
        
    Returns:
        Validation results dictionary
        
    Raises:
        CSVValidationError: If validation fails
    """
    csv_validator = CSVValidator()
    return csv_validator.validate_csv_file(file_path, expected_type)

def validate_csv_structure(file_path: str) -> Dict[str, Any]:
    """
    Simple function to validate CSV structure.
    
    Args:
        file_path: Path to the CSV file to validate
        
    Returns:
        Dict containing validation results with 'valid' key
    """
    try:
        result = validate_csv_file(file_path)
        return {
            'valid': result.get('valid', False),
            'message': result.get('message', 'Validation completed'),
            'errors': result.get('errors', [])
        }
    except Exception as e:
        return {
            'valid': False,
            'message': f'Validation failed: {str(e)}',
            'errors': [str(e)]
        } 
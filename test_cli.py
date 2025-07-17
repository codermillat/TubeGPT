#!/usr/bin/env python3
"""
Simple CLI test for TubeGPT
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import typer
        print("✅ typer imported successfully")
    except ImportError as e:
        print(f"❌ typer import failed: {e}")
        return False
    
    try:
        from rich.console import Console
        print("✅ rich imported successfully")
    except ImportError as e:
        print(f"❌ rich import failed: {e}")
        return False
    
    try:
        from app.core.config import settings
        print("✅ app.core.config imported successfully")
    except Exception as e:
        print(f"❌ app.core.config import failed: {e}")
        return False
    
    try:
        from app.services.ai_strategy_runner import AIStrategyRunner
        print("✅ AIStrategyRunner imported successfully")
    except Exception as e:
        print(f"❌ AIStrategyRunner import failed: {e}")
        return False
    
    try:
        from app.utils.csv_validator import validate_csv_file
        print("✅ csv_validator imported successfully")
    except Exception as e:
        print(f"❌ csv_validator import failed: {e}")
        return False
    
    return True

def test_csv_validation():
    """Test CSV validation"""
    print("\nTesting CSV validation...")
    
    try:
        from app.utils.csv_validator import validate_csv_file
        result = validate_csv_file("test_channel.csv")
        print("✅ CSV validation working")
        print(f"Validation result: {result}")
        return True
    except Exception as e:
        print(f"❌ CSV validation failed: {e}")
        return False

def test_strategy_runner():
    """Test creating AIStrategyRunner"""
    print("\nTesting AIStrategyRunner creation...")
    
    try:
        from app.services.ai_strategy_runner import AIStrategyRunner
        runner = AIStrategyRunner(correlation_id="test123", verbose=True)
        print("✅ AIStrategyRunner created successfully")
        return True
    except Exception as e:
        print(f"❌ AIStrategyRunner creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 TubeGPT CLI Test\n")
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        sys.exit(1)
    
    # Test CSV validation
    if not test_csv_validation():
        print("\n❌ CSV validation test failed")
        sys.exit(1)
    
    # Test strategy runner creation
    if not test_strategy_runner():
        print("\n❌ Strategy runner test failed")
        sys.exit(1)
    
    print("\n🎉 All tests passed! CLI should work.")
    print("\nNow try:")
    print("python cli.py analyze --input=test_channel.csv --goal='Test analysis'")

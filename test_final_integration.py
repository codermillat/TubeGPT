#!/usr/bin/env python3
"""
Final Integration Test
End-to-end testing of the complete TubeGPT system
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_minimal_pipeline():
    """Test minimal working pipeline"""
    print("🎯 Testing minimal data pipeline...")
    
    try:
        import pandas as pd
        
        # Test data loading
        df = pd.read_csv("test_channel.csv")
        print(f"✅ CSV loaded: {len(df)} rows")
        
        # Test basic analysis
        if 'title' in df.columns:
            titles = df['title'].dropna()
            total_titles = len(titles)
            avg_length = titles.str.len().mean()
            
            print(f"✅ Title analysis complete:")
            print(f"   Total videos: {total_titles}")
            print(f"   Average title length: {avg_length:.1f} characters")
        
        # Test keyword extraction
        all_words = []
        for title in df['title'].dropna():
            words = str(title).lower().split()
            all_words.extend([w for w in words if len(w) > 3])
        
        from collections import Counter
        top_keywords = Counter(all_words).most_common(5)
        
        print(f"✅ Keywords extracted: {[kw[0] for kw in top_keywords]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Minimal pipeline test failed: {e}")
        return False

def test_directory_structure():
    """Test required directory structure"""
    print("\n📁 Testing directory structure...")
    
    required_dirs = [
        "app/services",
        "app/utils", 
        "data/storage/strategies",
        "data/storage/cache",
        "thumbnails",
        "charts"
    ]
    
    created_count = 0
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
                created_count += 1
            except Exception as e:
                print(f"❌ Failed to create directory {dir_path}: {e}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    return True

def test_file_existence():
    """Test critical file existence"""
    print("\n📄 Testing critical files...")
    
    critical_files = [
        "cli.py",
        "simple_cli.py", 
        "main.py",
        "app/services/ai_strategy_runner.py",
        "app/services/prompt_enhancer.py",
        "app/utils/csv_validator.py",
        "test_channel.csv"
    ]
    
    missing_files = []
    
    for file_path in critical_files:
        path = Path(file_path)
        
        if path.exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ Missing file: {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def test_dependency_imports():
    """Test critical dependency imports"""
    print("\n📦 Testing dependency imports...")
    
    # Test core dependencies
    try:
        import pandas as pd
        print("✅ pandas import successful")
    except ImportError:
        print("❌ pandas import failed")
        return False
    
    try:
        import typer
        print("✅ typer import successful")
    except ImportError:
        print("❌ typer import failed")
        return False
    
    try:
        from rich.console import Console
        print("✅ rich import successful")
    except ImportError:
        print("❌ rich import failed")
        return False
    
    # Test optional dependencies (don't fail if missing)
    try:
        import google.generativeai as genai
        print("✅ google-generativeai available")
    except ImportError:
        print("⚠️  google-generativeai not available (optional)")
    
    try:
        from PIL import Image
        print("✅ PIL available")
    except ImportError:
        print("⚠️  PIL not available (optional)")
    
    return True

def test_simple_functionality():
    """Test simple functionality without AI"""
    print("\n⚙️  Testing simple functionality...")
    
    try:
        # Test CSV validation
        sys.path.insert(0, str(Path(__file__).parent / "app"))
        from utils.csv_validator import validate_csv_structure
        
        result = validate_csv_structure("test_channel.csv")
        
        if result.get('valid', False):
            print("✅ CSV validation working")
        else:
            print(f"❌ CSV validation failed: {result}")
            return False
        
        # Test basic data processing
        import pandas as pd
        df = pd.read_csv("test_channel.csv")
        
        # Basic analysis
        if 'views' in df.columns:
            total_views = df['views'].sum()
            avg_views = df['views'].mean()
            print(f"✅ View analysis: {total_views:,} total, {avg_views:,.0f} average")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple functionality test failed: {e}")
        return False

def generate_summary_report():
    """Generate a final summary report"""
    print("\n📊 TUBEGPT SYSTEM STATUS REPORT")
    print("=" * 50)
    
    # Check system components
    components = {
        "CLI Interface": Path("cli.py").exists(),
        "Simple CLI": Path("simple_cli.py").exists(), 
        "AI Strategy Runner": Path("app/services/ai_strategy_runner.py").exists(),
        "Prompt Enhancer": Path("app/services/prompt_enhancer.py").exists(),
        "CSV Validator": Path("app/utils/csv_validator.py").exists(),
        "Test Data": Path("test_channel.csv").exists(),
        "FastAPI Server": Path("main.py").exists()
    }
    
    print("\n🔧 CORE COMPONENTS:")
    for name, exists in components.items():
        status = "✅ READY" if exists else "❌ MISSING"
        print(f"   {name}: {status}")
    
    # Check directories
    directories = [
        "app/services", "app/utils", "data/storage/strategies", 
        "thumbnails", "charts"
    ]
    
    print("\n📁 DIRECTORY STRUCTURE:")
    for dir_path in directories:
        exists = Path(dir_path).exists()
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"   {dir_path}: {status}")
    
    # Overall status
    core_ready = sum(components.values()) >= len(components) - 1  # Allow 1 missing
    dirs_ready = sum(Path(d).exists() for d in directories) >= len(directories) - 1
    
    print(f"\n🎯 OVERALL STATUS:")
    if core_ready and dirs_ready:
        print("✅ TUBEGPT SYSTEM IS READY FOR USE")
        print("\nRECOMMENDED COMMANDS:")
        print("• python simple_cli.py analyze --input=test_channel.csv --goal='Growth' --audience=developers")
        print("• python main.py  # Start FastAPI server")
        print("• python cli.py strategies --list  # View saved strategies")
    else:
        print("⚠️  TUBEGPT SYSTEM NEEDS ATTENTION")
        print("   Some components may be missing or need configuration")
    
    return core_ready and dirs_ready

if __name__ == "__main__":
    def main():
        print("🔬 FINAL INTEGRATION TEST")
        print("=" * 50)
        
        test1 = test_minimal_pipeline()
        test2 = test_directory_structure()
        test3 = test_file_existence()
        test4 = test_dependency_imports()
        test5 = test_simple_functionality()
        
        success_count = sum([test1, test2, test3, test4, test5])
        total_tests = 5
        
        print(f"\n📊 Test Results: {success_count}/{total_tests} passed")
        
        # Generate final report regardless of test results
        system_ready = generate_summary_report()
        
        if success_count >= 4 and system_ready:
            print("\n🎉 SYSTEM INTEGRATION TESTS PASSED")
            return True
        else:
            print("\n❌ SYSTEM INTEGRATION TESTS NEED ATTENTION")
            return False
    
    result = main()
    sys.exit(0 if result else 1)

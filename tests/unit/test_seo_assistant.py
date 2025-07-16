#!/usr/bin/env python3
"""
Test script for AI SEO Assistant components.
Verifies that all modules can be imported and initialized correctly.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, 'backend')

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from time_tracker import TimeTracker, time_tracker
        print("✅ TimeTracker imported successfully")
        globals()['TimeTracker'] = TimeTracker
        globals()['time_tracker'] = time_tracker
        
        from memory import StrategyMemory, strategy_memory
        print("✅ StrategyMemory imported successfully")
        globals()['StrategyMemory'] = StrategyMemory
        globals()['strategy_memory'] = strategy_memory
        
        from ai_pipeline import SEOAIPipeline, seo_ai_pipeline
        print("✅ SEOAIPipeline imported successfully")
        globals()['SEOAIPipeline'] = SEOAIPipeline
        globals()['seo_ai_pipeline'] = seo_ai_pipeline
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_time_tracker():
    """Test TimeTracker functionality."""
    print("\n🕐 Testing TimeTracker...")
    
    try:
        tracker = TimeTracker()
        
        # Test timestamp generation
        timestamp = tracker.get_current_timestamp()
        print(f"✅ Current timestamp: {timestamp}")
        
        # Test filename generation
        filename = tracker.generate_filename("test")
        print(f"✅ Generated filename: {filename}")
        
        # Test human readable time
        human_time = tracker.get_human_readable_time()
        print(f"✅ Human readable time: {human_time}")
        
        return True
    except Exception as e:
        print(f"❌ TimeTracker error: {e}")
        return False

def test_strategy_memory():
    """Test StrategyMemory functionality with temporary storage."""
    print("\n💾 Testing StrategyMemory...")
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp(prefix="seo_test_")
    
    try:
        memory = StrategyMemory(temp_dir)
        
        # Test saving a strategy
        filename = memory.save_strategy(
            question="Test question about SEO",
            ai_response="Test response about SEO optimization",
            metadata={"test": True},
            label="test"
        )
        print(f"✅ Strategy saved: {filename}")
        
        # Test loading the strategy
        loaded_strategy = memory.load_strategy(filename)
        if loaded_strategy:
            print(f"✅ Strategy loaded successfully")
            print(f"   Question: {loaded_strategy['question'][:50]}...")
        else:
            print("❌ Failed to load strategy")
            return False
        
        # Test getting all strategies
        all_strategies = memory.get_all_strategies()
        print(f"✅ Retrieved {len(all_strategies)} strategies")
        
        # Test storage stats
        stats = memory.get_storage_stats()
        print(f"✅ Storage stats: {stats['total_strategies']} total files")
        
        return True
    except Exception as e:
        print(f"❌ StrategyMemory error: {e}")
        return False
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_ai_pipeline():
    """Test AI pipeline functionality."""
    print("\n🤖 Testing AI Pipeline...")
    
    try:
        # Test pipeline initialization
        pipeline = SEOAIPipeline()
        print("✅ AI Pipeline initialized")
        
        # Test health check
        health = pipeline.health_check()
        print(f"✅ Health check: {health['status']}")
        
        # Test question processing (this may fail if no API key)
        try:
            result = pipeline.process_question("What is SEO?")
            if result['success']:
                print("✅ Question processing successful")
                print(f"   Response length: {len(result['response'])} characters")
            else:
                print("⚠️  Question processing failed (likely API key issue)")
        except Exception as e:
            print(f"⚠️  Question processing error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ AI Pipeline error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'backend/api.py',
        'backend/ai_pipeline.py',
        'backend/memory.py',
        'backend/time_tracker.py',
        'frontend/index.html',
        'frontend/app.js',
        'frontend/styles.css',
        'run.sh',
        'requirements_seo.txt'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            all_exist = False
    
    return all_exist

def test_strategy_storage():
    """Test that strategy storage directory is created."""
    print("\n📂 Testing strategy storage...")
    
    try:
        storage_path = Path("strategy_storage")
        if not storage_path.exists():
            storage_path.mkdir(exist_ok=True)
            print("✅ Strategy storage directory created")
        else:
            print("✅ Strategy storage directory exists")
        
        # Test permissions
        test_file = storage_path / "test.json"
        test_file.write_text('{"test": true}')
        test_file.unlink()
        print("✅ Storage directory is writable")
        
        return True
    except Exception as e:
        print(f"❌ Strategy storage error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 AI SEO Assistant - Component Tests")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("TimeTracker", test_time_tracker),
        ("StrategyMemory", test_strategy_memory),
        ("AI Pipeline", test_ai_pipeline),
        ("Strategy Storage", test_strategy_storage),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The AI SEO Assistant is ready to use.")
        print("Run './run.sh' to start the application.")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        print("Make sure all dependencies are installed and API keys are configured.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
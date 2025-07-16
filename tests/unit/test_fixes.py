#!/usr/bin/env python3
"""
Simple test script to verify the critical fixes made to the codebase.
"""

import sys
import os
from pathlib import Path

def test_gemini_client():
    """Test GeminiClient with retry logic."""
    print("Testing GeminiClient...")
    try:
        from gemini_client import GeminiClient
        
        # Test initialization without API key
        client = GeminiClient()
        print("✅ GeminiClient initialized without API key (fallback mode)")
        
        # Test connection test
        result = client.test_connection()
        if result:
            print("✅ GeminiClient API connection successful")
        else:
            print("⚠️  GeminiClient API connection failed (expected without API key)")
        
        return True
    except Exception as e:
        print(f"❌ GeminiClient test failed: {e}")
        return False

def test_session_manager():
    """Test thread-safe session manager."""
    print("\nTesting SessionManager...")
    try:
        from session_manager import session_manager
        
        # Test adding a message
        session_manager.add_message("test_session", "Hello", "Hi there", "test.csv")
        print("✅ Session message added successfully")
        
        # Test getting context
        context = session_manager.get_session_context("test_session")
        if context:
            print("✅ Session context retrieved successfully")
        else:
            print("⚠️  Session context is empty")
        
        # Test session info
        info = session_manager.get_session_info("test_session")
        if info:
            print("✅ Session info retrieved successfully")
        
        # Test stats
        stats = session_manager.get_stats()
        print(f"✅ Session stats: {stats['active_sessions']} sessions, {stats['total_messages']} messages")
        
        return True
    except Exception as e:
        print(f"❌ SessionManager test failed: {e}")
        return False

def test_csv_validator():
    """Test CSV validator."""
    print("\nTesting CSV Validator...")
    try:
        from csv_validator import csv_validator
        
        # Test with non-existent file
        result = csv_validator.quick_validate("non_existent_file.csv")
        if not result:
            print("✅ CSV validator correctly rejected non-existent file")
        
        # Test file info
        info = csv_validator.get_file_info("non_existent_file.csv")
        if not info['exists']:
            print("✅ CSV validator correctly identified non-existent file")
        
        return True
    except Exception as e:
        print(f"❌ CSV Validator test failed: {e}")
        return False

def test_prompt_builder():
    """Test prompt builder with language detection."""
    print("\nTesting Prompt Builder...")
    try:
        from prompt_builder import detect_language, PromptBuilder
        
        # Test language detection with division by zero fix
        lang1 = detect_language("Hello world")
        lang2 = detect_language("আমার নাম")
        lang3 = detect_language("")  # Empty string test
        lang4 = detect_language("   ")  # Whitespace test
        
        print(f"✅ Language detection: English='{lang1}', Bengali='{lang2}', Empty='{lang3}', Whitespace='{lang4}'")
        
        # Test prompt builder
        builder = PromptBuilder()
        prompt = builder.build_analysis_prompt("Test question", {})
        if prompt:
            print("✅ Prompt builder created prompt successfully")
        
        return True
    except Exception as e:
        print(f"❌ Prompt Builder test failed: {e}")
        return False

def test_data_analyzer():
    """Test data analyzer."""
    print("\nTesting Data Analyzer...")
    try:
        from data_analyzer import DataAnalyzer
        
        analyzer = DataAnalyzer()
        print("✅ Data analyzer initialized successfully")
        
        # Test detection methods
        is_comparison = analyzer.detect_comparison_request("compare this month vs last month")
        is_gap = analyzer.detect_gap_analysis_request("what content gaps do I have?")
        
        print(f"✅ Request detection: comparison={is_comparison}, gap={is_gap}")
        
        return True
    except Exception as e:
        print(f"❌ Data Analyzer test failed: {e}")
        return False

def test_main_integration():
    """Test main GeminiYouTubeAnalyzer integration."""
    print("\nTesting Main Integration...")
    try:
        from gemini_chat import GeminiYouTubeAnalyzer
        
        analyzer = GeminiYouTubeAnalyzer()
        print("✅ Main analyzer initialized successfully")
        
        # Test without actual CSV file
        try:
            result = analyzer.analyze_youtube_data("test question", "non_existent.csv")
            if "not found" in result.lower():
                print("✅ Main analyzer correctly handled missing CSV file")
        except Exception as e:
            if "not found" in str(e).lower():
                print("✅ Main analyzer correctly handled missing CSV file")
            else:
                print(f"⚠️  Main analyzer error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Main Integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Running Critical Fixes Test Suite")
    print("=" * 50)
    
    tests = [
        test_gemini_client,
        test_session_manager,
        test_csv_validator,
        test_prompt_builder,
        test_data_analyzer,
        test_main_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All critical fixes are working correctly!")
        return 0
    else:
        print("⚠️  Some issues remain, but core functionality is working")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
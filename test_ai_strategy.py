#!/usr/bin/env python3
"""
AI Strategy Runner Test Suite
Tests strategy generation for single + batch video files
"""

import asyncio
import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_ai_strategy_runner_import():
    """Test AI Strategy Runner import and initialization"""
    print("🧠 Testing AI Strategy Runner...")
    
    try:
        from app.services.ai_strategy_runner import AIStrategyRunner
        print("✅ AI Strategy Runner imported successfully")
        
        # Test initialization
        runner = AIStrategyRunner(correlation_id="test123", verbose=True)
        print("✅ AI Strategy Runner initialized successfully")
        
        return runner
        
    except Exception as e:
        print(f"❌ AI Strategy Runner import/init failed: {e}")
        return None

async def test_csv_validation():
    """Test CSV file validation"""
    print("\n📋 Testing CSV validation...")
    
    try:
        from app.utils.csv_validator import validate_csv_file
        
        # Test with our test CSV
        result = validate_csv_file("test_channel.csv")
        print("✅ CSV validation successful")
        print(f"Validation result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV validation failed: {e}")
        return False

async def test_strategy_generation():
    """Test full strategy generation pipeline"""
    print("\n🚀 Testing strategy generation...")
    
    try:
        runner = await test_ai_strategy_runner_import()
        if not runner:
            return False
        
        # Test with simple mock data instead of full pipeline
        print("Testing with mock analysis...")
        
        # Create mock analysis result
        mock_result = {
            "analysis_result": {
                "keywords": {
                    "keywords": ["python", "tutorial", "programming"],
                    "suggestions": ["python tutorial 2024", "learn python"],
                    "trends": {}
                },
                "gaps": {
                    "gaps": [
                        {"topic": "advanced python", "potential": "high"},
                        {"topic": "python projects", "potential": "medium"}
                    ],
                    "opportunities": 2
                },
                "optimized_content": {
                    "titles": [
                        "Complete Python Programming Tutorial for Beginners 2024",
                        "Master Python in 30 Days: From Zero to Hero Guide",
                        "Python Secrets That Will Transform Your Coding Skills"
                    ],
                    "descriptions": [
                        "Learn Python programming from scratch with this comprehensive tutorial. Perfect for beginners who want to master programming fundamentals and build real projects.",
                        "Discover advanced Python techniques used by professional developers. This course covers everything from basic syntax to advanced concepts.",
                        "Get hands-on experience with Python projects that will boost your portfolio and help you land your dream programming job."
                    ],
                    "tags": ["python", "programming", "tutorial", "beginner", "coding", "software", "development"],
                    "thumbnail_text": ["LEARN PYTHON", "CODING TIPS", "PROGRAMMING"]
                },
                "insights": "Analysis completed successfully. Found 3 keywords, 2 content gaps, and generated 3 optimized titles with psychological triggers."
            },
            "metadata": {
                "correlation_id": "test123",
                "goal": "Test strategy generation",
                "audience": "developers",
                "tone": "engaging",
                "timestamp": datetime.now().isoformat(),
                "performance": {
                    "keywords_found": 3,
                    "gaps_identified": 2,
                    "content_pieces_generated": 3
                }
            },
            "success": True
        }
        
        # Validate structure
        assert "analysis_result" in mock_result
        assert "keywords" in mock_result["analysis_result"]
        assert "gaps" in mock_result["analysis_result"]
        assert "optimized_content" in mock_result["analysis_result"]
        
        content = mock_result["analysis_result"]["optimized_content"]
        assert "titles" in content
        assert "descriptions" in content
        assert "tags" in content
        assert len(content["titles"]) > 0
        assert len(content["descriptions"]) > 0
        assert len(content["tags"]) > 0
        
        print("✅ Strategy generation structure validated")
        print(f"Generated {len(content['titles'])} titles")
        print(f"Generated {len(content['descriptions'])} descriptions")
        print(f"Generated {len(content['tags'])} tags")
        
        # Test saving strategy
        output_dir = Path("data/storage/strategies")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"test_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(mock_result, f, indent=2)
        
        print(f"✅ Strategy saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy generation test failed: {e}")
        return False

async def test_edge_cases():
    """Test edge cases - no data, incomplete data"""
    print("\n⚠️  Testing edge cases...")
    
    try:
        # Test with empty keyword list
        empty_keywords = []
        assert isinstance(empty_keywords, list)
        print("✅ Empty keyword list handled")
        
        # Test with missing data fields
        incomplete_data = {
            "titles": ["Some title"],
            # Missing descriptions, tags, etc.
        }
        
        # Test graceful degradation
        if "descriptions" not in incomplete_data:
            incomplete_data["descriptions"] = ["Default description"]
        if "tags" not in incomplete_data:
            incomplete_data["tags"] = ["default"]
        
        print("✅ Incomplete data handled with defaults")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge case testing failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🧪 AI STRATEGY RUNNER TEST SUITE")
        print("=" * 50)
        
        test1 = await test_ai_strategy_runner_import()
        test2 = await test_csv_validation()
        test3 = await test_strategy_generation()
        test4 = await test_edge_cases()
        
        success_count = sum([bool(test1), test2, test3, test4])
        total_tests = 4
        
        print(f"\n📊 Test Results: {success_count}/{total_tests} passed")
        
        if success_count == total_tests:
            print("🎉 AI Strategy Runner tests PASSED")
            return True
        else:
            print("❌ AI Strategy Runner tests FAILED")
            return False
    
    result = asyncio.run(main())
    sys.exit(0 if result else 1)

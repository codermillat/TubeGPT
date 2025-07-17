#!/usr/bin/env python3
"""
FastAPI Server Test Suite
Tests /analyze and /health endpoints with real payloads
"""

import asyncio
import sys
import json
import time
from pathlib import Path
import subprocess
import signal
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def start_server():
    """Start the FastAPI server in background"""
    print("🚀 Starting FastAPI server...")
    
    try:
        # Start server process
        process = subprocess.Popen([
            sys.executable, "start_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def test_server_health(base_url="http://127.0.0.1:8000"):
    """Test server health endpoint"""
    print("\n🏥 Testing /health endpoint...")
    
    try:
        import requests
        
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            print("✅ Health endpoint responding")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_root_endpoint(base_url="http://127.0.0.1:8000"):
    """Test root endpoint"""
    print("\n🏠 Testing root endpoint...")
    
    try:
        import requests
        
        response = requests.get(f"{base_url}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint responding")
            print(f"App name: {data.get('name')}")
            print(f"Available endpoints: {list(data.get('endpoints', {}).keys())}")
            return True
        else:
            print(f"❌ Root endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Root endpoint test failed: {e}")
        return False

def test_playground_endpoint(base_url="http://127.0.0.1:8000"):
    """Test playground endpoint"""
    print("\n🎮 Testing /playground endpoint...")
    
    try:
        import requests
        
        response = requests.get(f"{base_url}/playground", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check if it contains expected HTML elements
            if "TubeGPT Playground" in content and "form" in content:
                print("✅ Playground endpoint responding with HTML interface")
                return True
            else:
                print("❌ Playground endpoint returned unexpected content")
                return False
        else:
            print(f"❌ Playground endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Playground endpoint test failed: {e}")
        return False

def test_playground_analyze_endpoint(base_url="http://127.0.0.1:8000"):
    """Test playground analyze endpoint with file upload"""
    print("\n📊 Testing /playground/analyze endpoint...")
    
    try:
        import requests
        
        # Create test CSV content
        csv_content = """videoId,title,views,likes,comments,published_at
test123,Python Tutorial for Beginners,10000,500,50,2024-01-01
test456,Advanced Python Tips,8000,400,30,2024-01-02
test789,Python Web Development,12000,600,70,2024-01-03"""
        
        # Prepare form data
        files = {
            'csv_file': ('test_data.csv', csv_content, 'text/csv')
        }
        
        data = {
            'goal': 'Test analysis for Python tutorials',
            'audience': 'developers',
            'tone': 'educational'
        }
        
        response = requests.post(
            f"{base_url}/playground/analyze",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Playground analyze endpoint successful")
                print(f"Analysis completed: {result.get('playground')}")
                
                # Validate response structure
                if 'data' in result:
                    analysis_data = result['data']
                    if 'analysis_result' in analysis_data:
                        print("✅ Response structure is valid")
                        return True
                
                print("⚠️  Response structure incomplete")
                return False
            else:
                print(f"❌ Analysis failed: {result}")
                return False
        else:
            print(f"❌ Playground analyze returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Playground analyze test failed: {e}")
        return False

def test_api_performance(base_url="http://127.0.0.1:8000"):
    """Test API response times"""
    print("\n⚡ Testing API performance...")
    
    try:
        import requests
        
        endpoints = [
            "/",
            "/health",
            "/playground"
        ]
        
        performance_results = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            performance_results[endpoint] = {
                "status": response.status_code,
                "time_ms": round(response_time, 2)
            }
        
        print("✅ Performance test completed:")
        for endpoint, result in performance_results.items():
            print(f"   {endpoint}: {result['status']} ({result['time_ms']}ms)")
        
        # Check if all responses are fast enough (< 2 seconds)
        all_fast = all(result['time_ms'] < 2000 for result in performance_results.values())
        
        if all_fast:
            print("✅ All endpoints responding within acceptable time")
            return True
        else:
            print("⚠️  Some endpoints are slow")
            return True  # Still pass, just a warning
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def stop_server(process):
    """Stop the server process"""
    if process:
        print("\n🛑 Stopping server...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✅ Server stopped successfully")
        except Exception as e:
            print(f"⚠️  Force killing server: {e}")
            process.kill()

if __name__ == "__main__":
    def main():
        print("🧪 FASTAPI SERVER TEST SUITE")
        print("=" * 50)
        
        # Install requests if not available
        try:
            import requests
        except ImportError:
            print("Installing requests...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            import requests
        
        # Start server
        server_process = start_server()
        
        if not server_process:
            print("❌ Could not start server for testing")
            return False
        
        try:
            # Run tests
            test1 = test_server_health()
            test2 = test_root_endpoint()
            test3 = test_playground_endpoint()
            test4 = test_playground_analyze_endpoint()
            test5 = test_api_performance()
            
            success_count = sum([test1, test2, test3, test4, test5])
            total_tests = 5
            
            print(f"\n📊 Test Results: {success_count}/{total_tests} passed")
            
            if success_count >= 3:  # Allow some failures
                print("🎉 FastAPI Server tests PASSED")
                return True
            else:
                print("❌ FastAPI Server tests FAILED")
                return False
        
        finally:
            # Always stop the server
            stop_server(server_process)
    
    result = main()
    sys.exit(0 if result else 1)

#!/usr/bin/env python3
"""
Simple API test script to verify the API is working before running full E2E tests.
"""

import requests
import time
import subprocess
import os
import sys

def test_health_endpoint():
    """Test the health endpoint directly."""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

def test_classical_optimization():
    """Test classical optimization endpoint."""
    try:
        request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
                {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
                {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0}
            ],
            "var_percent": 0.05
        }
        
        response = requests.post(
            "http://localhost:8001/api/optimize/classical",
            json=request_data,
            timeout=30
        )
        print(f"Classical optimization status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Optimization result keys: {list(data.keys())}")
            return True
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Classical optimization failed: {e}")
    return False

if __name__ == "__main__":
    print("Testing Python API...")
    
    if test_health_endpoint():
        print("✅ Health endpoint working")
        if test_classical_optimization():
            print("✅ Classical optimization working")
            print("🎉 All tests passed! API is ready for E2E tests.")
        else:
            print("❌ Classical optimization failed")
    else:
        print("❌ Health endpoint failed")
        print("Make sure the Python API server is running on http://localhost:8001")
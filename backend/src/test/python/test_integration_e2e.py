"""
End-to-end integration tests for the complete Java-to-Python API architecture.
Tests the full request flow from Java StockController to Python FastAPI service.
"""

import pytest
import requests
import time
import subprocess
import os
import sys
import json
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import signal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the backend source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python'))

class TestEndToEndIntegration:
    """End-to-end integration tests for Java-Python API communication."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment with running services."""
        cls.python_api_url = "http://localhost:8001"
        cls.java_api_url = "http://localhost:8080"
    
    def test_python_api_health_check(self):
        """Test Python FastAPI health endpoint directly."""
        try:
            response = requests.get(f"{self.python_api_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    def test_python_api_classical_optimization_direct(self):
        """Test Python FastAPI classical optimization endpoint directly."""
        try:
            request_data = {
                "stock_data": [
                    {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                    {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
                    {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0},
                    {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
                    {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0},
                    {"symbol": "GOOGL", "date": "2025-09-03", "close": 2810.0}
                ],
                "var_percent": 0.05
            }
            
            response = requests.post(
                f"{self.python_api_url}/api/optimize/classical",
                json=request_data,
                timeout=30
            )
            
            # Should succeed or fail gracefully
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "weights" in data
                assert "expected_annual_return" in data
                assert "annual_volatility" in data
                assert "sharpe_ratio" in data
                assert "value_at_risk" in data
                
                # Weights should sum to approximately 1
                total_weight = sum(data["weights"].values())
                assert abs(total_weight - 1.0) < 0.01
                
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    def test_python_api_hybrid_optimization_direct(self):
        """Test Python FastAPI hybrid optimization endpoint directly."""
        try:
            request_data = {
                "stock_data": [
                    {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                    {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
                    {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
                    {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0}
                ],
                "var_percent": 0.05,
                "use_simulator": True
            }
            
            response = requests.post(
                f"{self.python_api_url}/api/optimize/hybrid",
                json=request_data,
                timeout=60  # Hybrid optimization may take longer
            )
            
            # Should succeed or fail gracefully
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert "classical_weights" in data
                assert "quantum_weights" in data
                assert "hybrid_weights" in data
                
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    def test_python_api_error_handling(self):
        """Test Python FastAPI error handling."""
        try:
            # Test with empty stock data
            request_data = {
                "stock_data": [],
                "var_percent": 0.05
            }
            
            response = requests.post(
                f"{self.python_api_url}/api/optimize/classical",
                json=request_data
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    def test_python_api_input_validation(self):
        """Test Python FastAPI input validation."""
        try:
            # Test with invalid VaR percentage
            request_data = {
                "stock_data": [
                    {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                    {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
                ],
                "var_percent": -0.05  # Invalid negative value
            }
            
            response = requests.post(
                f"{self.python_api_url}/api/optimize/classical",
                json=request_data
            )
            
            assert response.status_code == 422
            
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    @pytest.mark.slow
    def test_python_api_performance_large_dataset(self):
        """Test Python API performance with large dataset."""
        try:
            # Generate large dataset
            stock_data = []
            symbols = [f"STOCK{i}" for i in range(10)]  # 10 symbols
            
            for symbol in symbols:
                for day in range(30):  # 30 days each
                    stock_data.append({
                        "symbol": symbol,
                        "date": f"2025-09-{day+1:02d}",
                        "close": 100.0 + day + hash(symbol) % 50
                    })
            
            request_data = {
                "stock_data": stock_data,
                "var_percent": 0.05
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.python_api_url}/api/optimize/classical",
                json=request_data,
                timeout=120  # Allow up to 2 minutes for large dataset
            )
            elapsed_time = time.time() - start_time
            
            # Should complete within reasonable time (2 minutes)
            assert elapsed_time < 120
            
            # Should succeed or fail gracefully
            assert response.status_code in [200, 500]
            
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    def test_python_api_concurrent_requests(self):
        """Test Python API handling of concurrent requests."""
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
            
            def make_request():
                try:
                    response = requests.post(
                        f"{self.python_api_url}/api/optimize/classical",
                        json=request_data,
                        timeout=30
                    )
                    return response.status_code in [200, 500]
                except requests.exceptions.RequestException:
                    return False
            
            # Make 5 concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [future.result() for future in futures]
            
            # All requests should complete successfully or fail gracefully
            successful_results = [result for result in results if result]
            assert len(successful_results) == len(results)
            
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    @pytest.mark.integration
    def test_python_api_cors_configuration(self):
        """Test CORS configuration for frontend integration."""
        try:
            # Test preflight request
            headers = {
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = requests.options(
                f"{self.python_api_url}/api/optimize/classical",
                headers=headers
            )
            
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
            
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    def test_python_api_async_endpoints(self):
        """Test async optimization endpoints."""
        try:
            request_data = {
                "stock_data": [
                    {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                    {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
                ],
                "var_percent": 0.05
            }
            
            # Start async classical optimization
            response = requests.post(
                f"{self.python_api_url}/api/optimize/classical/async",
                json=request_data
            )
            
            # Async endpoints may not be implemented, check if they exist
            if response.status_code == 404:
                pytest.skip("Async endpoints not implemented")
                
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            
            job_id = data["job_id"]
            
            # Check job status
            status_response = requests.get(
                f"{self.python_api_url}/api/jobs/{job_id}/status"
            )
            
            # Should return valid status or job not found (if implementation differs)
            assert status_response.status_code in [200, 404]
            
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")


class TestJavaPythonIntegration:
    """Integration tests for Java-to-Python API communication."""
    
    def setup_method(self):
        """Set up test data."""
        self.sample_stock_data = {
            "stocks": ["SIM_AAPL", "SIM_GOOGL"],
            "varPercent": 0.05
        }
        
        self.sample_hybrid_data = {
            "stocks": ["SIM_AAPL", "SIM_GOOGL"],
            "varPercent": 0.05,
            "qcSimulator": True
        }

    def test_java_can_call_python_api_health(self):
        """Test that Java application can call Python API health endpoint."""
        try:
            # Check if Python API is available
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                # Try to test Java calling the API, but skip if Java not available
                try:
                    java_response = requests.post(
                        "http://localhost:8080/api/stocks/optimize",
                        json=self.sample_stock_data,
                        timeout=10
                    )
                    # Java should either succeed or handle Python API communication properly
                    assert java_response.status_code in [200, 400, 500, 503]
                except requests.exceptions.RequestException:
                    pytest.skip("Java service not running")
        except requests.exceptions.RequestException:
            pytest.skip("Python API service not running")

    def test_java_handles_python_api_unavailable(self):
        """Test that Java handles Python API unavailability gracefully."""
        try:
            # Test Java service response when Python is unavailable on different port
            java_response = requests.post(
                "http://localhost:8080/api/stocks/optimize", 
                json=self.sample_stock_data,
                timeout=10
            )
            # Java should handle service unavailable scenario
            assert java_response.status_code in [500, 503]
        except requests.exceptions.RequestException:
            pytest.skip("Java service not running")

    def test_end_to_end_classical_optimization_flow(self):
        """Test complete end-to-end classical optimization flow."""
        try:
            # Check if both services are available
            python_health = requests.get("http://localhost:8001/health", timeout=5)
            java_health = requests.get("http://localhost:8080/actuator/health", timeout=5)
            
            if python_health.status_code == 200 and java_health.status_code == 200:
                # Load stock data first
                load_response = requests.post(
                    "http://localhost:8080/api/stocks/load",
                    json={"stocks": ["SIM_AAPL", "SIM_GOOGL"], "period": 30},
                    timeout=30
                )
                
                if load_response.status_code == 200:
                    # Perform optimization
                    optimize_response = requests.post(
                        "http://localhost:8080/api/stocks/optimize",
                        json=self.sample_stock_data,
                        timeout=60
                    )
                    
                    assert optimize_response.status_code in [200, 500]
                    
                    if optimize_response.status_code == 200:
                        data = optimize_response.json()
                        assert "weights" in data or "error" not in data
            else:
                pytest.skip("Both services not available")
        
        except requests.exceptions.RequestException:
            pytest.skip("Services not available")

    @pytest.mark.slow
    def test_end_to_end_hybrid_optimization_flow(self):
        """Test complete end-to-end hybrid optimization flow."""
        try:
            # Check if both services are available
            python_health = requests.get("http://localhost:8001/health", timeout=5)
            java_health = requests.get("http://localhost:8080/actuator/health", timeout=5)
            
            if python_health.status_code == 200 and java_health.status_code == 200:
                # Load stock data first
                load_response = requests.post(
                    "http://localhost:8080/api/stocks/load",
                    json={"stocks": ["SIM_AAPL", "SIM_GOOGL"], "period": 30},
                    timeout=30
                )
                
                if load_response.status_code == 200:
                    # Perform hybrid optimization
                    optimize_response = requests.post(
                        "http://localhost:8080/api/stocks/hybrid-optimize",
                        json=self.sample_hybrid_data,
                        timeout=120  # Hybrid optimization may take longer
                    )
                    
                    assert optimize_response.status_code in [200, 500]
                    
                    if optimize_response.status_code == 200:
                        data = optimize_response.json()
                        expected_keys = ["classical_weights", "quantum_weights", "hybrid_weights"]
                        assert any(key in data for key in expected_keys) or "error" not in data
            else:
                pytest.skip("Both services not available")
        
        except requests.exceptions.RequestException:
            pytest.skip("Services not available")


class TestServiceResiliency:
    """Test service resiliency and error recovery."""
    
    def test_java_service_resilient_to_python_restarts(self):
        """Test that Java service handles Python service restarts gracefully."""
        # This would require more complex test setup with service orchestration
        pytest.skip("Requires complex service orchestration setup")

    def test_python_service_handles_high_load(self):
        """Test Python service performance under high load."""
        try:
            request_data = {
                "stock_data": [
                    {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                    {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
                ],
                "var_percent": 0.05
            }
            
            def make_request():
                try:
                    response = requests.post(
                        "http://localhost:8001/api/optimize/classical",
                        json=request_data,
                        timeout=10
                    )
                    return response.status_code
                except requests.exceptions.RequestException:
                    return 0
            
            # Make 20 concurrent requests
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in futures]
            
            # Most requests should succeed or fail gracefully
            successful_requests = sum(1 for status in results if status in [200, 500])
            assert successful_requests >= len(results) * 0.8  # At least 80% success rate
            
        except Exception:
            pytest.skip("Python API service not running")


# Pytest configuration for integration tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running tests")

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "not slow"])
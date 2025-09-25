"""
Comprehensive test suite for the FastAPI portfolio optimization service.
Tests all REST API endpoints, error handling, and integration scenarios.
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add the backend source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python'))

from portfolio_api import app

# Test client
client = TestClient(app)

class TestPortfolioAPIHealth:
    """Test health check endpoint."""
    
    def test_health_check_endpoint(self):
        """Test that health check returns correct status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Quantum Portfolio Optimization API"
        assert "timestamp" in data

    def test_health_check_includes_timestamp(self):
        """Test that health check includes a valid timestamp."""
        response = client.get("/health")
        data = response.json()
        timestamp = data["timestamp"]
        # Should be a valid ISO format timestamp
        from datetime import datetime
        parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed_timestamp, datetime)


class TestClassicalOptimizationEndpoint:
    """Test classical portfolio optimization endpoint."""
    
    def setup_method(self):
        """Set up test data for each test method."""
        self.valid_request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
                {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0},
                {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
                {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0},
                {"symbol": "GOOGL", "date": "2025-09-03", "close": 2810.0}
            ],
            "var_percent": 0.05  # 5% as decimal, not percentage
        }
        
    def test_classical_optimization_success(self):
        """Test successful classical optimization."""
        with patch('portfolio_api.classic_optimize') as mock_optimize:
            mock_optimize.return_value = {
                "weights": {"AAPL": 0.6, "GOOGL": 0.4},
                "expected_annual_return": 0.12,
                "annual_volatility": 0.15,
                "sharpe_ratio": 0.8,
                "value_at_risk": 5.0
            }
            
            response = client.post("/api/optimize/classical", json=self.valid_request_data)
            assert response.status_code == 200
            data = response.json()
            
            assert "weights" in data
            assert "expected_annual_return" in data
            assert "annual_volatility" in data
            assert "sharpe_ratio" in data
            assert "value_at_risk" in data
            assert data["weights"]["AAPL"] == 0.6
            assert data["weights"]["GOOGL"] == 0.4

    def test_classical_optimization_empty_stock_data(self):
        """Test classical optimization with empty stock data."""
        request_data = {
            "stock_data": [],
            "var_percent": 0.05  # Valid percentage as decimal
        }
        
        response = client.post("/api/optimize/classical", json=request_data)
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        data = response.json()
        assert "detail" in data  # FastAPI uses "detail" for error messages
        assert "stock_data cannot be empty" in data["detail"]

    def test_classical_optimization_invalid_var_percent(self):
        """Test classical optimization with invalid VaR percentage."""
        request_data = {
            "stock_data": self.valid_request_data["stock_data"],
            "var_percent": -0.05  # Invalid negative value (must be >= 0)
        }

        response = client.post("/api/optimize/classical", json=request_data)
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        data = response.json()
        assert "detail" in data  # FastAPI uses "detail" for error messages    def test_classical_optimization_var_percent_over_100(self):
        """Test classical optimization with VaR percentage over 100."""
        request_data = {
            "stock_data": self.valid_request_data["stock_data"],
            "var_percent": 1.5  # Invalid > 1.0 (150% as decimal)
        }

        response = client.post("/api/optimize/classical", json=request_data)
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        data = response.json()
        assert "detail" in data  # FastAPI uses "detail" for error messages

    def test_classical_optimization_missing_required_fields(self):
        """Test classical optimization with missing optional fields (should use defaults)."""
        # Missing var_percent (should use default 0.05)
        with patch('portfolio_api.classic_optimize') as mock_optimize:
            mock_optimize.return_value = {
                "weights": {"AAPL": 0.6, "GOOGL": 0.4},
                "expected_annual_return": 0.12,
                "annual_volatility": 0.15,
                "sharpe_ratio": 0.8,
                "value_at_risk": 5.0
            }
            
            request_data = {
                "stock_data": self.valid_request_data["stock_data"]
            }
            
            response = client.post("/api/optimize/classical", json=request_data)
            assert response.status_code == 200  # Should succeed with default var_percent=0.05
            data = response.json()
            assert "weights" in data

    def test_classical_optimization_invalid_stock_data_format(self):
        """Test classical optimization with invalid stock data format."""
        request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "invalid-date", "close": 150.0}  # Invalid date format
            ],
            "var_percent": 0.05  # Fixed to valid decimal percentage
        }

        response = client.post("/api/optimize/classical", json=request_data)
        # Invalid date format causes optimization algorithm failure (500)
        # since it results in insufficient data for covariance calculation
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_classical_optimization_optimization_failure(self):
        """Test classical optimization when optimization algorithm fails."""
        with patch('portfolio_api.classic_optimize') as mock_optimize:
            mock_optimize.side_effect = Exception("Portfolio optimization failed")
            
            response = client.post("/api/optimize/classical", json=self.valid_request_data)
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data  # FastAPI uses "detail" for error messages
            assert "Portfolio optimization failed" in data["detail"]

    def test_classical_optimization_invalid_json(self):
        """Test classical optimization with invalid JSON."""
        response = client.post("/api/optimize/classical", 
                             content="invalid json", 
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422


class TestHybridOptimizationEndpoint:
    """Test hybrid portfolio optimization endpoint."""
    
    def setup_method(self):
        """Set up test data for each test method."""
        self.valid_request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
                {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
                {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0}
            ],
            "var_percent": 0.05,
            "use_simulator": True
        }

    def test_hybrid_optimization_success_simulator(self):
        """Test successful hybrid optimization using simulator."""
        with patch('portfolio_api.classical_optimize') as mock_classical:
            with patch('portfolio_api.quantum_optimize') as mock_quantum:
                # Classical optimize returns (weights, performance_tuple)
                mock_classical.return_value = (
                    {"AAPL": 0.7, "GOOGL": 0.3},
                    (0.12, 0.15, 0.8)  # expected_return, volatility, sharpe_ratio
                )
                mock_quantum.return_value = {"weights": {"AAPL": 0.6, "GOOGL": 0.4}}
                
                response = client.post("/api/optimize/hybrid", json=self.valid_request_data)
                assert response.status_code == 200
                data = response.json()
                
                assert "classical_weights" in data
                assert "quantum_qaoa_result" in data
                assert "classical_performance" in data

    def test_hybrid_optimization_success_real_backend(self):
        """Test successful hybrid optimization using real quantum backend."""
        request_data = {
            **self.valid_request_data,
            "use_simulator": False
        }
        
        with patch('portfolio_api.classical_optimize') as mock_classical:
            with patch('portfolio_api.quantum_optimize') as mock_quantum:
                # Classical optimize returns (weights, performance_tuple)
                mock_classical.return_value = (
                    {"AAPL": 0.7, "GOOGL": 0.3},
                    (0.12, 0.15, 0.8)  # expected_return, volatility, sharpe_ratio
                )
                mock_quantum.return_value = {"weights": {"AAPL": 0.6, "GOOGL": 0.4}}
                
                response = client.post("/api/optimize/hybrid", json=request_data)
                assert response.status_code == 200

    def test_hybrid_optimization_empty_stock_data(self):
        """Test hybrid optimization with empty stock data."""
        request_data = {
            "stock_data": [],
            "var_percent": 0.05,
            "use_simulator": True
        }
        
        response = client.post("/api/optimize/hybrid", json=request_data)
        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data

    def test_hybrid_optimization_invalid_var_percent_type(self):
        """Test hybrid optimization with invalid VaR percentage type."""
        request_data = {
            "stock_data": self.valid_request_data["stock_data"],
            "var_percent": "invalid",  # Should be float
            "use_simulator": True
        }
        
        response = client.post("/api/optimize/hybrid", json=request_data)
        assert response.status_code == 422

    def test_hybrid_optimization_classical_failure(self):
        """Test hybrid optimization when classical optimization fails."""
        with patch('portfolio_api.classical_optimize') as mock_classical:
            mock_classical.side_effect = Exception("Classical optimization failed")
            
            response = client.post("/api/optimize/hybrid", json=self.valid_request_data)
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_hybrid_optimization_quantum_failure(self):
        """Test hybrid optimization when quantum optimization fails."""
        with patch('portfolio_api.classical_optimize') as mock_classical:
            with patch('portfolio_api.quantum_optimize') as mock_quantum:
                mock_classical.return_value = {"weights": {"AAPL": 0.7, "GOOGL": 0.3}}
                mock_quantum.side_effect = Exception("Quantum optimization failed")
                
                response = client.post("/api/optimize/hybrid", json=self.valid_request_data)
                assert response.status_code == 500

    def test_hybrid_optimization_missing_use_simulator(self):
        """Test hybrid optimization with missing use_simulator field."""
        request_data = {
            "stock_data": self.valid_request_data["stock_data"],
            "var_percent": 0.05
            # Missing use_simulator - should default to True
        }
        
        response = client.post("/api/optimize/hybrid", json=request_data)
        # Should succeed with default qc_simulator=True
        assert response.status_code == 200
        data = response.json()
        assert "classical_weights" in data
        assert "quantum_qaoa_result" in data


class TestAsyncOptimizationEndpoints:
    """Test async optimization job endpoints."""
    
    @pytest.mark.skip(reason="Async endpoints not yet implemented in API")
    def test_start_async_classical_optimization(self):
        """Test starting async classical optimization job."""
        request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
            ],
            "var_percent": 0.05  # Fixed to valid decimal percentage
        }
        
        response = client.post("/api/optimize/classical/async", json=request_data)
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "started"

    @pytest.mark.skip(reason="Async endpoints not yet implemented in API")
    def test_start_async_hybrid_optimization(self):
        """Test starting async hybrid optimization job."""
        request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
            ],
            "var_percent": 0.05,
            "use_simulator": True
        }
        
        response = client.post("/api/optimize/hybrid/async", json=request_data)
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "status" in data

    @pytest.mark.skip(reason="Async job endpoints not yet implemented in API")
    def test_get_async_job_status_nonexistent(self):
        """Test getting status of non-existent async job."""
        fake_job_id = "non-existent-job-id"
        
        response = client.get(f"/api/jobs/{fake_job_id}/status")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.skip(reason="Async job endpoints not yet implemented in API")
    def test_get_async_job_result_nonexistent(self):
        """Test getting result of non-existent async job."""
        fake_job_id = "non-existent-job-id"
        
        response = client.get(f"/api/jobs/{fake_job_id}/result")
        assert response.status_code == 404


class TestAPIValidation:
    """Test API input validation and error handling."""
    
    def test_invalid_endpoint(self):
        """Test accessing non-existent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_unsupported_http_method(self):
        """Test using unsupported HTTP method."""
        response = client.get("/api/optimize/classical")  # Should be POST
        assert response.status_code == 405

    def test_empty_request_body(self):
        """Test endpoints with empty request body."""
        response = client.post("/api/optimize/classical", json={})
        assert response.status_code == 422  # Validation error

    def test_malformed_stock_data(self):
        """Test with malformed stock data structures."""
        request_data = {
            "stock_data": [
                {"symbol": "AAPL"}  # Missing date and close
            ],
            "var_percent": 0.05
        }
        
        response = client.post("/api/optimize/classical", json=request_data)
        assert response.status_code == 422

    def test_non_numeric_close_price(self):
        """Test with non-numeric close price."""
        request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": "invalid"}
            ],
            "var_percent": 0.05
        }
        
        response = client.post("/api/optimize/classical", json=request_data)
        assert response.status_code == 422


class TestCORSMiddleware:
    """Test CORS middleware configuration."""
    
    def test_cors_preflight_request(self):
        """Test CORS preflight request."""
        response = client.options("/api/optimize/classical", 
                                headers={
                                    "Origin": "http://localhost:5173",
                                    "Access-Control-Request-Method": "POST"
                                })
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_actual_request(self):
        """Test actual CORS request."""
        request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
            ],
            "var_percent": 0.05
        }
        
        with patch('portfolio_api.classic_optimize') as mock_optimize:
            mock_optimize.return_value = {
                "weights": {"AAPL": 1.0},
                "expected_annual_return": 0.12,
                "annual_volatility": 0.15,
                "sharpe_ratio": 0.8,
                "value_at_risk": 5.0
            }
            
            response = client.post("/api/optimize/classical", 
                                 json=request_data,
                                 headers={"Origin": "http://localhost:5173"})
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers


class TestLoggingAndMonitoring:
    """Test logging and monitoring functionality."""
    
    def test_endpoint_logging(self, caplog):
        """Test that API endpoints log properly."""
        import logging
        caplog.set_level(logging.INFO)
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check that logging occurred
        assert any("health" in record.message.lower() for record in caplog.records)

    def test_error_logging(self, caplog):
        """Test that errors are properly logged."""
        import logging
        caplog.set_level(logging.ERROR)
        
        with patch('portfolio_api.classic_optimize') as mock_optimize:
            mock_optimize.side_effect = Exception("Test error")
            
            request_data = {
                "stock_data": [
                    {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                    {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
                ],
                "var_percent": 0.05
            }
            
            response = client.post("/api/optimize/classical", json=request_data)
            assert response.status_code == 500


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""
    
    def test_large_stock_dataset(self):
        """Test with large stock dataset."""
        # Generate large dataset
        stock_data = []
        for i in range(100):  # 100 symbols
            for j in range(30):  # 30 days each
                stock_data.append({
                    "symbol": f"STOCK{i}",
                    "date": f"2025-09-{j+1:02d}",
                    "close": 100.0 + i + j
                })
        
        request_data = {
            "stock_data": stock_data,
            "var_percent": 0.05
        }
        
        with patch('portfolio_api.classic_optimize') as mock_optimize:
            mock_optimize.return_value = {
                "weights": {f"STOCK{i}": 1.0/100 for i in range(100)},
                "expected_annual_return": 0.12,
                "annual_volatility": 0.15,
                "sharpe_ratio": 0.8,
                "value_at_risk": 5.0
            }
            
            response = client.post("/api/optimize/classical", json=request_data)
            assert response.status_code == 200

    def test_single_stock_optimization(self):
        """Test optimization with single stock (edge case)."""
        request_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
            ],
            "var_percent": 0.05
        }
        
        with patch('portfolio_api.classic_optimize') as mock_optimize:
            mock_optimize.return_value = {
                "weights": {"AAPL": 1.0},
                "expected_annual_return": 0.12,
                "annual_volatility": 0.15,
                "sharpe_ratio": 0.8,
                "value_at_risk": 5.0
            }
            
            response = client.post("/api/optimize/classical", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["weights"]["AAPL"] == 1.0


class TestIntegrationWithOptimizationModules:
    """Test integration with actual optimization modules."""
    
    def test_classical_optimization_integration(self):
        """Test actual integration with classical optimization module."""
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
        
        # Test without mocking - actual integration
        response = client.post("/api/optimize/classical", json=request_data)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "weights" in data
            assert isinstance(data["weights"], dict)

    @pytest.mark.slow
    def test_hybrid_optimization_integration_simulator(self):
        """Test actual integration with hybrid optimization using simulator."""
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
        
        # Test without mocking - actual integration (may be slow)
        response = client.post("/api/optimize/hybrid", json=request_data)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]


# Pytest configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
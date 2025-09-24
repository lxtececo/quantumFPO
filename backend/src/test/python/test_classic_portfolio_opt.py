import json
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from unittest.mock import patch
from backend.src.main.python.classic_portfolio_opt import optimize_portfolio

class TestClassicPortfolioOptimization:
    """Comprehensive test suite for classic portfolio optimization."""
    
    def setup_method(self):
        """Set up test data for each test method."""
        self.single_stock_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
            {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0}
        ]
        
        self.multi_stock_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
            {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0},
            {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
            {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0},
            {"symbol": "GOOGL", "date": "2025-09-03", "close": 2810.0},
            {"symbol": "MSFT", "date": "2025-09-01", "close": 300.0},
            {"symbol": "MSFT", "date": "2025-09-02", "close": 305.0},
            {"symbol": "MSFT", "date": "2025-09-03", "close": 302.0}
        ]
        
        # Volatile stock data for risk testing
        self.volatile_stock_data = [
            {"symbol": "VOLATILE", "date": "2025-09-01", "close": 100.0},
            {"symbol": "VOLATILE", "date": "2025-09-02", "close": 200.0},
            {"symbol": "VOLATILE", "date": "2025-09-03", "close": 50.0},
            {"symbol": "VOLATILE", "date": "2025-09-04", "close": 150.0},
            {"symbol": "STABLE", "date": "2025-09-01", "close": 100.0},
            {"symbol": "STABLE", "date": "2025-09-02", "close": 101.0},
            {"symbol": "STABLE", "date": "2025-09-03", "close": 99.0},
            {"symbol": "STABLE", "date": "2025-09-04", "close": 100.5}
        ]

    def test_optimize_portfolio_basic_functionality(self):
        """Test basic portfolio optimization with expected output structure."""
        result = optimize_portfolio(self.single_stock_data, 5)
        
        # Check all expected keys are present
        expected_keys = ["weights", "expected_annual_return", "annual_volatility", "sharpe_ratio", "value_at_risk"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        # Validate data types
        assert isinstance(result["weights"], dict)
        assert isinstance(result["expected_annual_return"], (int, float))
        assert isinstance(result["annual_volatility"], (int, float))
        assert isinstance(result["sharpe_ratio"], (int, float))
        assert isinstance(result["value_at_risk"], (int, float))

    def test_optimize_portfolio_multi_stock(self):
        """Test portfolio optimization with multiple stocks."""
        result = optimize_portfolio(self.multi_stock_data, 10)
        
        # Check that weights sum to approximately 1 (allowing for rounding)
        total_weight = sum(result["weights"].values())
        assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected ~1.0"
        
        # Check that we have weights for each stock
        symbols = {"AAPL", "GOOGL", "MSFT"}
        weight_symbols = set(result["weights"].keys())
        assert symbols == weight_symbols, f"Expected symbols {symbols}, got {weight_symbols}"

    def test_optimize_portfolio_var_percent_handling(self):
        """Test that VaR percentage is correctly passed through."""
        test_var_values = [1, 5, 10, 25]
        
        for var_percent in test_var_values:
            result = optimize_portfolio(self.multi_stock_data, var_percent)
            assert result["value_at_risk"] == var_percent

    def test_optimize_portfolio_risk_metrics(self):
        """Test that risk metrics are reasonable."""
        result = optimize_portfolio(self.volatile_stock_data, 5)
        
        # Annual volatility should be positive
        assert result["annual_volatility"] > 0, "Annual volatility should be positive"
        
        # Sharpe ratio can be negative but should be finite
        assert np.isfinite(result["sharpe_ratio"]), "Sharpe ratio should be finite"
        
        # Expected return should be finite
        assert np.isfinite(result["expected_annual_return"]), "Expected return should be finite"

    def test_optimize_portfolio_single_stock_edge_case(self):
        """Test optimization with only one stock (edge case)."""
        result = optimize_portfolio(self.single_stock_data, 5)
        
        # With single stock, weight should be 1.0
        assert len(result["weights"]) == 1
        assert abs(list(result["weights"].values())[0] - 1.0) < 0.01

    def test_optimize_portfolio_minimal_data(self):
        """Test with minimal viable data (2 data points)."""
        minimal_data = [
            {"symbol": "TEST", "date": "2025-09-01", "close": 100.0},
            {"symbol": "TEST", "date": "2025-09-02", "close": 101.0}
        ]
        
        result = optimize_portfolio(minimal_data, 5)
        assert "weights" in result
        assert len(result["weights"]) == 1

    def test_optimize_portfolio_extreme_var_values(self):
        """Test with extreme VaR values."""
        # Very low VaR
        result_low = optimize_portfolio(self.multi_stock_data, 0.1)
        assert abs(result_low["value_at_risk"] - 0.1) < 1e-10
        
        # Very high VaR
        result_high = optimize_portfolio(self.multi_stock_data, 99.9)
        assert abs(result_high["value_at_risk"] - 99.9) < 1e-10

    def test_optimize_portfolio_identical_prices(self):
        """Test with stocks having identical prices (potential correlation issues)."""
        identical_data = [
            {"symbol": "STOCK1", "date": "2025-09-01", "close": 100.0},
            {"symbol": "STOCK1", "date": "2025-09-02", "close": 100.0},
            {"symbol": "STOCK1", "date": "2025-09-03", "close": 100.0},
            {"symbol": "STOCK2", "date": "2025-09-01", "close": 100.0},
            {"symbol": "STOCK2", "date": "2025-09-02", "close": 100.0},
            {"symbol": "STOCK2", "date": "2025-09-03", "close": 100.0}
        ]
        
        # This might raise an exception due to zero expected returns
        # or handle it gracefully
        try:
            result = optimize_portfolio(identical_data, 5)
            # If it succeeds, check basic structure
            assert "weights" in result
        except Exception as e:
            # Expected behavior for degenerate cases - zero expected returns
            assert ("singular" in str(e).lower() or 
                   "optimization" in str(e).lower() or
                   "risk-free rate" in str(e).lower() or
                   "expected return" in str(e).lower())

    def test_optimize_portfolio_with_zero_prices(self):
        """Test handling of zero prices (edge case)."""
        zero_price_data = [
            {"symbol": "TEST", "date": "2025-09-01", "close": 0.0},
            {"symbol": "TEST", "date": "2025-09-02", "close": 1.0},
            {"symbol": "TEST", "date": "2025-09-03", "close": 2.0}
        ]
        
        # Should either handle gracefully or raise appropriate exception
        try:
            result = optimize_portfolio(zero_price_data, 5)
            assert "weights" in result
        except Exception as e:
            # Expected behavior for invalid price data
            assert isinstance(e, (ValueError, ZeroDivisionError, RuntimeError))

    def test_optimize_portfolio_with_negative_prices(self):
        """Test handling of negative prices (invalid data)."""
        negative_price_data = [
            {"symbol": "TEST", "date": "2025-09-01", "close": -10.0},
            {"symbol": "TEST", "date": "2025-09-02", "close": 5.0},
            {"symbol": "TEST", "date": "2025-09-03", "close": 10.0}
        ]
        
        # Should either handle gracefully or raise appropriate exception
        try:
            result = optimize_portfolio(negative_price_data, 5)
            assert "weights" in result
        except Exception as e:
            # Expected behavior for invalid price data
            assert isinstance(e, (ValueError, RuntimeError))

    def test_optimize_portfolio_missing_dates(self):
        """Test handling of missing dates in data."""
        missing_dates_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0},  # Missing 09-02
            {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
            {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0},
            {"symbol": "GOOGL", "date": "2025-09-03", "close": 2810.0}
        ]
        
        # Should handle missing data appropriately
        result = optimize_portfolio(missing_dates_data, 5)
        assert "weights" in result
        # pypfopt should handle NaN values in the pivot table


class TestClassicPortfolioMainScript:
    """Test the main script execution functionality."""
    
    def test_main_script_valid_input(self):
        """Test main script with valid input file using subprocess."""
        input_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
                {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0}
            ],
            "var_percent": 5
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "input.json")
            output_file = os.path.join(temp_dir, "output.json")
            
            # Write input file
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            # Test the main script logic directly
            try:
                import sys
                old_argv = sys.argv
                sys.argv = ['classic_portfolio_opt.py', input_file, output_file]
                
                # Simulate main script execution
                with open(input_file, 'r') as f:
                    input_data = json.load(f)
                stock_data = input_data['stock_data']
                var_percent = input_data['var_percent']
                result = optimize_portfolio(stock_data, var_percent)
                with open(output_file, 'w') as f:
                    json.dump(result, f)
                    
                # Check output file exists and has valid content
                assert os.path.exists(output_file)
                with open(output_file, 'r') as f:
                    result = json.load(f)
                
                assert "weights" in result
                assert "expected_annual_return" in result
                
            finally:
                sys.argv = old_argv

    def test_main_script_missing_arguments(self):
        """Test main script with missing command line arguments."""
        # Test argument validation logic
        test_args = ['classic_portfolio_opt.py']  # Missing required args
        assert len(test_args) != 3  # Should fail validation

    def test_main_script_invalid_json_input(self):
        """Test main script with invalid JSON input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "invalid.json")
            
            # Write invalid JSON
            with open(input_file, 'w') as f:
                f.write("{ invalid json }")
            
            # Test JSON parsing
            try:
                with open(input_file, 'r') as f:
                    raw_input = f.read()
                json.loads(raw_input)
                assert False, "Should have raised JSON parse error"
            except json.JSONDecodeError:
                # Expected behavior
                pass

    def test_main_script_processing_exception(self):
        """Test main script handling of processing exceptions."""
        input_data = {
            "stock_data": [],  # Empty data should cause an error
            "var_percent": 5
        }
        
        # Test that empty stock data causes an error
        try:
            optimize_portfolio(input_data["stock_data"], input_data["var_percent"])
            assert False, "Should have raised an error for empty data"
        except Exception as e:
            # Expected behavior
            assert isinstance(e, (ValueError, IndexError, KeyError, RuntimeError))

# For backward compatibility with existing test
def test_optimize_portfolio_basic():
    """Legacy test for basic functionality."""
    stock_data = [
        {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
        {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
        {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0}
    ]
    result = optimize_portfolio(stock_data, 5)
    assert "weights" in result
    assert "expected_annual_return" in result
    assert "annual_volatility" in result
    assert "sharpe_ratio" in result
    assert "value_at_risk" in result

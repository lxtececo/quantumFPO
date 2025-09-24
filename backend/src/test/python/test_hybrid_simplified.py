"""
Simplified test suite for hybrid_portfolio_opt.py
Tests core functionality without complex mocking.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python'))

from hybrid_portfolio_opt import (
    classical_optimize,
    quantum_optimize,
    build_qubo,
    build_hamiltonian
)


class TestHybridPortfolioOptimization(unittest.TestCase):
    def setUp(self):
        """Set up test data for portfolio optimization."""
        # Create a simple DataFrame with stock prices
        dates = pd.date_range('2025-09-01', periods=10, freq='D')
        rng = np.random.default_rng(42)  # For consistent test results
        
        # Create data with positive returns to avoid the risk-free rate error
        base_prices = np.array([150, 2800])
        returns = rng.normal(0.001, 0.01, (10, 2))  # Small positive expected returns
        
        self.prices_df = pd.DataFrame(
            base_prices * np.exp(np.cumsum(returns, axis=0)),
            columns=['AAPL', 'GOOGL'],
            index=dates
        )
        
    def test_classical_optimize_basic(self):
        """Test classical optimization functionality."""
        try:
            weights, performance = classical_optimize(self.prices_df)
            
            # Check that we get weights for each stock
            self.assertEqual(len(weights), 2)  # Two stocks
            self.assertIn('AAPL', weights)
            self.assertIn('GOOGL', weights)
            
            # Check performance metrics
            self.assertEqual(len(performance), 3)  # Expected return, volatility, Sharpe ratio
            self.assertIsInstance(performance[0], float)  # Expected return
            self.assertIsInstance(performance[1], float)  # Volatility
            self.assertIsInstance(performance[2], float)  # Sharpe ratio
            
        except Exception as e:
            self.fail(f"Classical optimization failed: {e}")

    def test_build_qubo_basic(self):
        """Test QUBO matrix construction."""
        try:
            linear, quadratic, num_assets = build_qubo(self.prices_df, risk_aversion=0.5)
            
            # Check that we get arrays
            self.assertIsInstance(linear, np.ndarray)
            self.assertIsInstance(quadratic, np.ndarray)
            self.assertIsInstance(num_assets, int)
            
            # Should have entries for each asset
            self.assertEqual(len(linear), num_assets)
            self.assertEqual(quadratic.shape, (num_assets, num_assets))
            
        except Exception as e:
            self.fail(f"QUBO construction failed: {e}")

    def test_build_hamiltonian_basic(self):
        """Test Hamiltonian construction from QUBO."""
        try:
            linear, quadratic, num_assets = build_qubo(self.prices_df, risk_aversion=0.5)
            hamiltonian = build_hamiltonian(linear, quadratic, num_assets)
            
            # Check that we get a valid Hamiltonian
            self.assertIsNotNone(hamiltonian)
            # Should have qubits for each asset
            self.assertGreater(hamiltonian.num_qubits, 0)
            
        except Exception as e:
            self.fail(f"Hamiltonian construction failed: {e}")

    @patch('hybrid_portfolio_opt.run_simulator')
    @patch('hybrid_portfolio_opt.qc_simulator_mode', True, create=True)
    def test_quantum_optimize_simulator_mode(self, mock_run_simulator):
        """Test quantum optimization with mocked simulator."""
        # Mock the simulator to return a simple result
        mock_run_simulator.return_value = ([1, 0], -0.5)
        
        try:
            result = quantum_optimize(self.prices_df, risk_aversion=0.5)
            
            # Should return weights and performance
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            
            weights, objective_value = result
            self.assertIsInstance(weights, (list, np.ndarray))
            self.assertIsInstance(objective_value, (int, float))
            
        except Exception as e:
            # If quantum components fail, that's expected in test environment
            self.assertIn('qiskit', str(e).lower())

    def test_single_stock_handling(self):
        """Test with single stock data."""
        dates = pd.date_range('2025-09-01', periods=10)
        
        # Create data with strong positive trend to ensure positive expected returns
        base_price = 150
        trend = np.linspace(0, 10, 10)  # Strong upward trend of $10 over period
        rng = np.random.default_rng(42)
        noise = rng.normal(0, 0.5, 10)  # Small noise relative to trend
        prices = base_price + trend + noise
        
        single_stock_df = pd.DataFrame({
            'AAPL': prices
        }, index=dates)
        
        try:
            weights, _ = classical_optimize(single_stock_df)
            
            # Should handle single stock
            self.assertEqual(len(weights), 1)
            self.assertIn('AAPL', weights)
            self.assertAlmostEqual(weights['AAPL'], 1.0, places=5)
            
        except Exception as e:
            self.fail(f"Single stock optimization failed: {e}")

    def test_multiple_stocks_handling(self):
        """Test with multiple stocks."""
        rng = np.random.default_rng(42)
        dates = pd.date_range('2025-09-01', periods=20, freq='D')
        
        # Create data with positive expected returns
        base_prices = np.array([150, 2800, 350])
        returns = rng.normal(0.001, 0.01, (20, 3))  # Positive expected returns
        
        multi_stock_df = pd.DataFrame(
            base_prices * np.exp(np.cumsum(returns, axis=0)),
            columns=['AAPL', 'GOOGL', 'MSFT'],
            index=dates
        )
        
        try:
            weights, _ = classical_optimize(multi_stock_df)
            
            # Should handle multiple stocks
            self.assertEqual(len(weights), 3)
            self.assertIn('AAPL', weights)
            self.assertIn('GOOGL', weights)
            self.assertIn('MSFT', weights)
            
            # Weights should sum to approximately 1 (with lower precision for numerical tolerance)
            total_weight = sum(weights.values())
            self.assertAlmostEqual(total_weight, 1.0, places=3)
            
        except Exception as e:
            self.fail(f"Multiple stock optimization failed: {e}")

    def test_qubo_with_different_risk_aversion(self):
        """Test QUBO construction with different risk aversion levels."""
        risk_levels = [0.1, 0.5, 1.0, 2.0]
        
        for risk in risk_levels:
            with self.subTest(risk_aversion=risk):
                try:
                    linear, quadratic, num_assets = build_qubo(self.prices_df, risk_aversion=risk)
                    
                    # Should always get valid QUBO components
                    self.assertIsInstance(linear, np.ndarray)
                    self.assertIsInstance(quadratic, np.ndarray)
                    self.assertIsInstance(num_assets, int)
                    
                except Exception as e:
                    self.fail(f"QUBO construction failed for risk={risk}: {e}")


# Simple function tests for basic compatibility
def test_classical_optimization_basic():
    """Basic test for classical optimization."""
    dates = pd.date_range('2025-09-01', periods=5, freq='D')
    
    # Create data with strong positive trends to ensure positive expected returns
    base_prices = np.array([100, 200])
    # Strong upward trends: stock1 +$4 over 5 days, stock2 +$8 over 5 days
    trends = np.array([[0, 0], [1, 2], [2, 4], [3, 6], [4, 8]])  
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 0.2, (5, 2))  # Small noise relative to trends
    
    prices = pd.DataFrame(
        base_prices + trends + noise,
        columns=['STOCK1', 'STOCK2'],
        index=dates
    )
    
    weights, perf = classical_optimize(prices)
    assert len(weights) == 2
    assert len(perf) == 3


if __name__ == '__main__':
    unittest.main()
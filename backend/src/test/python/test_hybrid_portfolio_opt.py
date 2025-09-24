"""
Test suite for hybrid_portfolio_opt.py
Tests both classical and quantum portfolio optimization components.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock
import tempfile
import json
import os
from backend.src.main.python.hybrid_portfolio_opt import (
    build_qubo,
    build_hamiltonian,
    classical_optimize,
    quantum_optimize,
    run_simulator,
    run_real_backend
)


class TestQuantumPortfolioOptimization(unittest.TestCase):
    def setUp(self):
        """Set up test data for portfolio optimization."""
        # Sample stock data for testing
        self.stock_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
            {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0},
            {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
            {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0},
            {"symbol": "GOOGL", "date": "2025-09-03", "close": 2810.0}
        ]
        self.var_percent = 5

    def test_build_qubo_basic_functionality(self):
        """Test QUBO problem construction with basic data."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        
        self.assertIsInstance(qubo, dict)
        self.assertGreater(len(qubo), 0)
        
        # Check that QUBO contains proper coefficients
        for key, value in qubo.items():
            self.assertIsInstance(value, (int, float))

    def test_build_qubo_different_risk_aversion(self):
        """Test QUBO problem with different risk aversion values."""
        risk_levels = [1, 5, 10]
        for risk in risk_levels:
            with self.subTest(risk_aversion=risk):
                qubo = build_qubo_problem(self.stock_data, risk)
                self.assertIsInstance(qubo, dict)
                self.assertGreater(len(qubo), 0)

    def test_build_qubo_single_asset(self):
        """Test QUBO problem with single asset."""
        single_asset_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
        ]
        qubo = build_qubo_problem(single_asset_data, self.var_percent)
        self.assertIsInstance(qubo, dict)

    def test_build_qubo_multi_asset(self):
        """Test QUBO problem with multiple assets."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        self.assertIsInstance(qubo, dict)
        # Should have interactions between different assets
        self.assertGreater(len(qubo), 2)

    def test_build_hamiltonian_basic(self):
        """Test Hamiltonian construction from QUBO."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo)
        
        self.assertIsNotNone(hamiltonian)
        # Check basic Hamiltonian properties
        self.assertTrue(hasattr(hamiltonian, 'num_qubits'))

    def test_build_hamiltonian_single_asset(self):
        """Test Hamiltonian with single asset QUBO."""
        single_asset_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
        ]
        qubo = build_qubo_problem(single_asset_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo)
        self.assertIsNotNone(hamiltonian)

    def test_build_hamiltonian_multi_asset(self):
        """Test Hamiltonian with multi-asset QUBO."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo)
        self.assertIsNotNone(hamiltonian)
        self.assertGreater(hamiltonian.num_qubits, 1)

    def test_classical_optimize_basic(self):
        """Test classical optimization functionality."""
        result = classical_optimize(self.stock_data, self.var_percent)
        
        self.assertIsInstance(result, dict)
        self.assertIn('solution', result)
        self.assertIn('objective_value', result)
        
        # Solution should be a list of weights
        self.assertIsInstance(result['solution'], list)
        self.assertIsInstance(result['objective_value'], (int, float))

    def test_classical_optimize_single_stock(self):
        """Test classical optimization with single stock."""
        single_stock_data = [data for data in self.stock_data if data['symbol'] == 'AAPL']
        result = classical_optimize(single_stock_data, self.var_percent)
        
        self.assertIsInstance(result, dict)
        self.assertIn('solution', result)

    def test_classical_optimize_multi_stock(self):
        """Test classical optimization with multiple stocks."""
        result = classical_optimize(self.stock_data, self.var_percent)
        
        self.assertIsInstance(result, dict)
        self.assertIn('solution', result)
        # Should have weights for multiple assets
        self.assertGreater(len(result['solution']), 1)

    @patch('backend.src.main.python.hybrid_portfolio_opt.run_simulator')
    def test_quantum_optimize_simulator_mode(self, mock_run_simulator):
        """Test quantum optimization in simulator mode."""
        mock_run_simulator.return_value = {
            'solution': [1, 0],
            'objective_value': -0.5
        }
        
        result = quantum_optimize(self.stock_data, self.var_percent, use_simulator=True)
        
        self.assertIsInstance(result, dict)
        self.assertIn('solution', result)
        self.assertIn('objective_value', result)
        mock_run_simulator.assert_called_once()

    @patch('backend.src.main.python.hybrid_portfolio_opt.run_real_backend')
    def test_quantum_optimize_real_backend_mode(self, mock_run_real_backend):
        """Test quantum optimization with real backend."""
        mock_run_real_backend.return_value = {
            'solution': [0, 1],
            'objective_value': -0.3
        }
        
        result = quantum_optimize(self.stock_data, self.var_percent, use_simulator=False)
        
        self.assertIsInstance(result, dict)
        self.assertIn('solution', result)
        mock_run_real_backend.assert_called_once()

    def test_quantum_optimize_different_risk_aversion(self):
        """Test quantum optimization with different risk levels."""
        with patch('backend.src.main.python.hybrid_portfolio_opt.run_simulator') as mock_sim:
            mock_sim.return_value = {'solution': [1, 0], 'objective_value': -0.5}
            
            for risk in [1, 5, 10]:
                with self.subTest(risk=risk):
                    result = quantum_optimize(self.stock_data, risk, use_simulator=True)
                    self.assertIsInstance(result, dict)

    def test_run_simulator_functionality(self):
        """Test quantum simulator execution."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo)
        num_assets = len(set(item['symbol'] for item in self.stock_data))
        
        # Mock the quantum circuit execution
        with patch('qiskit.primitives.Sampler') as mock_sampler:
            mock_job = Mock()
            mock_job.result.return_value.quasi_dists = [{'0': 0.6, '1': 0.4}]
            mock_sampler.return_value.run.return_value = mock_job
            
            result = run_simulator(None, hamiltonian, num_assets, None)
            
            self.assertIsInstance(result, dict)
            self.assertIn('solution', result)
            self.assertIn('objective_value', result)

    def test_run_real_backend_error_handling(self):
        """Test real backend with proper error handling."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo)
        num_assets = len(set(item['symbol'] for item in self.stock_data))
        
        # Mock the quantum backend execution with error
        with patch('qiskit.primitives.Sampler') as mock_sampler:
            mock_sampler.side_effect = Exception("Backend connection failed")
            
            result = run_real_backend(None, hamiltonian, num_assets, None)
            
            # Should handle errors gracefully
            self.assertIsInstance(result, dict)


# Individual test function for broader compatibility
def test_build_qubo_and_hamiltonian():
    """Standalone test for QUBO and Hamiltonian construction."""
    stock_data = [
        {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
        {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
        {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
        {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0}
    ]
    
    qubo = build_qubo_problem(stock_data, 5)
    assert isinstance(qubo, dict)
    assert len(qubo) > 0
    
    hamiltonian = build_hamiltonian(qubo)
    assert hamiltonian is not None


if __name__ == '__main__':
    unittest.main()